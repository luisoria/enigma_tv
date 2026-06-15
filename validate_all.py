#!/usr/bin/env python3
import requests, glob, os

static = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
files = glob.glob(os.path.join(static, '*.m3u8')) + glob.glob(os.path.join(static, '*.m3u'))

all_channels = []
for f in sorted(files):
    fname = os.path.basename(f)
    with open(f, 'r', encoding='utf-8', errors='replace') as fh:
        lines = fh.readlines()
    name = ''
    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF'):
            name = line.split(',', 1)[1].strip() if ',' in line else 'Sin nombre'
        elif line and not line.startswith('#'):
            all_channels.append((fname, name or 'Sin nombre', line))
            name = ''

print(f"Total canales: {len(all_channels)} en {len(files)} archivos")
sep = "=" * 70
print(sep)

ok_list = []
fail_list = []

for fname, name, url in all_channels:
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}, stream=True)
        ct = r.headers.get("Content-Type", "")
        chunk = next(r.iter_content(1024), b"")
        head = chunk.decode("utf-8", errors="ignore")[:200]
        is_hls = head.strip().startswith("#EXTM3U") or head.strip().startswith("#EXT") or "mpegurl" in ct.lower()
        ok = r.status_code == 200 and (is_hls or len(chunk) > 100)
        r.close()
        if ok:
            ok_list.append((fname, name, url))
            print(f"  OK       [{fname}] {name}")
        else:
            fail_list.append((fname, name, url, r.status_code))
            print(f"  FAIL({r.status_code:3d}) [{fname}] {name}")
    except Exception as e:
        fail_list.append((fname, name, url, "TIMEOUT"))
        print(f"  TIMEOUT  [{fname}] {name}")

print(f"\n{sep}")
print(f"OK: {len(ok_list)} / {len(all_channels)}")
print(f"CAIDOS: {len(fail_list)}")
if fail_list:
    print(f"\nCanales caidos:")
    for fname, name, url, code in fail_list:
        print(f"  [{fname}] {name} -> {code}")
        print(f"    {url[:120]}")
