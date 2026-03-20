import requests
import re

OUTPUT = "live.txt"
SEARCH_URL = "https://tonkiang.us/api/search"

# 关键词：央视、卫视、贵州、电影
KEYWORDS = [
    "CCTV",
    "卫视",
    "贵州",
    "电影"
]

# 只保留 m3u8
PATTERN = re.compile(r'(https?://[^\s"\'<>]+?\.m3u8)', re.I)

# 排除全国地方台（市县频道）
EXCLUDE_LOCAL = [
    "新闻综合", "都市", "公共", "生活", "科教", "影视", "文体",
    "经济", "民生", "都市频道", "综合频道", "频道", "教育",
    "少儿", "法治", "交通", "娱乐", "资讯"
]

# 贵州例外（不能排除）
GUIZHOU_ALLOW = ["贵州", "贵阳", "遵义", "六盘水", "安顺", "毕节", "铜仁", "黔"]


def is_local_channel(name):
    """判断是否为全国地方台（排除贵州）"""
    if any(k in name for k in GUIZHOU_ALLOW):
        return False
    return any(k in name for k in EXCLUDE_LOCAL)


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
    all_urls = set()

    print("开始抓取 tonkiang.us ...")

    for kw in KEYWORDS:
        print(f"→ 抓取关键词：{kw}")
        html = fetch(kw)
        urls = extract(html)

        for url in urls:
            # 从 URL 推断频道名（简单处理）
            name = url.lower()

            # 排除全国地方台
            if is_local_channel(name):
                continue

            all_urls.add(url)

        print(f"  有效源：{len(all_urls)}")

    # 输出
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for u in sorted(all_urls):
            f.write(u + "\n")

    print(f"\n抓取完成，共 {len(all_urls)} 条源")
    print(f"已输出到：{OUTPUT}")


if __name__ == "__main__":
    main()
