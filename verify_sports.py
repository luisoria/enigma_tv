#!/usr/bin/env python3
import requests
import time

sports_channels = [
    (
        "Abu Dhabi Sports 1",
        "https://vo-live.cdb.cdn.orange.com/Content/Channel/AbuDhabiSportsChannel1/HLS/index.m3u8",
    ),
    (
        "Abu Dhabi Sports 2",
        "https://vo-live.cdb.cdn.orange.com/Content/Channel/AbuDhabiSportsChannel2/HLS/index.m3u8",
    ),
    (
        "ACI Sport TV",
        "https://g4wlk6xpy23a-hls-live.mariatvcdn.it/acisporttv/b7a3464f8e2001314de9fefebf11229d.sdp/playlist.m3u8",
    ),
    (
        "Afizzionados",
        "https://linear-348.frequency.stream/mt/studio/348/hls/master/playlist.m3u8",
    ),
    ("All Sports", "https://5cf4a2c2512a2.streamlock.net/dgrau/dgrau/playlist.m3u8"),
    ("AntenaSport", "https://stream1.antenaplay.ro/as/asrolive1/playlist.m3u8"),
    ("ASpor", "https://ythls.armelin.one/channel/UCJElRTCNEmLemgirqvsW63Q.m3u8"),
    (
        "Awapa Sports TV",
        "https://mgv-awapa.akamaized.net/hls/live/2104282/MGV_CHANNEL15/master.m3u8",
    ),
    ("B1B Box", "https://e105-ts.cdn.bg/b1b/fls/b1btv.stream/playlist.m3u8"),
    (
        "Belarus 5",
        "https://ngtrk.dc.beltelecom.by/ngtrk/smil:belarus5.smil/playlist.m3u8",
    ),
    (
        "BEK TV Sports West",
        "https://cdn3.wowza.com/5/ZWQ1K2NYTmpFbGsr/BEK-WOWZA-1/smil:BEKPRIMEW.smil/playlist.m3u8",
    ),
    (
        "CBS Sports Golazo",
        "https://dai.google.com/linear/hls/event/GxrCGmwST0ixsrc_QgB6qw/master.m3u8",
    ),
    ("CBS Sports Network", "http://fl2.moveonjoy.com/CBS_SPORTS_NETWORK/index.m3u8"),
    (
        "CnAr Deportes",
        "https://stmv1.cnarlatam.com/cnardeportes2/cnardeportes2/playlist.m3u8",
    ),
    ("CRTV", "https://vdo.panelstreaming.live:3058/stream/play.m3u8"),
    ("CT Sport", "http://88.212.15.27/live/test_ctsport_25p/playlist.m3u8"),
    (
        "D13",
        "https://jireh-2-hls-video-us-isp.dps.live/hls-video/ey6283je82983je9823je8jowowiekldk9838274/13d/13d.smil/playlist.m3u8",
    ),
    (
        "DF1",
        "https://dbjwcot8t7nyd.cloudfront.net/out/v1/9d068a9428444b458324ad77b5a0a4b8/index.m3u8",
    ),
    ("EDGEsport", "https://edgesport-samsunguk.amagi.tv/playlist.m3u8"),
    (
        "ERT Sports 1",
        "http://cbd537474fbad4634b64787657ff6456.msvdn.net/sports1/ert_sports1_main/mainabr/playlist.m3u8",
    ),
    (
        "ERT Sports 2",
        "http://cbd537474fbad4634b64787657ff6456.msvdn.net/sports2/ert_sports2_main/mainabr/playlist.m3u8",
    ),
    (
        "Fan Duel TV",
        "https://d2jl8r92tdc3f1.cloudfront.net/out/v1/59419700344b4625b7cb0693ba265ea3/TVGindex_5.m3u8",
    ),
    ("Fox Sports (ES)", "https://lnc-fox-sports-espanol2.tubi.video/index.m3u8"),
    ("Fox Sports (EN)", "https://lnc-fox-sports2.tubi.video/index.m3u8"),
    ("Fox Sports 1", "http://fl2.moveonjoy.com/FOX_Sports_1/index.m3u8"),
    ("Fox Sports 2", "http://fl2.moveonjoy.com/FOX_Sports_2/index.m3u8"),
    ("Fubo Sports", "https://apollo.production-public.tubi.io/live/ac-fubo.m3u8"),
    ("Idman", "https://edge02.odtv.az/o7/idman/playlist.m3u8"),
    ("Insight TV", "https://insighttv-vizio.amagi.tv/playlist.m3u8"),
    (
        "Inter TV",
        "https://open.http.mp.streamamg.com/p/3001560/sp/300156000/playManifest/entryId/0_xmkk2kjr/flavorIds/0_zlbr85f8,0_zlbr85f8,0_noewhew2/format/applehttp/protocol/https/a.m3u8",
    ),
    ("M4 Sport", "http://146.59.85.40:89/m4hd/index.m3u8"),
    ("MadeinBO TV", "https://srvx1.selftv.video/dmchannel/live/playlist.m3u8"),
    ("Mav TV", "https://mavtv-mavtvglobal-1-in.samsung.wurl.tv/playlist.m3u8"),
    ("M-Net Sport", "http://ares.mnet.mk/hls/mnet-sport.m3u8"),
    (
        "MUTV",
        "https://bcovlive-a.akamaihd.net/r2d2c4ca5bf57456fb1d16255c1a535c8/eu-west-1/6058004203001/playlist.m3u8",
    ),
    (
        "NBC Sports",
        "https://xumo-xumoent-vc-122-sjv70.fast.nbcuni.com/live/master.m3u8",
    ),
    ("NTV Spor", "http://46.4.193.238:8484/hls/ntvspor/playlist.m3u8"),
    (
        "Persiana Sport",
        "https://persiana.mastercast.cloud/memfs/f1accec0-3b52-476b-ada9-65f74ead985e.m3u8",
    ),
    (
        "Pluto TV Sports US",
        "http://cfd-v4-service-channel-stitcher-use1-1.prd.pluto.tv/stitch/hls/channel/56340779a738201b4ccfeac9/master.m3u8?appName=web&appVersion=unknown&clientTime=0&deviceDNT=0&deviceId=6c2b3b63-30d3-11ef-9cf5-e9ddff8ff496&deviceMake=Chrome&deviceModel=web&deviceType=web&deviceVersion=unknown&includeExtendedEvents=false&serverSideAds=false&sid=8673a43c-58ba-48b3-8db5-75986abb01b9",
    ),
    (
        "Pluto TV Deportes",
        "https://service-stitcher.clusters.pluto.tv/stitch/hls/channel/5dcde07af1c85b0009b18651/master.m3u8?advertisingId=&appName=web&appVersion=5.14.0&deviceDNT=false&deviceId=6fbead95-26b1-415d-998f-1bdef62d10be&deviceMake=Chrome&deviceModel=web&deviceType=web&deviceVersion=88.0.4324.150&marketingRegion=VE&serverSideAds=false",
    ),
    ("PTV Sports", "http://121.91.61.106:8000/play/a00l/index.m3u8"),
    ("Real Madrid TV", "https://stream.ads.ottera.tv/playlist.m3u8?network_id=1545"),
    (
        "Realitatea Sportiva",
        "https://stream.realitatea.net/realitatea/sportiva_md/playlist.m3u8",
    ),
    (
        "Sport En France",
        "https://sp1564435593.mytvchain.info/live/sp1564435593/index.m3u8",
    ),
    ("Sportitalia", "https://di-g7ij0rwh.vo.lswcdn.net/sportitalia/sihd/playlist.m3u8"),
    (
        "SportsConnect",
        "https://origin3.afxp.telemedia.co.za/PremiumFree/sportsconnect/playlist.m3u8",
    ),
    ("Stadium", "https://apollo.production-public.tubi.io/live/ac-stadium2.m3u8"),
    ("Trace Sports Stars", "https://trace-sportstars-samsungnz.amagi.tv/playlist.m3u8"),
    ("TR Sport", "https://livetr.teleromagna.it/mia/live/playlist.m3u8"),
    (
        "TVQ Sports",
        "https://dacastmmd.mmdlive.lldns.net/dacastmmd/1b6bbade53634f5a847b953c9adfd102/index.m3u8",
    ),
    ("TVR Sport", "https://tvr-tvrsport.cdn.zitec.com/live/tvrsport/main.m3u8"),
    ("Unbeaten", "https://unbeaten-tcl.amagi.tv/playlist.m3u8"),
    ("Vinx TV", "https://tv.radiocast.es:5443/vinxtv/streams/vinxtvlive.m3u8"),
    ("WAPA Deportes", "https://live.field59.com/wapa/wapa2/playlist.m3u8"),
    # Extreme Sports
    ("Extreme Sports", "https://edge02.odtv.az/o4/extremesport/playlist.m3u8"),
    (
        "FUEL TV",
        "https://d35j504z0x2vu2.cloudfront.net/v1/manifest/0bc8e8376bd8417a1b6761138aa41c26c7309312/fuel-tv/606c2f67-acff-4152-975a-e5bfef54eb61/2.m3u8",
    ),
    ("grvty", "https://d37j5jg7ob6kji.cloudfront.net/index.m3u8"),
    (
        "Nitro Circus",
        "https://dai2.xumo.com/amagi_hls_data_xumo1212A-redboxnitrocircus/CDN/playlist.m3u8",
    ),
    (
        "Red Bull TV",
        "https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8",
    ),
    # Fight Sports
    ("Combate Global", "https://stream.ads.ottera.tv/playlist.m3u8?network_id=960"),
    ("FightBox", "http://stream01.vnet.am/Fightbox/mono.m3u8"),
    ("Fight Network", "https://d12a2vxqkkh1bo.cloudfront.net/hls/main.m3u8"),
    (
        "FITE 24/7",
        "https://d3d85c7qkywguj.cloudfront.net/v1/master/9d062541f2ff39b5c0f48b743c6411d25f62fc25/FiteTV-Nuestra/263.m3u8",
    ),
    (
        "Glory Kickboxing",
        "https://dai2.xumo.com/amagi_hls_data_xumo1212A-redboxglorykickboxing/CDN/playlist.m3u8",
    ),
    (
        "Hard Knocks",
        "https://d3uyzhwvmemdyf.cloudfront.net/v1/master/9d062541f2ff39b5c0f48b743c6411d25f62fc25/HardKnocks-SportsTribal/121.m3u8",
    ),
    (
        "IMPACT Wrestling",
        "https://d3mwqwqfak7y2q.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/ImpactWrestling-prod/hls/main.m3u8",
    ),
    ("TVS Boxing", "https://bozztv.com/gusa/gusa-tvsboxing/index.m3u8"),
    ("WLN Wrestling", "https://hls.airy.tv/stream/14/airy.m3u8"),
    # Baseball
    ("MLB Network", "http://fl2.moveonjoy.com/MLB_NETWORK/index.m3u8"),
    # Basketball
    ("NBA TV", "http://fl2.moveonjoy.com/NBA_TV/index.m3u8"),
    # Ice Hockey
    ("NHL Network", "https://fl2.moveonjoy.com/NHL_NETWORK/index.m3u8"),
    # Motor Sports
    ("MAVTV Select", "https://mavtv-mavtvglobal-1-eu.rakuten.wurl.tv/playlist.m3u8"),
    ("NHRA TV", "https://apollo.production-public.tubi.io/live/ac-nhra.m3u8"),
    ("Racing America", "https://lnc-racing-america.tubi.video/playlist.m3u8"),
    # Women's Sports
    (
        "Women Sports Network",
        "https://lnc-fast-studios-womens-sports.tubi.video/playlist.m3u8",
    ),
    # Poker/Gambling
    ("Players TV", "https://playerstv-roku-us.amagi.tv/playlist.m3u8"),
]

print(f"Total canales deportivos a verificar: {len(sports_channels)}")
print("=" * 60)
print("VERIFICANDO CANALES DEPORTIVOS...")
print("=" * 60)

active = []
for name, url in sports_channels:
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
print(f"CANALES ACTIVOS: {len(active)}/{len(sports_channels)}")
print(f"{'=' * 60}")

with open(
    "C:/Users/luiso/iptv-portal/deportes_activos_global.m3u8", "w", encoding="utf-8"
) as f:
    f.write("#EXTM3U\n")
    for name, url in active:
        f.write(f'#EXTINF:-1 group-title="Deportes",{name}\n')
        f.write(f"{url}\n")

print(f"Archivo generado: deportes_activos_global.m3u8")
