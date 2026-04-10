import os
import re
import requests

def log(msg):
    print(msg, flush=True)

extinf_re = re.compile(
    r'#EXTINF:[^\n]*group-title="(?P<group>[^"]*)"[^\n]*,(?P<name>.+)$'
)

def download_m3u(url):
    log(f"下载直播源内容: {url}")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        log(f"下载失败: {e}")
        return ""

def extract_channels(m3u_text):
    categories = {}

    for line in m3u_text.splitlines():
        line = line.strip()
        if not line.startswith("#EXTINF"):
            continue

        m = extinf_re.match(line)
        if not m:
            continue

        group = m.group("group").strip() or "未分类"
        name = m.group("name").strip() or "未命名"

        if group not in categories:
            categories[group] = []
        categories[group].append(name)

    return categories

def build_yings_txt():
    root = os.getcwd()
    data_file = os.path.join(root, "data.txt")

    with open(data_file, 'r', encoding='utf-8') as f:
        url = f.read().strip()

    m3u_text = download_m3u(url)
    categories = extract_channels(m3u_text)

    out_file = os.path.join(root, "yings.txt")
    with open(out_file, 'w', encoding='utf-8') as f:
        for cat, names in categories.items():
            f.write(f"{cat}\n")
            for n in names:
                f.write(f"  {n}\n")
            f.write("\n")

    log("yings.txt 写入完成")

if __name__ == "__main__":
    build_yings_txt()
