import os
import time
import requests

CDN_DIANTONG = [
    "39.134.24.162",
    "39.134.24.161",
    "39.134.24.166",
    "39.134.24.165",
    "39.134.24.160"
]

CDN_CTC = [
    "111.20.105.60",
    "111.20.105.61",
    "111.20.105.62",
    "111.20.105.63"
]

CDN_GUIZHOU = [
    "183.62.140.14",
    "183.62.140.15",
    "183.62.140.16"
]

CDN_OTT = [
    "ott.mobaibox.com",
    "live.cooltv.top",
    "tv.iptvcloud.top"
]

def in_github_actions():
    return "GITHUB_ACTIONS" in os.environ

def test_speed(url):
    try:
        start = time.time()
        r = requests.get("http://" + url, timeout=1)
        if r.status_code == 200:
            return time.time() - start
    except:
        return 999
    return 999

def pick_fastest(cdns):
    best = cdns[0]
    best_time = 999
    for cdn in cdns:
        t = test_speed(cdn)
        if t < best_time:
            best_time = t
            best = cdn
    return best

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

# ⭐⭐ 核心修复：正确拼接 IPTV URL ⭐⭐
def fix_url(url, dcdn, ctc, gzdn, ott):

    # 去掉所有 http://
    url = url.replace("http://", "")

    # 替换占位符
    url = url.replace("[电信CDN]", dcdn)
    url = url.replace("[CTC]", ctc)
    url = url.replace("[贵州电信]", gzdn)
    url = url.replace("[OTT]", ott)

    # IPTV 源（含 PLTV）
    if "PLTV" in url:
        # 正确格式： http://IP:6610/PLTV/.../index.m3u8?IASHttpSessionId=OTT
        return f"http://{url.split('/')[0]}:6610/" + "/".join(url.split('/')[1:]) + "?IASHttpSessionId=OTT"

    # OTT 源
    return f"http://{url}"

def replace_placeholders(sources, dcdn, ctc, gzdn, ott):
    result = []
    for name, url in sources:
        fixed = fix_url(url, dcdn, ctc, gzdn, ott)
        result.append((name, fixed))
    return result

def save_m3u(sources):
    with open("tvbox.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for name, url in sources:
            f.write(f"#EXTINF:-1,{name}\n{url}\n")
    print("✅ 已生成 tvbox.m3u")

def main():

    if in_github_actions():
        print("⚠️ GitHub Actions 环境 → 使用默认 CDN")
        dcdn = CDN_DIANTONG[0]
        ctc = CDN_CTC[0]
        gzdn = CDN_GUIZHOU[0]
        ott = CDN_OTT[0]
    else:
        dcdn = pick_fastest(CDN_DIANTONG)
        ctc = pick_fastest(CDN_CTC)
        gzdn = pick_fastest(CDN_GUIZHOU)
        ott = pick_fastest(CDN_OTT)

    print("\n⭐ 使用 CDN：")
    print("电信 =", dcdn)
    print("CTC =", ctc)
    print("贵州 =", gzdn)
    print("OTT =", ott)

    sources = load_sources()
    final_sources = replace_placeholders(sources, dcdn, ctc, gzdn, ott)
    save_m3u(final_sources)

if __name__ == "__main__":
    main()
