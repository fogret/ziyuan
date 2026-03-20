import requests
import re

OUTPUT = "live"

# 国内可抓取、可播放、可在 GitHub Actions 运行的 API
SOURCE_URLS = [
    "https://live.fanmingming.com/tv/m3u/global.m3u",
    "https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u"
]

# 提取 m3u8 的正则
PATTERN = re.compile(r'(https?://[^\s"\'<>]+?\.m3u8)', re.I)

# CCTV 识别
CCTV = re.compile(r'cctv(\d+)', re.I)

# 贵州地名映射
GUIZHOU_MAP = {
    "guiyang": "贵阳",
    "zunyi": "遵义",
    "liupanshui": "六盘水",
    "anshun": "安顺",
    "bijie": "毕节",
    "tongren": "铜仁",
    "kaili": "凯里",
    "qiandongnan": "黔东南",
    "duyun": "都匀",
    "qiannan": "黔南",
    "xingyi": "兴义",
    "qianxinan": "黔西南",
    "guizhou": "贵州"
}

GUIZHOU_KEYS = list(GUIZHOU_MAP.values())

# 影视频道关键词
MOVIE_KEYS = ["电影", "影视", "影迷", "影", "movie", "film"]

# 音乐频道关键词
MUSIC_KEYS = ["音乐", "mtv", "音悦", "music", "kpop", "hits"]


def clean_name(name):
    name = name.lower()
    for bad in ["_hd", "_sd", "_4k", "_1080p", "_720p", "-hd", "-sd", "-4k"]:
        name = name.replace(bad, "")
    for bad in ["live", "stream", "tv"]:
        name = name.replace(bad, "")
    for s in ["_", "-", "."]:
        name = name.replace(s, "")
    return name


def to_chinese(name):
    for en, zh in GUIZHOU_MAP.items():
        if en in name:
            return zh + name.replace(en, "")
    return name


def classify(name):
    # CCTV
    m = CCTV.search(name)
    if m:
        num = m.group(1)
        return f"CCTV{num}", "央视频道"

    # 贵州频道
    if any(k in name for k in GUIZHOU_KEYS) or any(en in name for en in GUIZHOU_MAP.keys()):
        return to_chinese(name), "贵州频道"

    # 卫视
    if "卫视" in name:
        return name, "卫视频道"

    # 影视频道
    if any(k in name for k in MOVIE_KEYS):
        return name, "影视频道"

    # 音乐频道
    if any(k in name for k in MUSIC_KEYS):
        return name, "音乐频道"

    return None, None  # 不要地方台


def fetch(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.text
    except:
        return ""


def extract(text):
    return PATTERN.findall(text)


def test_url(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.head(url, headers=headers, timeout=3)
        return resp.status_code == 200
    except:
        return False


def main():
    print("开始：精准抓取 + 测速 + 过滤坏源 + 分类 + 排序 + 输出 live ...")

    items = []
    seen = set()

    # 抓取
    for src in SOURCE_URLS:
        print(f"→ 抓取：{src}")
        text = fetch(src)
        urls = extract(text)

        for url in urls:
            if url in seen:
                continue
            seen.add(url)

            raw = url.lower().split("/")[-1].replace(".m3u8", "")
            name = clean_name(raw)

            title, group = classify(name)
            if title is None:
                continue  # 不要地方台

            items.append((title, group, url))

    print(f"抓取完成，共 {len(items)} 条，开始测速...")

    # 测速
    good = []
    for title, group, url in items:
        if test_url(url):
            good.append((title, group, url))

    print(f"测速完成，可用源：{len(good)} 条")

    # 排序
    order = {
        "央视频道": 1,
        "卫视频道": 2,
        "贵州频道": 3,
        "影视频道": 4,
        "音乐频道": 5
    }

    good.sort(key=lambda x: (order[x[1]], x[0]))

    # 输出
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for title, group, url in good:
            f.write(f'#EXTINF:-1 tvg-name="{title}" group-title="{group}",{title}\n')
            f.write(url + "\n")

    print(f"\n最终可用频道：{len(good)} 条")
    print(f"已生成：{OUTPUT}")


if __name__ == "__main__":
    main()
