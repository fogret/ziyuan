import os,sys,requests,re

root=os.path.dirname(os.path.abspath(__file__))
data_file=os.path.join(root,"data.txt")
pingd_file=os.path.join(root,"pingd.txt")
out_file=os.path.join(root,"live.m3u")

def log(x):
    print(x,flush=True)

def load_local(path,name):
    if not os.path.exists(path):
        log(f"[ERR] {name} 不存在")
        return []
    with open(path,"r",encoding="utf-8") as f:
        return [i.strip() for i in f if i.strip()]

# 清洗频道名：去掉 emoji、符号、分类、标点
def clean(text):
    text = re.sub(r"[^\w\u4e00-\u9fa5]+", " ", text)  # 去掉 emoji 和符号
    parts = text.split()
    # 最后一个通常是频道名
    return parts[-1] if parts else ""

# 解析 m3u：提取频道名 + 播放地址
def parse_m3u(url):
    try:
        r=requests.get(url,timeout=10)
        if r.status_code!=200:
            log(f"[WARN] 无法读取 m3u: " + url)
            return []

        lines=r.text.splitlines()
        result=[]
        name=None

        for line in lines:
            line=line.strip()
            if line.startswith("#EXTINF"):
                m=re.search(r",(.+)$",line)
                if m:
                    name=clean(m.group(1).strip())
            elif line.startswith("http"):
                if name:
                    result.append((name,line))
                name=None

        log(f"[OK] 解析 m3u {url} 共 {len(result)} 条")
        return result

    except Exception as e:
        log(f"[ERR] 请求失败 {url}: {e}")
        return []

log("[START] pingd.py 开始执行")

raw_data=load_local(data_file,"data.txt")

# 所有解析后的频道源：[(频道名, 播放地址)]
all_sources=[]

media_ext = (".mp3",".flac",".m4a",".aac",".wav",".ogg",
             ".mp4",".ts",".flv",".m3u8")

for src in raw_data:

    if src.endswith(".m3u"):
        all_sources.extend(parse_m3u(src))

    elif src.endswith(media_ext):
        all_sources.append((None,src))

    else:
        all_sources.append((None,src))

log(f"[OK] 总共解析频道源 {len(all_sources)} 条")

# 解析 pingd.txt（智能提取频道名）
raw_channels = load_local(pingd_file,"pingd.txt")
channels = [clean(line) for line in raw_channels if clean(line)]

log(f"[OK] 频道数量 {len(channels)}")

# 输出
with open(out_file,"w",encoding="utf-8") as f:
    f.write("#EXTM3U\n")

    for ch in channels:

        matched=[]

        # 匹配 m3u 解析出来的频道名
        for name,url in all_sources:
            if name and ch in name:
                matched.append(url)

        # 匹配 mp4/mp3/flac 等 URL（按频道名模糊匹配 URL）
        for name,url in all_sources:
            if name is None and ch in url:
                matched.append(url)

        if not matched:
            log(f"[MISS] 未找到频道: " + ch)
            continue

        for url in matched:
            f.write(f'#EXTINF:-1,{ch}\n{url}\n')

log("[DONE] live.m3u 已生成")
