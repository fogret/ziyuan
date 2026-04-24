import re
import os

# 配置路径
INPUT_PATH = "urls.txt"
OUTPUT_PATH = "zhubo.txt"

# 精准匹配你要的格式：http://ip:port/rtp/数字组播地址
URL_PATTERN = re.compile(
    r"http://\d+\.\d+\.\d+\.\d+:\d+/rtp/\d+\.\d+\.\d+\.\d+:\d+",
    re.IGNORECASE
)

unique_links = []
seen = set()

# 读取并提取
if os.path.exists(INPUT_PATH):
    with open(INPUT_PATH, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    raw_links = URL_PATTERN.findall(content)

    # 去重
    for link in raw_links:
        link = link.strip()
        if link and link not in seen:
            seen.add(link)
            unique_links.append(link)

# 写入结果
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(unique_links))

print(f"提取完成！")
print(f"共提取 {len(unique_links)} 条符合格式的 rtp 源")
print(f"已保存到 {OUTPUT_PATH}")
