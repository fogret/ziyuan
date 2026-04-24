import re
import os
import requests

# 配置
INPUT_PATH = "urls.txt"
OUTPUT_PATH = "zhubo.txt"

# 匹配规则
pattern = re.compile(r"http[s]?://\d+\.\d+\.\d+\.\d+:\d+/rtp/\S+", re.I)

all_links = set()

# 读取订阅地址
try:
    with open(INPUT_PATH, "r", encoding="utf-8", errors="ignore") as f:
        urls = [line.strip() for line in f if line.strip()]
except:
    urls = []

print(f"订阅源数量：{len(urls)}")

# 遍历下载
for u in urls:
    try:
        print(f"下载：{u}")
        r = requests.get(u, timeout=15)
        r.encoding = "utf-8"
        content = r.text

        # 提取
        links = pattern.findall(content)
        for l in links:
            ll = l.strip()
            if ll:
                all_links.add(ll)
    except Exception as e:
        print(f"失败：{u} => {e}")

# 去重 + 排序
final = sorted(all_links)

# 写入根目录
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(final))

print(f"提取完成：{len(final)} 条")
print(f"已生成：{OUTPUT_PATH}")
