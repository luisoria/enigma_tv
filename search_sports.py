#!/usr/bin/env python3
import requests

urls = [
    'https://iptv-org.github.io/iptv/categories/sports.m3u',
    'https://iptv-org.github.io/iptv/countries/ve.m3u',
    'https://iptv-org.github.io/iptv/countries/ar.m3u',
    'https://iptv-org.github.io/iptv/countries/mx.m3u',
    'https://iptv-org.github.io/iptv/countries/us.m3u',
    'https://iptv-org.github.io/iptv/countries/co.m3u',
    'https://iptv-org.github.io/iptv/countries/cl.m3u',
]

keywords = ['espn', 'directv', 'fox sport', 'dsports', 'win sport',
            'tdn', 'tudn', 'bein', 'deportv', 'tyc sport', 'gol tv',
            'star sport', 'dazn']

found = []
seen_urls = set()

for list_url in urls:
    try:
        fname = list_url.split("/")[-1]
        print(f"Descargando: {fname}...")
        r = requests.get(list_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            print(f"  FAIL status {r.status_code}")
            continue

        lines = r.text.splitlines()
        print(f"  {len(lines)} lineas")

        for i, line in enumerate(lines):
            if line.startswith("#EXTINF"):
                name_lower = line.lower()
                for kw in keywords:
                    if kw in name_lower:
                        url = ""
                        for j in range(i + 1, min(i + 3, len(lines))):
                            if lines[j].strip() and not lines[j].startswith("#"):
                                url = lines[j].strip()
                                break
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            name = line.split(",", 1)[1].strip() if "," in line else "Sin nombre"
                            found.append((name, url, line))
                            print(f"  >> {name}")
                        break
    except Exception as e:
        msg = str(e)[:80]
        print(f"  Error: {msg}")

print(f"\n{'=' * 50}")
print(f"Canales encontrados: {len(found)}")
print(f"{'=' * 50}")

for name, url, extinf in found:
    print(f"\n  Canal: {name}")
    trunc = url[:130]
    print(f"  URL:   {trunc}")
    print(f"  EXTINF: {extinf[:150]}")

# Verificar cuales funcionan
print(f"\n{'=' * 50}")
print("Verificando cuales funcionan...")
print(f"{'=' * 50}")

working = []
for name, url, extinf in found:
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"}, stream=True)
        ct = r.headers.get("Content-Type", "")
        chunk = next(r.iter_content(512), b"")
        head = chunk.decode("utf-8", errors="ignore")[:200]
        is_hls = head.strip().startswith("#EXTM3U") or head.strip().startswith("#EXT") or "mpegurl" in ct.lower()
        ok = r.status_code == 200 and (is_hls or len(chunk) > 0)
        status = "OK" if ok else f"FAIL({r.status_code})"
        print(f"  {status:10s} {name}")
        if ok:
            working.append((name, url, extinf))
        r.close()
    except Exception as e:
        msg = str(e)[:50]
        print(f"  TIMEOUT    {name} -> {msg}")

print(f"\n{'=' * 50}")
print(f"FUNCIONANDO: {len(working)}/{len(found)}")
print(f"{'=' * 50}")
for name, url, extinf in working:
    print(f"  {name}")
    print(f"    {url}")
