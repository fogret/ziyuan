import os
import re
import json
import requests

def log(msg):
    print(msg, flush=True)

def wlen(s):
    return sum(2 if ord(c) > 127 else 1 for c in s)

def download(url):
    log(f"  → 下载: {url}")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text.lstrip("\ufeff")
    except Exception as e:
        log(f"    × 下载失败: {e}")
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
            log(f"    M3U 解析进度：{count}")
    log(f"    M3U 解析完成：{count}")
    return categories

def parse_txt(text, categories, seen):
    count = 0
    for line in text.splitlines():
        name = line.strip()
        if not name or name.startswith("#"):
            continue
        if name in seen:
            continue
        seen.add(name)
        categories.setdefault("未分类", []).append(name)
        count += 1
        if count % 200 == 0:
            log(f"    TXT 解析进度：{count}")
    log(f"    TXT 解析完成：{count}")
    return categories

def parse_json(text, categories, seen):
    try:
        data = json.loads(text)
    except:
        log("    × JSON 解析失败")
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
            log(f"    JSON 解析进度：{count}")

    log(f"    JSON 解析完成：{count}")
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

    log("[0/5] 读取 data.txt")
    with open(data_file, "r", encoding="utf-8") as f:
        urls = [x.strip() for x in f.readlines() if x.strip()]

    log(f"[1/5] 共 {len(urls)} 条源，将逐条下载并解析")

    categories = {}
    seen = set()

    for idx, url in enumerate(urls, 1):
        log(f"[2/5] 处理源 {idx}/{len(urls)}")
        text = download(url)
        if not text:
            continue

        fmt = detect_format(text)
        log(f"    检测到格式：{fmt}")

        if fmt == "m3u":
            parse_m3u(text, categories, seen)
        elif fmt == "json":
            parse_json(text, categories, seen)
        else:
            parse_txt(text, categories, seen)

    log(f"[3/5] 全部源解析完成，总计 {len(seen)} 条频道（已去重）")

    out_file = os.path.join(root, "yings.txt")
    log("[4/5] 写入 yings.txt（横向 + 自动换行）")

    with open(out_file, "w", encoding="utf-8") as f:
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

    log("[5/5] yings.txt 写入完成")

if __name__ == "__main__":
    build_yings()
