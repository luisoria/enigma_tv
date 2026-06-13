#!/usr/bin/env python3
"""
Obtiene servidores IPTV Xtream desde la API de RapidAPI y genera
un archivo .m3u8 completo con todos los canales.

Flujo:
1. Consulta la API de RapidAPI para obtener credenciales Xtream.
2. Para cada servidor, usa la API Xtream (player_api.php) para
   obtener categorías y canales.
3. Genera un .m3u8 con todos los canales encontrados.
"""
import json
import sys
import time
import requests

# ── Configuración de la API de RapidAPI ──────────────────────────────
RAPIDAPI_URL = "https://free-daily-xtream-iptv-servers.p.rapidapi.com/get"
RAPIDAPI_HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": "free-daily-xtream-iptv-servers.p.rapidapi.com",
    "x-rapidapi-key": "7507f05353msh36a64955e30579cp1491c7jsn6d81e3186882",
}

OUTPUT_FILE = "iptv_list.m3u8"
TIMEOUT = 20


def fetch_xtream_servers():
    """Consulta la API de RapidAPI para obtener servidores Xtream."""
    print("=" * 60)
    print("  Consultando API de RapidAPI...")
    print("=" * 60)
    try:
        resp = requests.get(RAPIDAPI_URL, headers=RAPIDAPI_HEADERS, timeout=TIMEOUT)
        print(f"  Status: {resp.status_code}")
        print(f"  Content-Length: {len(resp.content)} bytes")

        if resp.status_code != 200:
            print(f"  Error HTTP: {resp.status_code}")
            print(f"  Body: {resp.text[:500]}")
            return []

        if not resp.content or not resp.text.strip():
            print("  ⚠  La API devolvió respuesta vacía.")
            print("     (Es probable que no haya servidores disponibles hoy)")
            return []

        data = resp.json()
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            for key in ("servers", "data", "results", "items", "list"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            return [data]
        return []
    except requests.RequestException as e:
        print(f"  Error de red: {e}")
        return []
    except json.JSONDecodeError:
        print(f"  La respuesta no es JSON válido: {resp.text[:200]}")
        return []


def fetch_xtream_channels(server):
    """
    Dado un servidor Xtream (dict con host/port/username/password),
    obtiene la lista de canales live usando player_api.php.
    """
    host = server.get("host") or server.get("server") or server.get("url") or ""
    port = server.get("port") or ""
    user = server.get("username") or server.get("user") or ""
    pwd = server.get("password") or server.get("pass") or ""

    if not host or not user or not pwd:
        return [], "", ""

    base = host.rstrip("/")
    if not base.startswith("http"):
        base = f"http://{base}"
    if port:
        base = f"{base}:{port}"

    print(f"\n  Conectando a: {base}")
    print(f"  Usuario: {user}")

    # 1. Obtener categorías
    categories = {}
    try:
        cat_url = f"{base}/player_api.php?username={user}&password={pwd}&action=get_live_categories"
        r = requests.get(cat_url, timeout=TIMEOUT)
        if r.status_code == 200:
            cats = r.json()
            if isinstance(cats, list):
                for c in cats:
                    cid = str(c.get("category_id", ""))
                    cname = c.get("category_name", "Sin grupo")
                    if cid:
                        categories[cid] = cname
                print(f"  ✓ Categorías: {len(categories)}")
    except Exception as e:
        print(f"  ⚠ Error obteniendo categorías: {e}")

    # 2. Obtener canales live
    channels = []
    try:
        ch_url = f"{base}/player_api.php?username={user}&password={pwd}&action=get_live_streams"
        r = requests.get(ch_url, timeout=TIMEOUT)
        if r.status_code == 200:
            streams = r.json()
            if isinstance(streams, list):
                for s in streams:
                    sid = s.get("stream_id", "")
                    name = s.get("name", "Sin nombre")
                    icon = s.get("stream_icon", "")
                    cat_id = str(s.get("category_id", ""))
                    group = categories.get(cat_id, "Sin grupo")
                    epg_id = s.get("epg_channel_id", "")

                    # URL de reproducción directa
                    stream_url = f"{base}/live/{user}/{pwd}/{sid}.ts"

                    channels.append({
                        "name": name,
                        "logo": icon,
                        "group": group,
                        "tvg_id": epg_id,
                        "url": stream_url,
                    })
                print(f"  ✓ Canales live: {len(channels)}")
    except Exception as e:
        print(f"  ⚠ Error obteniendo canales: {e}")

    return channels, base, user


def channels_to_m3u8(all_channels):
    """Convierte lista de canales a formato M3U8."""
    lines = ["#EXTM3U"]
    for ch in all_channels:
        attrs = []
        if ch.get("tvg_id"):
            attrs.append(f'tvg-id="{ch["tvg_id"]}"')
        if ch.get("logo"):
            attrs.append(f'tvg-logo="{ch["logo"]}"')
        if ch.get("group"):
            attrs.append(f'group-title="{ch["group"]}"')

        attr_str = " ".join(attrs)
        if attr_str:
            attr_str = " " + attr_str

        lines.append(f'#EXTINF:-1{attr_str},{ch["name"]}')
        lines.append(ch["url"])

    return "\n".join(lines) + "\n"


def servers_to_m3u8(servers):
    """
    Si no se pudieron obtener canales individuales,
    genera un M3U8 con las URLs de playlist completa de cada servidor.
    """
    lines = ["#EXTM3U"]
    for i, srv in enumerate(servers):
        host = srv.get("host") or srv.get("server") or srv.get("url") or ""
        port = srv.get("port") or ""
        user = srv.get("username") or srv.get("user") or ""
        pwd = srv.get("password") or srv.get("pass") or ""

        if not host:
            continue

        base = host.rstrip("/")
        if not base.startswith("http"):
            base = f"http://{base}"
        if port:
            base = f"{base}:{port}"

        # URL M3U completa del servidor
        m3u_url = f"{base}/get.php?username={user}&password={pwd}&type=m3u_plus&output=ts"
        name = srv.get("name") or f"Servidor Xtream {i+1}"

        lines.append(f'#EXTINF:-1 group-title="Servidores Xtream",{name}')
        lines.append(m3u_url)

    return "\n".join(lines) + "\n"


def main():
    start = time.time()

    # Paso 1: Obtener servidores de la API
    servers = fetch_xtream_servers()

    all_channels = []

    if servers:
        print(f"\n✓ Se encontraron {len(servers)} servidor(es) Xtream")
        print(f"\nEstructura del primer servidor:")
        print(json.dumps(servers[0], indent=2, ensure_ascii=False)[:500])

        # Paso 2: Intentar obtener canales de cada servidor
        for i, srv in enumerate(servers):
            print(f"\n{'─' * 50}")
            print(f"  Servidor {i+1}/{len(servers)}")
            channels, base, user = fetch_xtream_channels(srv)
            all_channels.extend(channels)

        if all_channels:
            # Generar M3U8 con canales individuales
            m3u_content = channels_to_m3u8(all_channels)
        else:
            # Fallback: generar M3U8 con URLs de playlist completa
            print("\n⚠ No se pudieron obtener canales individuales.")
            print("  Generando M3U8 con URLs de playlist completa...")
            m3u_content = servers_to_m3u8(servers)
    else:
        print("\n⚠ La API no devolvió servidores.")
        print("  Esto suele ocurrir porque los servidores gratuitos se")
        print("  actualizan diariamente y puede que no haya disponibles ahora.")
        print("\n  Generando archivo M3U8 de ejemplo con listas públicas...")

        # Generar M3U8 con streams de prueba públicos y funcionales
        m3u_content = """#EXTM3U
#EXTINF:-1 tvg-id="PlutoTV" tvg-logo="" group-title="Entretenimiento",Pluto TV - Cine Estelar
https://service-stitcher.clusters.pluto.tv/v1/stitch/embed/hls/channel/5ddb9644b1cdfc0009c4ec5f/master.m3u8?advertisingId=&appName=web&appVersion=5.14.0&deviceDNT=0&deviceId=channel&deviceMake=&deviceModel=web&deviceType=web&deviceVersion=5.14.0
#EXTINF:-1 tvg-id="PlutoTV" tvg-logo="" group-title="Entretenimiento",Pluto TV - Cine Acción
https://service-stitcher.clusters.pluto.tv/v1/stitch/embed/hls/channel/5ddb961b7c5e210009f0f27a/master.m3u8?advertisingId=&appName=web&appVersion=5.14.0&deviceDNT=0&deviceId=channel&deviceMake=&deviceModel=web&deviceType=web&deviceVersion=5.14.0
#EXTINF:-1 tvg-id="PlutoTV" tvg-logo="" group-title="Entretenimiento",Pluto TV - Cine Drama
https://service-stitcher.clusters.pluto.tv/v1/stitch/embed/hls/channel/5ddb96a52b76b20009beaf10/master.m3u8?advertisingId=&appName=web&appVersion=5.14.0&deviceDNT=0&deviceId=channel&deviceMake=&deviceModel=web&deviceType=web&deviceVersion=5.14.0
#EXTINF:-1 tvg-id="PlutoTV" tvg-logo="" group-title="Noticias",Pluto TV - Noticias
https://service-stitcher.clusters.pluto.tv/v1/stitch/embed/hls/channel/625a5e3db527f100073dc3a2/master.m3u8?advertisingId=&appName=web&appVersion=5.14.0&deviceDNT=0&deviceId=channel&deviceMake=&deviceModel=web&deviceType=web&deviceVersion=5.14.0
#EXTINF:-1 tvg-id="PlutoTV" tvg-logo="" group-title="Noticias",Pluto TV - CNN en Español
https://service-stitcher.clusters.pluto.tv/v1/stitch/embed/hls/channel/5f7b6742635ba40007aa4b8e/master.m3u8?advertisingId=&appName=web&appVersion=5.14.0&deviceDNT=0&deviceId=channel&deviceMake=&deviceModel=web&deviceType=web&deviceVersion=5.14.0
#EXTINF:-1 tvg-id="PlutoTV" tvg-logo="" group-title="Deportes",Pluto TV - Deportes
https://service-stitcher.clusters.pluto.tv/v1/stitch/embed/hls/channel/5ddb964d2f819c00098bd456/master.m3u8?advertisingId=&appName=web&appVersion=5.14.0&deviceDNT=0&deviceId=channel&deviceMake=&deviceModel=web&deviceType=web&deviceVersion=5.14.0
#EXTINF:-1 tvg-id="PlutoTV" tvg-logo="" group-title="Infantil",Pluto TV - Animación
https://service-stitcher.clusters.pluto.tv/v1/stitch/embed/hls/channel/5f4a89b0c889740007b19503/master.m3u8?advertisingId=&appName=web&appVersion=5.14.0&deviceDNT=0&deviceId=channel&deviceMake=&deviceModel=web&deviceType=web&deviceVersion=5.14.0
#EXTINF:-1 tvg-id="PlutoTV" tvg-logo="" group-title="Música",Pluto TV - MTV Hits
https://service-stitcher.clusters.pluto.tv/v1/stitch/embed/hls/channel/5f7b67c3635ba40007aa4dc0/master.m3u8?advertisingId=&appName=web&appVersion=5.14.0&deviceDNT=0&deviceId=channel&deviceMake=&deviceModel=web&deviceType=web&deviceVersion=5.14.0
#EXTINF:-1 tvg-id="PlutoTV" tvg-logo="" group-title="Entretenimiento",Pluto TV - Reality
https://service-stitcher.clusters.pluto.tv/v1/stitch/embed/hls/channel/5ddb966e5f80350009a493c7/master.m3u8?advertisingId=&appName=web&appVersion=5.14.0&deviceDNT=0&deviceId=channel&deviceMake=&deviceModel=web&deviceType=web&deviceVersion=5.14.0
#EXTINF:-1 tvg-id="PlutoTV" tvg-logo="" group-title="Entretenimiento",Pluto TV - Comedy
https://service-stitcher.clusters.pluto.tv/v1/stitch/embed/hls/channel/5ddb965df32cab0009c56c8a/master.m3u8?advertisingId=&appName=web&appVersion=5.14.0&deviceDNT=0&deviceId=channel&deviceMake=&deviceModel=web&deviceType=web&deviceVersion=5.14.0
"""
        all_channels = []  # indicar que usamos fallback

    # Guardar archivo
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(m3u_content)

    elapsed = time.time() - start

    # Resumen
    print(f"\n{'=' * 60}")
    print(f"  RESULTADO")
    print(f"{'=' * 60}")
    count = m3u_content.count("#EXTINF")
    print(f"  Archivo generado: {OUTPUT_FILE}")
    print(f"  Total de canales: {count}")
    print(f"  Tamaño: {len(m3u_content):,} bytes")
    print(f"  Tiempo: {elapsed:.1f}s")

    # Mostrar grupos
    groups = set()
    for line in m3u_content.splitlines():
        if 'group-title="' in line:
            g = line.split('group-title="')[1].split('"')[0]
            groups.add(g)
    if groups:
        print(f"  Grupos: {', '.join(sorted(groups))}")

    print(f"\n  Primeras líneas del archivo:")
    for line in m3u_content.splitlines()[:15]:
        print(f"    {line}")

    print(f"\n{'=' * 60}")
    print(f"  ✓ Listo. Carga '{OUTPUT_FILE}' en tu Portal IPTV")
    print(f"    http://127.0.0.1:8088")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
