import re
import os
import requests

# 配置
INPUT_PATH = "urls.txt"
OUTPUT_PATH = "zhubo.txt"

# 匹配 http://ip:port/rtp/...
pattern = re.compile(r"http://\d+\.\d+\.\d+\.\d+:\d+/rtp/\d+\.\d+\.\d+\.\d+:\d+", re.I)

seen = set()

# 读取订阅列表
with open(INPUT_PATH, "r", encoding="utf-8", errors="ignore") as f:
    lines = [line.strip() for line in f if line.strip()]

print(f"=== 开始下载并提取 ===")
print(f"订阅源数量：{len(lines)}")

# 逐个下载
for url in lines:
    try:
        print(f"正在下载：{url}")
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        content = resp.text

        # 提取
        links = pattern.findall(content)
        for link in links:
            seen.add(link.strip())
    except Exception as e:
        print(f"下载失败：{url} | {e}")

# 保存
final = sorted(seen)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(final))

print(f"=== 提取完成 ===")
print(f"共提取有效 RTP 源：{len(final)} 条")
print(f"已保存到：{OUTPUT_PATH}")
