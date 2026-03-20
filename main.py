import os
import time
import requests

# ============================
#  CDN 列表（自动测速）
# ============================

CDN_DIANTONG = [
    "http://39.134.24.162",
    "http://39.134.24.161",
    "http://39.134.24.166",
    "http://39.134.24.165",
    "http://39.134.24.160"
]

CDN_CTC = [
    "http://111.20.105.60",
    "http://111.20.105.61",
    "http://111.20.105.62",
    "http://111.20.105.63"
]

CDN_GUIZHOU = [
    "http://183.62.140.14",
    "http://183.62.140.15",
    "http://183.62.140.16"
]

CDN_OTT = [
    "http://ott.mobaibox.com",
    "http://live.cooltv.top",
    "http://tv.iptvcloud.top"
]

# ============================
#  测速函数
# ============================

def test_speed(url):
    try:
        start = time.time()
        r = requests.get(url, timeout=1)
        if r.status_code == 200:
            return time.time() - start
    except:
        return 999
    return 999

def pick_fastest(cdns):
    best = None
    best_time = 999
    for cdn in cdns:
        t = test_speed(cdn)
        if t < best_time:
            best_time = t
            best = cdn
    return best

# ============================
#  读取 shuju.txt
# ============================

def load_sources():
    if not os.path.exists("shuju.txt"):
        print("❌ 未找到 shuju.txt")
        exit()

    with open("shuju.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    sources = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "," not in line:
            continue
        name, url = line.split(",", 1)
        sources.append((name, url))
    return sources

# ============================
#  替换占位符
# ============================

def replace_placeholders(sources, dcdn, ctc, gzdn, ott):
    result = []
    for name, url in sources:
        url = url.replace("[电信CDN]", dcdn)
        url = url.replace("[CTC]", ctc)
        url = url.replace("[贵州电信]", gzdn)
        url = url.replace("[OTT]", ott)
        result.append((name, url))
    return result

# ============================
#  输出 m3u
# ============================

def save_m3u(sources):
    with open("tvbox.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for name, url in sources:
            f.write(f"#EXTINF:-1,{name}\n{url}\n")
    print("✅ 已生成 tvbox.m3u")

# ============================
#  主流程
# ============================

def main():
    print("⏳ 正在测速电信 CDN...")
    dcdn = pick_fastest(CDN_DIANTONG)

    print("⏳ 正在测速全国电信 CTC CDN...")
    ctc = pick_fastest(CDN_CTC)

    print("⏳ 正在测速贵州电信 CDN...")
    gzdn = pick_fastest(CDN_GUIZHOU)

    print("⏳ 正在测速 OTT CDN...")
    ott = pick_fastest(CDN_OTT)

    print("\n⭐ 最终选择的最快 CDN：")
    print("电信 IPTV =", dcdn)
    print("全国 CTC =", ctc)
    print("贵州电信 =", gzdn)
    print("OTT =", ott)

    print("\n⏳ 正在读取 shuju.txt...")
    sources = load_sources()

    print("⏳ 正在替换占位符...")
    final_sources = replace_placeholders(sources, dcdn, ctc, gzdn, ott)

    print("⏳ 正在生成 m3u...")
    save_m3u(final_sources)

    print("\n🎉 完成！你的 IPTV 列表已经准备好。")

if __name__ == "__main__":
    main()
