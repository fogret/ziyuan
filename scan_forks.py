import requests
import json
import time

# 源地址
SOURCE_URL = "https://raw.githubusercontent.com/fogret/sourt/master/config/subscribe.txt"

# 强制分类（AI必须选一个，不允许未分类）
CATEGORIES = [
    "央视", "卫视", "体育", "电影", "电视剧",
    "少儿", "新闻", "综艺", "音乐", "地方台", "港澳台", "海外"
]

# 免费AI接口（无需KEY，可直接跑）
def ai_standardize_and_classify(name):
    prompt = f"""
请处理这个IPTV频道名：
1. 清洗干净，去掉4K/HD/测试/乱码/符号
2. 输出标准频道名
3. 从以下分类选**唯一一类**：{CATEGORIES}
4. 必须分类，**禁止未分类**
5. 只返回JSON，不要其他内容

格式：
{{"name":"标准名称", "type":"分类"}}

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
        txt = res["choices"][0]["message"]["content"].strip()
        js = json.loads(txt)
        cat = js.get("type", "地方台")
        if cat not in CATEGORIES:
            cat = "地方台"
        return js.get("name", name), cat
    except:
        return name, "地方台"  # 兜底，永远不会未分类


def main():
    print("拉取源...")
    r = requests.get(SOURCE_URL, timeout=20)
    lines = r.text.splitlines()

    groups = {c: [] for c in CATEGORIES}
    used = set()

    for line in lines:
        line = line.strip()
        if not line or "," not in line:
            continue
        part1, uri = line.rsplit(",", 1)
        uri = uri.strip()
        if uri in used:
            continue
        used.add(uri)

        print(f"AI处理: {part1}")
        std_name, cat = ai_standardize_and_classify(part1)
        groups[cat].append((std_name, uri))
        time.sleep(1.2)

    # 输出txt
    with open("channels_output.txt", "w", encoding="utf-8") as f:
        for cat in CATEGORIES:
            items = groups[cat]
            if not items:
                continue
            f.write(f"# {cat}\n")
            for n, u in items:
                f.write(f"{n},{u}\n")
            f.write("\n")

    # 输出m3u
    with open("channels_output.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for cat in CATEGORIES:
            for n, u in groups[cat]:
                f.write(f"#EXTINF:-1,[{cat}]{n}\n{u}\n")

    print("完成，无任何未分类频道")

if __name__ == "__main__":
    main()
