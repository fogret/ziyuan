import os,requests,re

root=os.path.dirname(os.path.abspath(__file__))
data_file=os.path.join(root,"data.txt")
pingd_file=os.path.join(root,"pingd.txt")
out_file=os.path.join(root,"live.m3u")

def log(x):
    print(x,flush=True)

def load_local(path):
    with open(path,"r",encoding="utf-8") as f:
        return [i.strip() for i in f if i.strip()]

# -----------------------------
# 把 pingd.txt 横向名称拆成竖向名称
# -----------------------------
def parse_pingd(lines):
    names = []
    for line in lines:
        # 去掉 emoji、冒号等
        clean = re.sub(r"[^\w\u4e00-\u9fa5,，()（） ]+", " ", line)

        # 按逗号分割
        parts = re.split(r"[，,]+", clean)

        for p in parts:
            p = p.strip()
            if not p:
                continue
            names.append(p)

    # 去重保持顺序
    seen = set()
    ordered = []
    for n in names:
        if n not in seen:
            seen.add(n)
            ordered.append(n)

    return ordered

# -----------------------------
# 解析 m3u 文件（支持增强格式）
# -----------------------------
def parse_m3u(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return []

        lines = r.text.splitlines()
        result = []
        name = None

        for line in lines:
            line = line.strip()

            if line.startswith("#EXTINF"):
                # 你的格式：#EXTINF:-1 xxx,真正名称
                if "," in line:
                    name = line.split(",", 1)[1].strip()
                else:
                    name = None

            elif line.startswith("http"):
                if name:
                    result.append((name, line))
                name = None

        return result

    except:
        return []

# -----------------------------
# 从 URL 推断名称（mp4/m3u8）
# -----------------------------
def guess_name(url):
    base = os.path.basename(url)
    base = re.sub(r"\.\w+$", "", base)
    return base.strip()

# -----------------------------
# 主流程
# -----------------------------
log("开始解析 data.txt")

raw_data = load_local(data_file)

sources = {}  # {名称: [url1,url2]}

for src in raw_data:

    if src.endswith(".m3u"):
        items = parse_m3u(src)
        for name, url in items:
            sources.setdefault(name, []).append(url)

    else:
        name = guess_name(src)
        if name:
            sources.setdefault(name, []).append(src)

log(f"解析到频道数量：{len(sources)}")

# -----------------------------
# 解析 pingd.txt（横向拆竖向）
# -----------------------------
raw_pingd = load_local(pingd_file)
pingd_names = parse_pingd(raw_pingd)

log(f"pingd.txt 名称数量：{len(pingd_names)}")

# -----------------------------
# 输出 m3u
# -----------------------------
with open(out_file, "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")

    for name in pingd_names:
        if name in sources:
            for url in sources[name]:
                f.write(f"#EXTINF:-1,{name}\n{url}\n")
        else:
            log(f"[MISS] 未找到名称：{name}")

log("live.m3u 生成完成")
