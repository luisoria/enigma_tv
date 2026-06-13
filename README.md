# Señal — Portal IPTV local

Reproductor web local para listas `.m3u` / `.m3u8`. Carga la lista por URL o
archivo, parsea los canales (nombre, logo, grupo) y los reproduce en el
navegador. Incluye un proxy interno que resuelve el **CORS** y permite forzar
**User-Agent** y **Referer**, reescribiendo las playlists HLS para que los
segmentos pasen por el proxy.

La lista la aportas tú. La app es solo el reproductor.

## Requisitos
- Python 3.9+

## Instalación y uso
```bash
cd iptv-portal
python3 -m venv .venv && source .venv/bin/activate   # opcional
pip install -r requirements.txt
python3 app.py
```
Abre: http://127.0.0.1:8088

1. Pestaña **URL**: pega la URL de tu lista (`.m3u`/`.m3u8`). Opcional: un
   User-Agent si el proveedor lo exige.
2. Pestaña **Archivo**: sube un `.m3u` local.
3. Busca por nombre, filtra por grupo y haz clic en un canal.

## Cómo funciona el proxy
- `POST /api/playlist` — descarga/parsea la lista → JSON de canales.
- `GET /stream?url=...&ua=...&referer=...` — proxy:
  - Si es playlist HLS, reescribe las URIs de segmentos/llaves para enrutarlas
    de vuelta por `/stream` (evita CORS y mantiene la cadena de cabeceras).
  - Si es segmento/binario, lo reenvía en streaming (soporta `Range`).

## Notas
- Por defecto escucha solo en `127.0.0.1` (no se expone a la red). Si quieres
  acceso desde la LAN, cambia `host` en `app.py` a `0.0.0.0` y protégelo
  detrás de tu ingress (Traefik) — no lo dejes abierto.
- `#EXTVLCOPT:http-user-agent` y `http-referrer` de la lista se respetan por
  canal.
- Para empaquetar en Docker, una imagen `python:3.12-slim` + `gunicorn` basta;
  recuerda que el proxy hace egress hacia los CDN de los streams.

## Estructura
```
app.py              backend Flask (UI + parse + proxy)
templates/index.html
static/styles.css
static/app.js
sample.m3u          lista de prueba
requirements.txt
```
