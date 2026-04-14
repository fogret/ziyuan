import os
from urllib.parse import urlparse

data_file = "data.txt"
out_file = "live.txt"

def extract_name(url):
    path = urlparse(url).path
    name = os.path.basename(path)
    if not name:
        name = urlparse(url).netloc
    return name[:40]

if not os.path.exists(data_file):
    print("data.txt 不存在")
    exit()

with open(data_file, "r", encoding="utf-8") as f:
    urls = [i.strip() for i in f if i.strip()]

total = len(urls)

unique = {}
for url in urls:
    domain = urlparse(url).netloc
    if domain not in unique:
        unique[domain] = url

with open(out_file, "w", encoding="utf-8") as f:
    for domain, url in unique.items():
        name = extract_name(url)
        f.write(f"#EXTINF:-1,{name}\n{url}\n")

print(f"总频道数: {total}")
print(f"域名去重后: {len(unique)}")
