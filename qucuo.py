import os
import re
import requests

data_file = "data.txt"
out_file = "live.txt"

def download_text(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.text
    except:
        return ""
    return ""

def parse_m3u_or_txt(text):
    result = []
    lines = text.splitlines()
    current_name = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            m = re.search(r",(.+)", line)
            if m:
                current_name = m.group(1).strip()
        elif line.startswith("http://") or line.startswith("https://"):
            url = line
            name = current_name
            if not name:
                # 没有 #EXTINF 的情况，用 URL 生成一个名字兜底
                name = url.split("/")[-1]
                name = re.sub(r"\.m3u8.*", "", name)
                name = re.sub(r"\.m3u.*", "", name)
                name = re.sub(r"\.txt.*", "", name)
                name = re.sub(r"[^0-9A-Za-z\u4e00-\u9fa5_\-]+", "", name)
                if not name:
                    name = "频道"
            result.append((name, url))
            current_name = None
    return result

if not os.path.exists(data_file):
    print("data.txt 不存在")
    exit()

# data.txt 里是“源文件 URL 列表”
with open(data_file, "r", encoding="utf-8") as f:
    source_urls = [i.strip() for i in f if i.strip() and not i.startswith("#EXTINF")]

all_pairs = []

print("开始下载并解析源文件...")

for src in source_urls:
    text = download_text(src)
    if not text:
        continue
    pairs = parse_m3u_or_txt(text)
    all_pairs.extend(pairs)

total = len(all_pairs)

# 按“播放地址 URL”去重，保留第一次出现的频道名
unique = {}
for name, url in all_pairs:
    if url not in unique:
        unique[url] = name

with open(out_file, "w", encoding="utf-8") as f:
    for url, name in unique.items():
        f.write(f"#EXTINF:-1,{name}\n{url}\n")

print(f"解析到的总频道数: {total}")
print(f"去重后播放地址数: {len(unique)}")
