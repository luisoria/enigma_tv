#!/usr/bin/env python3
import requests
import time

# Excluir estos canales
exclude = [
    "pluto tv deportes",
    "aspor",
    "m-net sport",
    "bek tv",
    "pluto tv sports us",
    "plutosports",
]

channels = [
    ("AntenaSport", "https://stream1.antenaplay.ro/as/asrolive1/playlist.m3u8"),
    (
        "Belarus 5",
        "https://ngtrk.dc.beltelecom.by/ngtrk/smil:belarus5.smil/playlist.m3u8",
    ),
    (
        "CBS Sports Golazo",
        "https://dai.google.com/linear/hls/event/GxrCGmwST0ixsrc_QgB6qw/master.m3u8",
    ),
    (
        "Inter TV",
        "https://open.http.mp.streamamg.com/p/3001560/sp/300156000/playManifest/entryId/0_xmkk2kjr/flavorIds/0_zlbr85f8,0_zlbr85f8,0_noewhew2/format/applehttp/protocol/https/a.m3u8",
    ),
    ("MadeinBO TV", "https://srvx1.selftv.video/dmchannel/live/playlist.m3u8"),
    (
        "NBC Sports",
        "https://xumo-xumoent-vc-122-sjv70.fast.nbcuni.com/live/master.m3u8",
    ),
    ("Trace Sports Stars", "https://trace-sportstars-samsungnz.amagi.tv/playlist.m3u8"),
    ("TR Sport", "https://livetr.teleromagna.it/mia/live/playlist.m3u8"),
    ("Unbeaten", "https://unbeaten-tcl.amagi.tv/playlist.m3u8"),
    (
        "Red Bull TV",
        "https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8",
    ),
    (
        "FITE 24/7",
        "https://d3d85c7qkywguj.cloudfront.net/v1/master/9d062541f2ff39b5c0f48b743c6411d25f62fc25/FiteTV-Nuestra/263.m3u8",
    ),
    ("TVS Boxing", "https://bozztv.com/gusa/gusa-tvsboxing/index.m3u8"),
    ("Fox Sports (ES)", "https://lnc-fox-sports-espanol2.tubi.video/index.m3u8"),
    ("Fox Sports (EN)", "https://lnc-fox-sports2.tubi.video/index.m3u8"),
    ("Fubo Sports", "https://apollo.production-public.tubi.io/live/ac-fubo.m3u8"),
    ("Stadium", "https://apollo.production-public.tubi.io/live/ac-stadium2.m3u8"),
    ("TVS Classic Sports", "https://bozztv.com/gusa/gusa-tvs/index.m3u8"),
    ("TVS Sports", "https://bozztv.com/gusa/gusa-tvssports/index.m3u8"),
    ("TVS Sports Bureau", "https://bozztv.com/gusa/gusa-tvssportsbureau/index.m3u8"),
    ("TVS Turbo", "https://bozztv.com/gusa/gusa-tvsturbo/index.m3u8"),
    ("TVS Bowling", "https://bozztv.com/gusa/gusa-tvsbowling/index.m3u8"),
    ("TVS Women Sports", "https://bozztv.com/gusa/gusa-tvswsn/index.m3u8"),
    ("Pac 12 Insider", "https://pac12-firetv.amagi.tv/playlist.m3u8"),
    (
        "Women Sports Network",
        "https://lnc-fast-studios-womens-sports.tubi.video/playlist.m3u8",
    ),
    ("SportsGrid", "https://amg00315-sportsgrid-firetv.amagi.tv/playlist.m3u8"),
    ("NHRA TV", "https://apollo.production-public.tubi.io/live/ac-nhra.m3u8"),
    ("NBA G League", "https://apollo.production-public.tubi.io/live/nba-g-league.m3u8"),
    ("NHL Tubi", "https://apollo.production-public.tubi.io/live/ac-nhl.m3u8"),
    ("MavTV Select", "https://mavtv-mavtvglobal-1-eu.rakuten.wurl.tv/playlist.m3u8"),
    ("Mav TV", "https://mavtv-mavtvglobal-1-in.samsung.wurl.tv/playlist.m3u8"),
    (
        "DAZN Womens Football",
        "https://apollo.production-public.tubi.io/live/dazn-womens-football.m3u8",
    ),
    ("Racing America", "https://lnc-racing-america.tubi.video/playlist.m3u8"),
    ("Billiards+", "https://lte.wiseplayout.com/WiseM3U8_18/master.m3u8"),
    ("Rugby Zone TV", "https://lte.wiseplayout.com/WiseM3U8_19/master.m3u8"),
    (
        "Cricket TV Gold",
        "https://d382r3rgbxdixq.cloudfront.net/v1/manifest/9d062541f2ff39b5c0f48b743c6411d25f62fc25/STIRR-MuxIP-CricketGold/a65cfa82-5804-440f-89bb-e82085655f1e/4.m3u8",
    ),
    (
        "Cornhole TV",
        "https://dbrb49pjoymg4.cloudfront.net/manifest/3fec3e5cac39a52b2132f9c66c83dae043dc17d4/prod_default_xumo-ams-aws/27607a86-358e-4a9f-98d9-9aa3fa3c13a6/2.m3u8",
    ),
    (
        "Surfing TV",
        "https://dr4jwhk0sty71.cloudfront.net/v1/manifest/9d062541f2ff39b5c0f48b743c6411d25f62fc25/STIRR-MuxIP-SurfingPlus/2db134b8-501d-4aed-a2da-3570b2643f36/2.m3u8",
    ),
    (
        "PBR RidePass",
        "http://cfd-v4-service-channel-stitcher-use1-1.prd.pluto.tv/stitch/hls/channel/60d39387706fe50007fda8e8/master.m3u8?appName=web&appVersion=unknown&clientTime=0&deviceDNT=0&deviceId=6c2a9f21-30d3-11ef-9cf5-e9ddff8ff496&deviceMake=Chrome&deviceModel=web&deviceType=web&deviceVersion=unknown&includeExtendedEvents=false&serverSideAds=false&sid=f7275d4e-aa8e-4e8d-9d5e-6a5665bf8190",
    ),
    (
        "Strongman",
        "http://cfd-v4-service-channel-stitcher-use1-1.prd.pluto.tv/stitch/hls/channel/5e1452156c07b50009d0230e/master.m3u8?appName=web&appVersion=unknown&clientTime=0&deviceDNT=0&deviceId=84af8ae0-4b92-11ef-aece-533610f1ea34&deviceMake=Chrome&deviceModel=web&deviceType=web&deviceVersion=unknown&includeExtendedEvents=false&serverSideAds=false&sid=c0be139f-be68-4d55-940e-e5aae0d99e04",
    ),
    (
        "Monster Jam",
        "http://cfd-v4-service-channel-stitcher-use1-1.prd.pluto.tv/stitch/hls/channel/65c69b683ba51e00084534a3/master.m3u8?appName=web&appVersion=unknown&clientTime=0&deviceDNT=0&deviceId=6c29dbd5-30d3-11ef-9cf5-e9ddff8ff496&deviceMake=Chrome&deviceModel=web&deviceType=web&deviceVersion=unknown&includeExtendedEvents=false&serverSideAds=false&sid=414e0846-04a7-4d68-9f4e-a8c0750c4959",
    ),
    (
        "Motorvision TV",
        "http://cfd-v4-service-channel-stitcher-use1-1.prd.pluto.tv/stitch/hls/channel/6093f2ae4dd5ab0007d1ff9d/master.m3u8?appName=web&appVersion=unknown&clientTime=0&deviceDNT=0&deviceId=84addd30-4b92-11ef-aece-533610f1ea34&deviceMake=Chrome&deviceModel=web&deviceType=web&deviceVersion=unknown&includeExtendedEvents=false&serverSideAds=false&sid=456ff785-b712-4c67-a20f-5327add4053e",
    ),
    (
        "Pluto TV Extreme FR",
        "http://cfd-v4-service-channel-stitcher-use1-1.prd.pluto.tv/stitch/hls/channel/5f8ed327f9e9b0000761141e/master.m3u8?appName=web&appVersion=unknown&clientTime=0&deviceDNT=0&deviceId=8e055173-1f2c-11ef-86d8-5d587df108c6&deviceMake=Chrome&deviceModel=web&deviceType=web&deviceVersion=unknown&includeExtendedEvents=false&serverSideAds=false&sid=7522642e-9d44-4966-a890-495997625c28",
    ),
    (
        "Pluto TV Motor FR",
        "http://cfd-v4-service-channel-stitcher-use1-1.prd.pluto.tv/stitch/hls/channel/618d4ea306d23b0007356080/master.m3u8?appName=web&appVersion=unknown&clientTime=0&deviceDNT=0&deviceId=8e0662e3-1f2c-11ef-86d8-5d587df108c6&deviceMake=Chrome&deviceModel=web&deviceType=web&deviceVersion=unknown&includeExtendedEvents=false&serverSideAds=false&sid=1d7e5e82-392b-4e7e-84f2-2f5ce35e088d",
    ),
    (
        "Pluto TV Sports FR",
        "http://cfd-v4-service-channel-stitcher-use1-1.prd.pluto.tv/stitch/hls/channel/6081310e48d3200007afaf3b/master.m3u8?appName=web&appVersion=unknown&clientTime=0&deviceDNT=0&deviceId=8e05c6a5-1f2c-11ef-86d8-5d587df108c6&deviceMake=Chrome&deviceModel=web&deviceType=web&deviceVersion=unknown&includeExtendedEvents=false&serverSideAds=false&sid=aa2cd1f8-5f20-441d-97cb-63e4c1c5e4f6",
    ),
    (
        "Pluto TV Sports UK",
        "https://service-stitcher.clusters.pluto.tv/stitch/hls/channel/6081310e48d3200007afaf3b/master.m3u8?appName=web&appVersion=unknown&clientTime=0&deviceDNT=0&deviceId=2c8bf322-e98a-11eb-a932-2f3c780ff9ff&deviceMake=Chrome&deviceModel=web&deviceType=web&deviceVersion=unknown&includeExtendedEvents=false&serverSideAds=false&sid=0727f4fb-ea0b-4814-bb58-fdf3c4534220",
    ),
    (
        "Pluto TV Surf DE",
        "https://service-stitcher.clusters.pluto.tv/stitch/hls/channel/5d1ce51dbaca4afdb7abfe5f/master.m3u8?advertisingId=&appName=web&appVersion=DNT&deviceDNT=1&deviceId=5d1ce51dbaca4afdb7abfe5f&deviceMake=web&deviceModel=web&deviceType=web&deviceVersion=DNT&includeExtendedEvents=false&marketingRegion=DE&serverSideAds=false&sid=abec40e3-86b9-48b6-981d-dc5eeecc6cf9&terminate=false&userId=",
    ),
    (
        "Pluto TV Sport IT",
        "https://stitcher-ipv4.pluto.tv/v1/stitch/embed/hls/channel/608030eff4b6f70007e1684c/master.m3u8?advertisingId={PSID}&appVersion=unknown&deviceDNT={TARGETOPT}&deviceId={PSID}&deviceLat=0&deviceLon=0&deviceMake=samsung&deviceModel=samsung&deviceType=samsung-tvplus&deviceVersion=unknown&embedPartner=samsung-tvplus&profileFloor=&profileLimit=&samsung_app_domain={APP_DOMAIN}&samsung_app_name={APP_NAME}&us_privacy=1YNY",
    ),
]

print(f"Total: {len(channels)} canales")
print("=" * 60)

active = []
for name, url in channels:
    name_lower = name.lower()
    skip = any(ex in name_lower for ex in exclude)
    if skip:
        continue
    try:
        r = requests.get(
            url, timeout=8, headers={"User-Agent": "Mozilla/5.0"}, stream=True
        )
        ct = r.headers.get("Content-Type", "")
        chunk = next(r.iter_content(512), b"")
        head = chunk.decode("utf-8", errors="ignore")[:300]
        is_hls = (
            "#EXTM3U" in head.upper()
            or "#EXT" in head.upper()
            or "mpegurl" in ct.lower()
        )
        ok = r.status_code == 200 and (is_hls or len(chunk) > 0)
        if ok:
            active.append((name, url))
            print(f"  OK   | {name}")
        else:
            print(f"  FAIL | {name} ({r.status_code})")
        r.close()
    except Exception as e:
        print(f"  ERR  | {name}")
    time.sleep(0.1)

print(f"\n{'=' * 60}")
print(f"ACTIVOS: {len(active)}")
print(f"{'=' * 60}")

with open(
    "C:/Users/luiso/iptv-portal/deportes_activos_clean.m3u8", "w", encoding="utf-8"
) as f:
    f.write("#EXTM3U\n")
    for name, url in active:
        f.write(f'#EXTINF:-1 group-title="Deportes",{name}\n')
        f.write(f"{url}\n")

print("Archivo: deportes_activos_clean.m3u8")
