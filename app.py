#!/usr/bin/env python3
"""
EnigmaTV — Portal IPTV Streaming

- Landing page de marketing con planes de suscripción.
- Sistema de login/registro con SQLite.
- Reproductor web de listas .m3u / .m3u8.
- Proxy interno que resuelve CORS y permite forzar User-Agent / Referer,
  reescribiendo las playlists HLS para que los segmentos pasen por el proxy.
"""

import io
import os
import re
import sqlite3
import time
from functools import wraps
from urllib.parse import quote, unquote, urljoin, urlparse

import requests
from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    stream_with_context,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "enigmatv-secret-key-change-in-prod-2026")

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            plan TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


init_db()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    if "user_id" not in session:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return user

DEFAULT_UA = (
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
)
TIMEOUT = 20
SESSION = requests.Session()

# ---------------------------------------------------------------------------
# Parser M3U
# ---------------------------------------------------------------------------
ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')


def _base_name(hint):
    """Nombre base a partir del filename/URL de origen."""
    if not hint:
        return "Stream"
    last = hint.rstrip("/").split("/")[-1]
    last = last.split("?")[0]
    for ext in (".m3u8", ".m3u", ".txt"):
        if last.lower().endswith(ext):
            last = last[: -len(ext)]
    return last or "Stream"


def _parse_master(text, name_hint=""):
    """Fallback: master playlist HLS (#EXT-X-STREAM-INF) -> un canal por variante."""
    channels = []
    base = _base_name(name_hint)
    lines = text.splitlines()
    pending = None  # resolucion de la ultima #EXT-X-STREAM-INF
    idx = 0
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.upper().startswith("#EXT-X-STREAM-INF"):
            res = re.search(r"RESOLUTION=([0-9x]+)", line, re.I)
            pending = res.group(1) if res else ""
        elif not line.startswith("#"):
            idx += 1
            host = urlparse(line).netloc or "directo"
            channels.append(
                {
                    "name": f"{base} - {idx:02d}",
                    "logo": "",
                    "group": base,
                    "tvg_id": "",
                    "ua": "",
                    "referer": "",
                    "url": line,
                    "id": len(channels),
                }
            )
            pending = None
    return channels, ([base] if channels else [])


def parse_m3u(text, name_hint=""):
    """Devuelve (lista_de_canales, lista_de_grupos)."""
    up = text.upper()
    # Master playlist HLS de un solo stream (variantes #EXT-X-STREAM-INF,
    # sin entradas de canal #EXTINF): lo tratamos como mirrors de un canal.
    if "#EXT-X-STREAM-INF" in up and "#EXTINF" not in up:
        return _parse_master(text, name_hint)

    channels = []
    groups = set()
    cur = None
    lines = text.splitlines()

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        if line.upper().startswith("#EXTINF"):
            # #EXTINF:-1 tvg-id="" tvg-logo="" group-title="Cine",Nombre canal
            attrs = dict(ATTR_RE.findall(line))
            name = line.split(",", 1)[1].strip() if "," in line else ""
            cur = {
                "name": name or attrs.get("tvg-name", "") or "Sin nombre",
                "logo": attrs.get("tvg-logo", ""),
                "group": attrs.get("group-title", "") or "Sin grupo",
                "tvg_id": attrs.get("tvg-id", ""),
                "ua": "",
                "referer": "",
            }
        elif line.upper().startswith("#EXTGRP"):
            if cur is not None and ":" in line:
                cur["group"] = line.split(":", 1)[1].strip() or cur["group"]
        elif line.upper().startswith("#EXTVLCOPT"):
            # opciones tipo http-user-agent / http-referrer
            if cur is not None and ":" in line:
                opt = line.split(":", 1)[1].strip()
                if "=" in opt:
                    k, v = opt.split("=", 1)
                    k = k.lower().strip()
                    if k in ("http-user-agent", "user-agent"):
                        cur["ua"] = v.strip()
                    elif k in ("http-referrer", "http-referer", "referer"):
                        cur["referer"] = v.strip()
        elif line.startswith("#"):
            continue  # otros tags de cabecera
        else:
            # línea de URL del stream
            if cur is None:
                cur = {
                    "name": line.split("/")[-1] or "Stream",
                    "logo": "",
                    "group": "Sin grupo",
                    "tvg_id": "",
                    "ua": "",
                    "referer": "",
                }
            cur["url"] = line
            cur["id"] = len(channels)
            groups.add(cur["group"])
            channels.append(cur)
            cur = None

    # Sin canales #EXTINF: puede ser un master playlist de un solo stream.
    if not channels:
        return _parse_master(text, name_hint)

    return channels, sorted(groups)


# ---------------------------------------------------------------------------
# Rutas — Páginas principales
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    user = get_current_user()
    return render_template("home.html", user=user)


@app.route("/login", methods=["GET"])
def login_page():
    if "user_id" in session:
        return redirect(url_for("player"))
    error = request.args.get("error", "")
    success = request.args.get("success", "")
    return render_template("login.html", error=error, success=success)


@app.route("/register", methods=["GET"])
def register_page():
    if "user_id" in session:
        return redirect(url_for("player"))
    error = request.args.get("error", "")
    return render_template("register.html", error=error)


@app.route("/api/auth/register", methods=["POST"])
def api_register():
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm") or ""
    plan = request.form.get("plan") or "free"

    if not name or not email or not password:
        return redirect(url_for("register_page", error="Todos los campos son obligatorios."))
    if len(password) < 4:
        return redirect(url_for("register_page", error="La contraseña debe tener al menos 4 caracteres."))
    if password != confirm:
        return redirect(url_for("register_page", error="Las contraseñas no coinciden."))
    if plan not in ("free", "inicio", "premium"):
        plan = "free"

    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return redirect(url_for("register_page", error="Ya existe una cuenta con ese email."))

    hashed = generate_password_hash(password)
    conn.execute(
        "INSERT INTO users (name, email, password, plan) VALUES (?, ?, ?, ?)",
        (name, email, hashed, plan),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("login_page", success="Cuenta creada. Inicia sesión."))


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    if not email or not password:
        return redirect(url_for("login_page", error="Ingresa email y contraseña."))

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password"], password):
        return redirect(url_for("login_page", error="Email o contraseña incorrectos."))

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_plan"] = user["plan"]
    return redirect(url_for("player"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/player")
@login_required
def player():
    user = get_current_user()
    return render_template("landing.html", user=user)


@app.route("/legacy")
def legacy():
    return render_template("index.html")


@app.route("/enigma")
def enigma():
    return render_template("enigma.html")


@app.route("/api/playlist", methods=["POST"])
def api_playlist():
    """Recibe {url} o un archivo 'file'. Devuelve canales + grupos."""
    text = None
    src = ""

    if request.files.get("file"):
        f = request.files["file"]
        text = f.read().decode("utf-8", errors="replace")
        src = f.filename
    else:
        data = request.get_json(silent=True) or {}
        url = (data.get("url") or "").strip()
        ua = (data.get("ua") or "").strip() or DEFAULT_UA
        if not url:
            return jsonify(error="Falta la URL o el archivo de la lista."), 400

        # Handle local file paths
        if url.startswith("/static/"):
            import os

            local_path = os.path.join(os.path.dirname(__file__), url.lstrip("/"))
            if os.path.exists(local_path):
                with open(local_path, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read()
                src = url
            else:
                return jsonify(error=f"Archivo local no encontrado: {url}"), 404
        else:
            try:
                r = SESSION.get(
                    url,
                    headers={"User-Agent": ua},
                    timeout=TIMEOUT,
                    allow_redirects=True,
                )
                r.raise_for_status()
                text = r.text
                src = url
            except requests.RequestException as e:
                return jsonify(error=f"No se pudo descargar la lista: {e}"), 502

    if not text or not text.strip():
        return jsonify(error="La lista está vacía o no es un M3U válido."), 400

    channels, groups = parse_m3u(text, name_hint=src)

    return jsonify(source=src, count=len(channels), groups=groups, channels=channels)


def _passthrough_headers(upstream):
    out = {}
    for h in (
        "Content-Type",
        "Content-Length",
        "Cache-Control",
        "Accept-Ranges",
        "Content-Range",
    ):
        if h in upstream.headers:
            out[h] = upstream.headers[h]
    out["Access-Control-Allow-Origin"] = "*"
    return out


def _is_playlist(url, content_type, head):
    if "mpegurl" in (content_type or "").lower():
        return True
    if url.split("?")[0].lower().endswith((".m3u8", ".m3u")):
        return True
    return head.lstrip().upper().startswith("#EXTM3U")


def _rewrite_playlist(text, base_url, ua, referer):
    """Reescribe URIs de una playlist HLS para que pasen por /stream."""

    def wrap(target):
        absu = urljoin(base_url, target.strip())
        q = "/stream?url=" + quote(absu, safe="")
        if ua:
            q += "&ua=" + quote(ua, safe="")
        if referer:
            q += "&referer=" + quote(referer, safe="")
        return q

    out_lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            out_lines.append(line)
            continue
        if s.startswith("#"):
            # reescribe atributos URI="..." (EXT-X-KEY, EXT-X-MEDIA, EXT-X-MAP)
            m = re.search(r'URI="([^"]+)"', s)
            if m:
                new = s.replace(m.group(1), wrap(m.group(1)))
                out_lines.append(new)
            else:
                out_lines.append(line)
        else:
            out_lines.append(wrap(s))
    return "\n".join(out_lines)


@app.route("/stream")
def stream():
    """Proxy de streams: reescribe playlists y reenvía segmentos."""
    url = request.args.get("url", "")
    if not url:
        return "Falta url", 400
    url = unquote(url)
    ua = unquote(request.args.get("ua", "")) or DEFAULT_UA
    referer = unquote(request.args.get("referer", ""))

    headers = {"User-Agent": ua}
    if referer:
        headers["Referer"] = referer
    # reenvía Range para seeking en VOD / mp4
    if "Range" in request.headers:
        headers["Range"] = request.headers["Range"]

    try:
        upstream = SESSION.get(
            url, headers=headers, stream=True, timeout=TIMEOUT, allow_redirects=True
        )
    except requests.RequestException as e:
        return f"Error upstream: {e}", 502

    ctype = upstream.headers.get("Content-Type", "")
    # leemos un pedazo para olfatear si es playlist
    first = next(upstream.iter_content(chunk_size=4096), b"")
    head = first[:512].decode("utf-8", errors="ignore")

    if _is_playlist(url, ctype, head):
        # ya consumimos 'first'; juntamos el resto del cuerpo
        body = first + b"".join(upstream.iter_content(chunk_size=64 * 1024))
        try:
            text = body.decode("utf-8", errors="replace")
        except Exception:
            text = first.decode("utf-8", errors="replace")
        rewritten = _rewrite_playlist(text, url, ua, referer)
        return Response(
            rewritten,
            content_type="application/vnd.apple.mpegurl",
            headers={"Access-Control-Allow-Origin": "*"},
        )

    # segmento / binario: streaming directo
    def generate():
        yield first
        for chunk in upstream.iter_content(chunk_size=64 * 1024):
            if chunk:
                yield chunk

    status = upstream.status_code
    return Response(
        stream_with_context(generate()),
        status=status,
        headers=_passthrough_headers(upstream),
    )


@app.route("/api/check", methods=["POST"])
def api_check():
    """Comprobacion rapida de disponibilidad de un stream."""
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify(ok=False, reason="sin-url")
    ua = (data.get("ua") or "").strip() or DEFAULT_UA
    referer = (data.get("referer") or "").strip()
    headers = {"User-Agent": ua}
    if referer:
        headers["Referer"] = referer
    try:
        r = SESSION.get(
            url, headers=headers, stream=True, timeout=6, allow_redirects=True
        )
        ok = r.status_code < 400
        if ok:
            chunk = next(r.iter_content(chunk_size=2048), b"")
            r.close()
            looks_hls = "#EXTM3U" in chunk[:64].decode(
                "utf-8", "ignore"
            ).upper() or url.split("?")[0].lower().endswith((".m3u8", ".m3u"))
            if looks_hls:
                txt = chunk.decode("utf-8", "ignore")
                # reproducible si la playlist trae variantes o segmentos
                has_body = (
                    "#EXT-X-STREAM-INF" in txt
                    or "#EXTINF" in txt
                    or ".ts" in txt
                    or ".m3u8" in txt
                    or any(
                        ln.strip() and not ln.startswith("#") for ln in txt.splitlines()
                    )
                )
                ok = has_body
            else:
                ok = len(chunk) > 0
        else:
            r.close()
        return jsonify(ok=bool(ok), status=r.status_code)
    except requests.RequestException:
        return jsonify(ok=False, reason="timeout-o-error")


@app.route("/api/playlists", methods=["GET"])
def api_playlists():
    """Lista las playlists disponibles en el directorio static."""
    import os
    import glob as glob_module

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    m3u_files = glob_module.glob(os.path.join(static_dir, "*.m3u8")) + glob_module.glob(
        os.path.join(static_dir, "*.m3u")
    )

    playlists = []
    for filepath in m3u_files:
        filename = os.path.basename(filepath)
        playlists.append(
            {
                "name": filename.replace(".m3u8", "")
                .replace(".m3u", "")
                .replace("_", " ")
                .title(),
                "filename": filename,
                "url": f"/static/{filename}",
            }
        )

    return jsonify(playlists=playlists)


@app.route("/health")
def health():
    return jsonify(ok=True, ts=time.time())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8088, threaded=True, debug=False)
