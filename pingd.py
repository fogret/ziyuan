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

# 清洗频道名（适配你 pingd.txt 的复杂格式）
def clean_name(text):
    text = re.sub(r"[^\w\u4e00-\u9fa5]+", " ", text)
    parts = text.split()
    return parts[-1] if parts else ""

# 解析 m3u 文件
def parse_m3u(url):
    try:
        r=requests.get(url,timeout=10)
        if r.status_code!=200:
            return []

        lines=r.text.splitlines()
        result=[]
        name=None

        for line in lines:
            line=line.strip()
            if line.startswith("#EXTINF"):
                m=re.search(r",(.+)$",line)
                if m:
                    name=clean_name(m.group(1).strip())
            elif line.startswith("http"):
                if name:
                    result.append((name,line))
                name=None

        return result

    except:
        return []

# 从 URL 推断频道名（mp4/m3u8）
def guess_name(url):
    base=os.path.basename(url)
    base=re.sub(r"\.\w+$","",base)
    base=re.sub(r"[^\w\u4e00-\u9fa5]+"," ",base)
    return base.strip()

log("开始解析 data.txt")

raw_data=load_local(data_file)

# 所有频道源：{频道名: [url1,url2]}
sources={}

for src in raw_data:

    if src.endswith(".m3u"):
        items=parse_m3u(src)
        for name,url in items:
            sources.setdefault(name,[]).append(url)

    else:
        name=guess_name(src)
        if name:
            sources.setdefault(name,[]).append(src)

log(f"解析到频道数量：{len(sources)}")

# 解析 pingd.txt（自动适配你的格式）
raw_pingd=load_local(pingd_file)
pingd_channels=[]

for line in raw_pingd:
    line=re.sub(r"[^\w\u4e00-\u9fa5,，、 ]+"," ",line)
    parts=re.split(r"[ ,，、]+",line)
    for p in parts:
        p=p.strip()
        if not p:
            continue
        pingd_channels.append(p)

# 去重保持顺序
seen=set()
ordered=[]
for c in pingd_channels:
    if c not in seen:
        seen.add(c)
        ordered.append(c)

log(f"pingd.txt 频道数量：{len(ordered)}")

# 输出 m3u
with open(out_file,"w",encoding="utf-8") as f:
    f.write("#EXTM3U\n")

    for ch in ordered:
        if ch in sources:
            for url in sources[ch]:
                f.write(f"#EXTINF:-1,{ch}\n{url}\n")
        else:
            log(f"[MISS] 未找到频道：{ch}")

log("live.m3u 生成完成")
