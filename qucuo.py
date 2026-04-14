import os
import re
import requests

data_file = "data.txt"
out_file = "live.txt"

def download_text(url):
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            return r.text
    except:
        return ""
    return ""

def parse_streams(text):
    urls = []
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if line.startswith("http://") or line.startswith("https://"):
            urls.append(line)
    return urls

def extract_name(url):
    name = url.split("/")[-1]
    name = re.sub(r"\.m3u8.*", "", name)
    name = re.sub(r"\.m3u.*", "", name)
    name = re.sub(r"\.txt.*", "", name)
    name = re.sub(r"[^0-9A-Za-z\u4e00-\u9fa5_\-]+", "", name)
    return name[:40] if name else "频道"

if not os.path.exists(data_file):
    print("data.txt 不存在")
    exit()

# 读取源文件 URL 列表
with open(data_file, "r", encoding="utf-8") as f:
    source_urls = [i.strip() for i in f if i.strip() and not i.startswith("#EXTINF")]

all_streams = []

print("开始下载并解析源文件...")

# 下载并解析每个源文件
for src in source_urls:
    text = download_text(src)
    if text:
        streams = parse_streams(text)
        all_streams.extend(streams)

total = len(all_streams)

# 播放地址去重（完全相同的 URL）
unique_streams = list(dict.fromkeys(all_streams))

# 写入 live.txt
with open(out_file, "w", encoding="utf-8") as f:
    for url in unique_streams:
        name = extract_name(url)
        f.write(f"#EXTINF:-1,{name}\n{url}\n")

print(f"解析到的总播放地址: {total}")
print(f"去重后播放地址: {len(unique_streams)}")
