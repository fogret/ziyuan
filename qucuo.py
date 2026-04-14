import re
import os

data_file = "data.txt"
out_file = "live.txt"

def extract_name(url):
    url = url.strip()
    if "#EXTINF" in url:
        m = re.search(r",(.+)", url)
        if m:
            return m.group(1).strip()
    name = re.sub(r"https?://", "", url)
    name = name.split("?")[0]
    name = name.split("/")[-1]
    name = re.sub(r"\.m3u8.*", "", name)
    name = re.sub(r"[^0-9A-Za-z\u4e00-\u9fa5]+", "", name)
    if len(name) == 0:
        name = "未知频道"
    return name[:20]

if not os.path.exists(data_file):
    print("data.txt 不存在")
    exit()

with open(data_file, "r", encoding="utf-8") as f:
    lines = [i.strip() for i in f if i.strip()]

total = len(lines)

parsed = []
for line in lines:
    if line.startswith("#EXTINF"):
        continue
    name = extract_name(line)
    parsed.append((name, line))

unique = {}
for name, url in parsed:
    if name not in unique:
        unique[name] = url

with open(out_file, "w", encoding="utf-8") as f:
    for name, url in unique.items():
        f.write(f"#EXTINF:-1,{name}\n{url}\n")

print(f"总频道数: {total}")
print(f"去重后: {len(unique)}")
