import os
from urllib.parse import urlparse
import re

data_file = "data.txt"
out_file = "live.txt"

def extract_name(url):
    # 提取文件名作为频道名
    path = urlparse(url).path
    name = os.path.basename(path)
    name = re.sub(r"\.m3u8.*", "", name)
    name = re.sub(r"\.txt.*", "", name)
    name = re.sub(r"[^0-9A-Za-z\u4e00-\u9fa5_\-]+", "", name)
    if not name:
        name = urlparse(url).netloc
    return name[:40]

if not os.path.exists(data_file):
    print("data.txt 不存在")
    exit()

# 读取所有 URL
with open(data_file, "r", encoding="utf-8") as f:
    urls = [i.strip() for i in f if i.strip() and not i.startswith("#EXTINF")]

total = len(urls)

# 按播放地址去重（完整 URL）
unique_urls = list(dict.fromkeys(urls))

# 写入 live.txt
with open(out_file, "w", encoding="utf-8") as f:
    for url in unique_urls:
        name = extract_name(url)
        f.write(f"#EXTINF:-1,{name}\n{url}\n")

print(f"总频道数: {total}")
print(f"去重后播放地址数: {len(unique_urls)}")
