import requests
import re

OUTPUT = "live"
SEARCH_URL = "https://tonkiang.us/api/search"

KEYWORDS = ["CCTV", "卫视", "贵州", "电影"]

PATTERN = re.compile(r'(https?://[^\s"\'<>]+?\.m3u8)', re.I)

CCTV = re.compile(r'cctv(\d+)', re.I)

# 贵州地名映射（用于中文化）
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

GUIZHOU_KEYS = list(GUIZHOU_MAP.values())  # 中文关键词

MOVIE_KEYS = ["电影", "movie", "film", "影"]


def clean_name(name):
    """洗名：去垃圾后缀、符号、格式化"""
    name = name.lower()

    for bad in ["_hd", "_sd", "_4k", "_1080p", "_720p", "-hd", "-sd", "-4k"]:
        name = name.replace(bad, "")

    for bad in ["live", "stream", "tv"]:
        name = name.replace(bad, "")

    for s in ["_", "-", "."]:
        name = name.replace(s, "")

    return name


def to_chinese(name):
    """将英文地名转为中文（如果能识别）"""
    for en, zh in GUIZHOU_MAP.items():
        if en in name:
            return zh + name.replace(en, "")
    return name


def classify(name):
    """分类为：央视频道、贵州频道、数字频道、电影频道"""

    # 央视频道
    m = CCTV.search(name)
    if m:
        num = m.group(1)
        return f"CCTV{num}", "央视频道"

    # 贵州频道（中文或英文）
    if any(k in name for k in GUIZHOU_KEYS) or any(en in name for en in GUIZHOU_MAP.keys()):
        return to_chinese(name), "贵州频道"

    # 电影频道
    if any(k in name for k in MOVIE_KEYS):
        return name, "电影频道"

    # 数字频道（兜底）
    return name, "数字频道"


def fetch(keyword):
    """加入 UA 修复抓取失败问题"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        resp = requests.get(
            SEARCH_URL,
            params={"keyword": keyword},
            headers=headers,
            timeout=10
        )
        resp.raise_for_status()
        return resp.text
    except:
        return ""


def extract(text):
    return PATTERN.findall(text)


def main():
    print("开始：抓取 + 洗名 + 中文化 + 分类 + 去重 + 排序 + 输出 live ...")

    items = []
    seen = set()

    for kw in KEYWORDS:
        print(f"→ 搜索：{kw}")
        html = fetch(kw)
        urls = extract(html)

        for url in urls:
            if url in seen:
                continue
            seen.add(url)

            raw = url.lower().split("/")[-1].replace(".m3u8", "")
            name = clean_name(raw)

            title, group = classify(name)
            items.append((title, group, url))

    # 排序规则
    order = {
        "央视频道": 1,
        "贵州频道": 2,
        "电影频道": 3,
        "数字频道": 4
    }

    # 贵州内部排序
    guizhou_order = {
        "贵阳": 1, "遵义": 2, "六盘水": 3, "安顺": 4,
        "毕节": 5, "铜仁": 6, "凯里": 7, "黔东南": 8,
        "都匀": 9, "黔南": 10, "兴义": 11, "黔西南": 12
    }

    def sort_key(item):
        title, group, _ = item
        if group == "贵州频道":
            for k in guizhou_order:
                if k in title:
                    return (order[group], guizhou_order[k], title)
        return (order[group], title)

    items.sort(key=sort_key)

    # 输出
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for title, group, url in items:
            f.write(f'#EXTINF:-1 tvg-name="{title}" group-title="{group}",{title}\n')
            f.write(url + "\n")

    print(f"\n完成，共 {} 条频道".format(len(items)))
    print(f"已生成：{OUTPUT}")


if __name__ == "__main__":
    main()
