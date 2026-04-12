import os
import re
import json
import requests

def log(msg):
    print(msg, flush=True)

def wlen(s):
    return sum(2 if ord(c) > 127 else 1 for c in s)

def download(url):
    log(f"  -> Download: {url}")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text.lstrip("\ufeff")
    except Exception as e:
        log(f"    x Download failed: {e}")
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

def clean_txt_name(line):
    line = line.strip()
    if not line:
        return ""
    if "更新" in line:
        return ""
    if "#genre#" in line:
        return ""
    if "," in line:
        name = line.split(",", 1)[0].strip()
    else:
        name = line
    if name.startswith("http"):
        return ""
    return name.strip()

def parse_m3u(text, categories, seen):
    count = 0
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("#EXTINF"):
            continue
        group, name = parse_extinf(line)
        if not name or name in seen:
            continue
        seen.add(name)
        categories.setdefault(group, []).append(name)
        count += 1
        if count % 200 == 0:
            log(f"    M3U progress: {count}")
    log(f"    M3U done: {count}")
    return categories

def parse_txt(text, categories, seen):
    count = 0
    for line in text.splitlines():
        name = clean_txt_name(line)
        if not name or name in seen:
            continue
        seen.add(name)
        categories.setdefault("未分类", []).append(name)
        count += 1
        if count % 200 == 0:
            log(f"    TXT progress: {count}")
    log(f"    TXT done: {count}")
    return categories

def parse_json(text, categories, seen):
    try:
        data = json.loads(text)
    except:
        log("    x JSON parse failed")
        return categories
    count = 0
    items = data.values() if isinstance(data, dict) else data
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("channel") or "").strip()
        group = str(item.get("group") or item.get("category") or "未分类").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        categories.setdefault(group, []).append(name)
        count += 1
        if count % 200 == 0:
            log(f"    JSON progress: {count}")
    log(f"    JSON done: {count}")
    return categories

def detect_format(text):
    if "#EXTINF" in text:
        return "m3u"
    if text.strip().startswith("{") or text.strip().startswith("["):
        return "json"
    return "txt"

def build_yings():
    root = os.getcwd()
    data_file = os.path.join(root, "data.txt")

    log("[0/5] Read data.txt")
    with open(data_file, "r", encoding="utf-8") as f:
        urls = [x.strip() for x in f.readlines() if x.strip()]

    log(f"[1/5] Total {len(urls)} sources")

    categories = {}
    seen = set()

    for idx, url in enumerate(urls, 1):
        log(f"[2/5] Source {idx}/{len(urls)}")
        text = download(url)
        if not text:
            continue
        fmt = detect_format(text)
        log(f"    Format: {fmt}")
        if fmt == "m3u":
            parse_m3u(text, categories, seen)
        elif fmt == "json":
            parse_json(text, categories, seen)
        else:
            parse_txt(text, categories, seen)

    log(f"[3/5] Total channels: {len(seen)}")

    out_file = os.path.join(root, "yings.txt")
    if os.path.exists(out_file):
        os.remove(out_file)

    log("[4/5] Writing yings.txt")

    with open(out_file, "w", encoding="utf-8") as f:
        for cat, names in categories.items():
            f.write(f"{cat}:\n")
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

    log("[5/5] Done")

if __name__ == "__main__":
    build_yings()
