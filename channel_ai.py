import requests
import json
import time

# 源地址
SOURCE_URL = "https://raw.githubusercontent.com/fogret/sourt/master/config/subscribe.txt"

# 强制分类，绝不允许未分类
CATEGORIES = [
    "央视", "卫视", "体育", "电影", "电视剧",
    "少儿", "新闻", "综艺", "音乐", "地方台", "港澳台", "海外"
]

def ai_process(name):
    prompt = f"""
你是专业IPTV频道标准化助手。
处理规则：
1. 清理频道名，去掉4K/HD/超清/测试/乱码/符号
2. 输出标准频道名称
3. 从以下分类中选择**唯一一个**：
{CATEGORIES}
4. 必须分类，**绝对不能出现未分类**
5. 只返回JSON，不要任何多余文字

格式示例：
{{"standard":"CCTV1","category":"央视"}}

频道名：{name}
"""

    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }

    try:
        resp = requests.post(url, json=data, timeout=20)
        res = resp.json()
        content = res["choices"][0]["message"]["content"].strip()
        js = json.loads(content)
        std = js.get("standard", name).strip()
        cate = js.get("category", "地方台")
        if cate not in CATEGORIES:
            cate = "地方台"
        return std, cate
    except:
        return name.strip(), "地方台"  # 兜底，永远不会未分类


def download_source(url):
    print("正在下载订阅文件...")
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_lines(text):
    channels = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "," in line:
            name_part, uri = line.rsplit(",", 1)
            uri = uri.strip()
            if uri.startswith("http"):
                channels.append((name_part, uri))
    return channels


def main():
    text = download_source(SOURCE_URL)
    channels = parse_lines(text)

    groups = {cat: [] for cat in CATEGORIES}
    used_uri = set()

    for name_part, uri in channels:
        if uri in used_uri:
            continue
        used_uri.add(uri)

        print(f"AI处理: {name_part}")
        std_name, cate = ai_process(name_part)
        groups[cate].append((std_name, uri))
        time.sleep(1)

    # 输出 txt
    with open("channels_output.txt", "w", encoding="utf-8") as f:
        for cate in CATEGORIES:
            lst = groups[cate]
            if not lst:
                continue
            f.write(f"# {cate}\n")
            for n, u in lst:
                f.write(f"{n},{u}\n")
            f.write("\n")

    # 输出 m3u
    with open("channels_output.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for cate in CATEGORIES:
            for n, u in groups[cate]:
                f.write(f"#EXTINF:-1,[{cate}]{n}\n{u}\n")

    print("全部完成，无未分类频道")


if __name__ == "__main__":
    main()
