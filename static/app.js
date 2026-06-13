"use strict";

const $ = (s) => document.querySelector(s);
const state = { channels: [], pool: [], filtered: [], activeId: null, ua: "", checked: {} };
const RENDER_LIMIT = 400;   // filas máximas en pantalla (rendimiento)
let searchTimer = null;

let hls = null;
const video = $("#video");

/* ---------- Tabs de carga ---------- */
document.querySelectorAll(".seg").forEach((b) => {
  b.addEventListener("click", () => {
    document.querySelectorAll(".seg").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    document.querySelectorAll(".tab-panel").forEach((p) => {
      p.classList.toggle("hidden", p.dataset.panel !== b.dataset.tab);
    });
  });
});

/* ---------- Estado / mensajes ---------- */
function setStatus(msg, kind = "") {
  const el = $("#status");
  el.textContent = msg;
  el.className = "status " + kind;
}

/* ---------- Carga de lista ---------- */
async function loadUrlValue(url, ua, btn) {
  if (!url) return setStatus("Indica una URL.", "err");
  state.ua = ua || "";
  setStatus("Descargando lista…", "busy");
  if (btn) btn.disabled = true;
  try {
    const r = await fetch("/api/playlist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, ua }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "Error al cargar.");
    ingest(data);
  } catch (e) {
    setStatus(e.message, "err");
  } finally {
    if (btn) btn.disabled = false;
  }
}

function loadFromUrl() {
  loadUrlValue($("#urlInput").value.trim(), $("#uaInput").value.trim(), $("#loadUrl"));
}

function loadCatalog() {
  const url = $("#catalogSel").value;
  if (!url) return setStatus("Elige una fuente del catálogo.", "err");
  loadUrlValue(url, "", $("#loadCatalog"));
}

async function loadFromFile() {
  const f = $("#fileInput").files[0];
  if (!f) return setStatus("Elige un archivo.", "err");
  setStatus("Procesando archivo…", "busy");
  $("#loadFile").disabled = true;
  const fd = new FormData();
  fd.append("file", f);
  try {
    const r = await fetch("/api/playlist", { method: "POST", body: fd });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "Error al procesar.");
    ingest(data);
  } catch (e) {
    setStatus(e.message, "err");
  } finally {
    $("#loadFile").disabled = false;
  }
}

function buildGroups(groups) {
  const sel = $("#groupSel");
  sel.innerHTML = '<option value="">Todos los grupos</option>';
  groups.forEach((g) => {
    const o = document.createElement("option");
    o.value = g;
    o.textContent = g;
    sel.appendChild(o);
  });
}

function ingest(data) {
  state.channels = data.channels;
  state.checked = {};
  $("#metaCount").textContent = `${data.count} canales`;
  buildGroups(data.groups);

  if ($("#autoValidate").checked) {
    validateAndPopulate(data.channels);
  } else {
    state.pool = data.channels;
    setStatus(`${data.count} canales · ${data.groups.length} grupos`, "ok");
    applyFilters();
  }
}

/* ---------- Auto-validación al cargar ---------- */
const VALIDATE_MAX = Infinity;   // sin límite; pon un número para capar
let renderTimer = null;

function scheduleRender() {
  clearTimeout(renderTimer);
  renderTimer = setTimeout(applyFilters, 250);
}

function cancelValidation() {
  if (state._valCtl) state._valCtl.stop = true;
}

async function validateAndPopulate(list) {
  cancelValidation();
  const ctl = (state._valCtl = { stop: false });
  state.pool = [];
  applyFilters();

  const capped = Number.isFinite(VALIDATE_MAX) && list.length > VALIDATE_MAX;
  const candidates = capped ? list.slice(0, VALIDATE_MAX) : list;
  $("#cancelVal").classList.remove("hidden");

  let i = 0, alive = 0, done = 0;
  const CONC = 10;

  async function worker() {
    while (i < candidates.length && !ctl.stop) {
      const c = candidates[i++];
      let ok = false;
      try {
        const r = await fetch("/api/check", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: c.url, ua: c.ua || state.ua, referer: c.referer }),
        });
        const d = await r.json();
        ok = !!d.ok;
      } catch { ok = false; }
      done++;
      if (ok) {
        alive++;
        state.checked[c.id] = "ok";
        state.pool.push(c);
        scheduleRender();           // agrega los buenos en vivo
      } else {
        state.checked[c.id] = "dead";
      }
      setStatus(`Validando… ${done}/${candidates.length} · ${alive} en línea`, "busy");
    }
  }

  await Promise.all(Array.from({ length: CONC }, worker));
  $("#cancelVal").classList.add("hidden");

  // grupos solo de los canales que quedaron
  buildGroups([...new Set(state.pool.map((c) => c.group))].sort());
  applyFilters();

  const note = ctl.stop ? "cancelado · " : "";
  const ofTxt = capped ? ` (de los primeros ${VALIDATE_MAX})` : "";
  setStatus(`${note}${alive} reproducibles${ofTxt} de ${done} comprobados`,
            alive ? "ok" : "err");
}

/* ---------- Filtros ---------- */
function applyFilters() {
  const q = $("#search").value.toLowerCase();
  const g = $("#groupSel").value;
  const pool = state.pool || [];
  state.filtered = pool.filter((c) => {
    if (g && c.group !== g) return false;
    if (q && !c.name.toLowerCase().includes(q)) return false;
    return true;
  });
  renderChannels();
}

/* ---------- Render de canales ---------- */
function renderChannels() {
  const ul = $("#channels");
  ul.innerHTML = "";
  const total = state.filtered.length;
  if (!total) {
    ul.innerHTML = '<li class="empty">Sin coincidencias.<br>Carga una lista o ajusta el filtro.</li>';
    $("#listMeta").textContent = "";
    return;
  }

  const slice = state.filtered.slice(0, RENDER_LIMIT);
  $("#listMeta").textContent =
    total > RENDER_LIMIT
      ? `Mostrando ${RENDER_LIMIT} de ${total} · afina la búsqueda`
      : `${total} canal${total === 1 ? "" : "es"}`;

  const frag = document.createDocumentFragment();
  slice.forEach((c) => {
    const li = document.createElement("li");
    li.className = "ch" + (c.id === state.activeId ? " active" : "");
    li.dataset.id = c.id;

    const logo = document.createElement("div");
    logo.className = "ch-logo";
    if (c.logo) {
      const img = document.createElement("img");
      img.src = c.logo;
      img.loading = "lazy";
      img.onerror = () => { img.remove(); logo.textContent = "TV"; };
      logo.appendChild(img);
    } else {
      logo.textContent = "TV";
    }

    const body = document.createElement("div");
    body.className = "ch-body";
    body.innerHTML = `<div class="ch-name"></div><div class="ch-group"></div>`;
    body.querySelector(".ch-name").textContent = c.name;
    body.querySelector(".ch-group").textContent = c.group;

    const dot = document.createElement("span");
    dot.className = "ch-dot " + (state.checked[c.id] || "");
    dot.title = { ok: "En línea", dead: "Sin respuesta" }[state.checked[c.id]] || "Sin comprobar";

    li.append(logo, body, dot);
    li.addEventListener("click", () => play(c));
    frag.appendChild(li);
  });
  ul.appendChild(frag);
}

/* ---------- Validador de canales ---------- */
async function checkVisible() {
  const btn = $("#checkBtn");
  const slice = state.filtered.slice(0, RENDER_LIMIT);
  if (!slice.length) return;
  btn.disabled = true;
  btn.textContent = "Comprobando…";

  let i = 0, alive = 0;
  const CONCURRENCY = 8;
  async function worker() {
    while (i < slice.length) {
      const c = slice[i++];
      try {
        const r = await fetch("/api/check", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: c.url, ua: c.ua || state.ua, referer: c.referer }),
        });
        const d = await r.json();
        state.checked[c.id] = d.ok ? "ok" : "dead";
        if (d.ok) alive++;
      } catch {
        state.checked[c.id] = "dead";
      }
      const dot = document.querySelector(`.ch[data-id="${c.id}"] .ch-dot`);
      if (dot) {
        dot.className = "ch-dot " + state.checked[c.id];
        dot.title = state.checked[c.id] === "ok" ? "En línea" : "Sin respuesta";
      }
    }
  }
  await Promise.all(Array.from({ length: CONCURRENCY }, worker));

  btn.disabled = false;
  btn.textContent = "Comprobar";
  setStatus(`${alive} en línea de ${slice.length} comprobados`, alive ? "ok" : "err");
}

/* ---------- Reproducción ---------- */
function proxied(rawUrl, ua, referer) {
  let u = "/stream?url=" + encodeURIComponent(rawUrl);
  const finalUa = ua || state.ua;
  if (finalUa) u += "&ua=" + encodeURIComponent(finalUa);
  if (referer) u += "&referer=" + encodeURIComponent(referer);
  return u;
}

function play(c) {
  state.activeId = c.id;
  renderChannels();

  $("#idle").classList.add("hidden");
  $("#tally").classList.add("live");
  $("#onairName").textContent = c.name;
  $("#nowName").textContent = c.name;
  $("#nowSub").textContent = c.group;
  $("#nowLogo").style.backgroundImage = c.logo ? `url("${c.logo}")` : "none";
  $("#nowTech").innerHTML = "Conectando…";

  const src = proxied(c.url, c.ua, c.referer);
  const isHls = /\.m3u8(\?|$)/i.test(c.url) || /mpegurl/i.test(c.url);

  if (hls) { hls.destroy(); hls = null; }

  if (isHls && window.Hls && Hls.isSupported()) {
    hls = new Hls({ lowLatencyMode: true, enableWorker: true });
    hls.loadSource(src);
    hls.attachMedia(video);
    hls.on(Hls.Events.MANIFEST_PARSED, () => video.play().catch(() => {}));
    hls.on(Hls.Events.LEVEL_LOADED, (_, d) => {
      const lvl = hls.levels[hls.currentLevel] || hls.levels[0];
      if (lvl) {
        $("#nowTech").innerHTML =
          `HLS · <b>${lvl.width || "?"}×${lvl.height || "?"}</b><br>${Math.round((lvl.bitrate || 0) / 1000)} kbps`;
      } else {
        $("#nowTech").innerHTML = "HLS · <b>en vivo</b>";
      }
    });
    hls.on(Hls.Events.ERROR, (_, d) => {
      if (d.fatal) $("#nowTech").innerHTML = `<span style="color:var(--red)">Error: ${d.details}</span>`;
    });
  } else {
    // HLS nativo (Safari) o stream directo (mp4/ts)
    video.src = src;
    video.play().catch(() => {});
    $("#nowTech").innerHTML = isHls ? "HLS nativo" : "Directo";
    video.onerror = () => {
      $("#nowTech").innerHTML = '<span style="color:var(--red)">No se pudo reproducir</span>';
    };
  }
}

/* ---------- Eventos ---------- */
$("#loadUrl").addEventListener("click", loadFromUrl);
$("#loadCatalog").addEventListener("click", loadCatalog);
$("#loadFile").addEventListener("click", loadFromFile);
$("#urlInput").addEventListener("keydown", (e) => { if (e.key === "Enter") loadFromUrl(); });
$("#search").addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(applyFilters, 180);
});
$("#groupSel").addEventListener("change", applyFilters);
$("#checkBtn").addEventListener("click", checkVisible);
$("#cancelVal").addEventListener("click", cancelValidation);
$("#fileInput").addEventListener("change", () => {
  const f = $("#fileInput").files[0];
  $("#fileText").textContent = f ? f.name : "Arrastra o elige un .m3u";
});
