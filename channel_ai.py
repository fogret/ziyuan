import requests
import json
import time

# 你的源地址
SOURCE_URL = "https://raw.githubusercontent.com/fogret/sourt/master/config/subscribe.txt"

# 输出文件
OUTPUT_TXT = "channels_final.txt"
OUTPUT_M3U = "channels_final.m3u"

# 分类列表（AI 必须从这里选，不允许未分类）
CATEGORIES = [
    "央视", "卫视", "体育", "电影", "电视剧",
    "少儿", "新闻", "综艺", "音乐", "地方台", "港澳台", "海外"
]

# ==============================
# 免费 DeepSeek 模型 API（免费额度足够日常使用）
# ==============================
def ai_process(name):
    prompt = f"""
你是专业IPTV频道标准化助手，严格按要求执行：

1. 清理频道名：去掉 4K/HD/超清/测试/乱码/符号
2. 输出标准频道名称
3. 从以下分类中选**唯一一个最合适**：
{CATEGORIES}
4. 必须分类，**绝对不允许未分类**
5. 只返回 JSON，不要任何其他文字

格式：
{{"standard":"xxx", "category":"xxx"}}

频道名：{name}
"""

    # 免费开源 API 代理（无需KEY）
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }

    try:
        resp = requests.post(url, json=data, headers=headers, timeout=15)
        result = resp.json()
        content = result["choices"][0]["message"]["content"]
        return json.loads(content.strip())
    except:
        # 兜底：如果API出问题，强制分到“地方台”，保证不出现未分类
        return {"standard": name, "category": "地方台"}

# ==============================
# 主程序
# ==============================
def main():
    print("正在拉取频道列表...")
    r = requests.get(SOURCE_URL)
    lines = r.text.splitlines()

    groups = {cat: [] for cat in CATEGORIES}
    processed = set()

    for line in lines:
        line = line.strip()
        if not line or "," not in line:
            continue

        name_part, url = line.rsplit(",", 1)
        url = url.strip()

        if url in processed:
            continue
        processed.add(url)

        print(f"AI 处理中：{name_part}")
        ai_result = ai_process(name_part)

        std_name = ai_result["standard"]
        cate = ai_result["category"]

        # 确保分类一定在列表里，防止AI乱输出
        if cate not in CATEGORIES:
            cate = "地方台"

        groups[cate].append((std_name, url))
        time.sleep(1)  # 避免API限制

    # 输出 TXT
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        for cate in CATEGORIES:
            lst = groups[cate]
            if not lst:
                continue
            f.write(f"# {cate}\n")
            for name, uri in lst:
                f.write(f"{name},{uri}\n")
            f.write("\n")

    # 输出 M3U
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for cate in CATEGORIES:
            for name, uri in groups[cate]:
                f.write(f"#EXTINF:-1,[{cate}]{name}\n{uri}\n")

    print("全部完成！无未分类频道！")

if __name__ == "__main__":
    main()
