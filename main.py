import requests
import re

OUTPUT = "live"
SEARCH_URL = "https://tonkiang.us/api/search"

KEYWORDS = ["CCTV", "卫视", "贵州", "电影"]

PATTERN = re.compile(r'(https?://[^\s"\'<>]+?\.m3u8)', re.I)

CCTV = re.compile(r'cctv(\d+)', re.I)

GUIZHOU_KEYS = [
    "贵州", "贵阳", "遵义", "六盘水", "安顺", "毕节", "铜仁",
    "凯里", "黔东南", "都匀", "黔南", "兴义", "黔西南"
]

MOVIE_KEYS = ["电影", "movie", "film", "影"]


def clean_name(name):
    """洗名：去垃圾后缀、符号、格式化"""
    name = name.lower()

    # 去掉后缀
    for bad in ["_hd", "_sd", "_4k", "_1080p", "_720p", "-hd", "-sd", "-4k"]:
        name = name.replace(bad, "")

    # 去掉无意义词
    for bad in ["live", "stream", "tv"]:
        name = name.replace(bad, "")

    # 去掉符号
    for s in ["_", "-", "."]:
        name = name.replace(s, "")

    return name


def classify(name):
    """分类为：央视频道、贵州频道、数字频道、电影频道"""

    # 央视频道
    m = CCTV.search(name)
    if m:
        num = m.group(1)
        return f"CCTV{num}", "央视频道"

    # 贵州频道
    if any(k in name for k in GUIZHOU_KEYS):
        return name, "贵州频道"

    # 电影频道
    if any(k in name for k in MOVIE_KEYS):
        return name, "电影频道"

    # 数字频道（兜底）
    return name, "数字频道"


def fetch(keyword):
    try:
        resp = requests.get(SEARCH_URL, params={"keyword": keyword}, timeout=10)
        resp.raise_for_status()
        return resp.text
    except:
        return ""


def extract(text):
    return PATTERN.findall(text)


def main():
    print("开始：抓取 + 洗名 + 分类 + 排序 + 输出 live ...")

    items = []

    for kw in KEYWORDS:
        print(f"→ 搜索：{kw}")
        html = fetch(kw)
        urls = extract(html)

        for url in urls:
            raw = url.lower().split("/")[-1].replace(".m3u8", "")
            name = clean_name(raw)

            title, group = classify(name)
            items.append((title, group, url))

    # 排序：按分类顺序 → 分类内按频道名
    order = {
        "央视频道": 1,
        "贵州频道": 2,
        "电影频道": 3,
        "数字频道": 4
    }

    items.sort(key=lambda x: (order[x[1]], x[0]))

    # 输出
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for title, group, url in items:
            f.write(f'#EXTINF:-1 tvg-name="{title}" group-title="{group}",{title}\n')
            f.write(url + "\n")

    print(f"\n完成，共 {len(items)} 条频道")
    print(f"已生成：{OUTPUT}")


if __name__ == "__main__":
    main()
