import os
import re
import requests

def log(msg):
    print(msg, flush=True)

def wlen(s):
    return sum(2 if ord(c) > 127 else 1 for c in s)

def download_m3u(url):
    log(f"[1/5] 下载直播源内容: {url}")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        log("[2/5] 下载完成，开始解析")
        return resp.text.lstrip("\ufeff")
    except Exception as e:
        log(f"下载失败: {e}")
        return ""

extinf_re = re.compile(
    r'#EXTINF:[^\n]*?(?:group-title="?([^",]*)"?)[^\n]*?,\s*(.*)$'
)

name_re = re.compile(r'tvg-name="([^"]+)"')

def parse_extinf(line):
    m = extinf_re.search(line)
    if m:
        group = m.group(1).strip() if m.group(1) else "未分类"
        name = m.group(2).strip()
        if name.startswith("http"):
            nm = name_re.search(line)
            if nm:
                name = nm.group(1).strip()
        return group, name
    nm = name_re.search(line)
    if nm:
        return "未分类", nm.group(1).strip()
    if "," in line:
        return "未分类", line.split(",", 1)[1].strip()
    return None, None

def extract_channels(m3u_text):
    categories = {}
    count = 0
    for line in m3u_text.splitlines():
        line = line.strip()
        if not line.startswith("#EXTINF"):
            continue
        group, name = parse_extinf(line)
        if not name:
            continue
        categories.setdefault(group, []).append(name)
        count += 1
        if count % 100 == 0:
            log(f"解析进度：已处理 {count} 条频道")
    log(f"[3/5] 解析完成，总计 {count} 条频道")
    return categories

def build_yings_txt():
    root = os.getcwd()
    data_file = os.path.join(root, "data.txt")

    log("[0/5] 读取 data.txt")
    with open(data_file, 'r', encoding='utf-8') as f:
        url = f.read().strip()

    m3u_text = download_m3u(url)
    categories = extract_channels(m3u_text)

    out_file = os.path.join(root, "yings.txt")
    log("[4/5] 写入 yings.txt")

    with open(out_file, 'w', encoding='utf-8') as f:
        for cat, names in categories.items():
            f.write(f"{cat}：\n")
            line = "  "
            for name in names:
                item = f"{name}, "
                if wlen(line) + wlen(item) > 40:
                    f.write(line.rstrip() + "\n")
                    line = "  " + item
                else:
                    line += item
            if line.strip():
                f.write(line.rstrip() + "\n")
            f.write("\n")

    log("[5/5] yings.txt 写入完成（横向 + 自动换行 + 全格式兼容）")

if __name__ == "__main__":
    build_yings_txt()
