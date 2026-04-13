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

# 解析 m3u：提取频道名 + 播放地址
def parse_m3u(url):
    try:
        r=requests.get(url,timeout=10)
        if r.status_code!=200:
            log(f"[WARN] 无法读取 m3u: {url}")
            return []

        lines=r.text.splitlines()
        result=[]
        name=None

        for line in lines:
            line=line.strip()
            if line.startswith("#EXTINF"):
                m=re.search(r",(.+)$",line)
                if m:
                    name=m.group(1).strip()
            elif line.startswith("http"):
                if name:
                    result.append((name,line))
                name=None

        log(f"[OK] 解析 m3u {url} 共 {len(result)} 条播放地址")
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

    # data.txt 里的 m3u → 解析里面的真实播放地址
    if src.endswith(".m3u"):
        all_sources.extend(parse_m3u(src))

    # 其他格式 → 直接加入（频道名未知）
    elif src.endswith(media_ext):
        all_sources.append((None,src))

    else:
        log(f"[WARN] 未识别格式，按普通 URL 处理: {src}")
        all_sources.append((None,src))

log(f"[OK] 总共解析频道源 {len(all_sources)} 条")

# 加载分类与频道
pingd_lines=load_local(pingd_file,"pingd.txt")

groups=[]
for line in pingd_lines:
    parts=line.replace("，"," ").replace(","," ").split()
    if len(parts)>1:
        groups.append((parts[0],parts[1:]))

log(f"[OK] 分类 {len(groups)} 组")

# 输出
with open(out_file,"w",encoding="utf-8") as f:
    f.write("#EXTM3U\n")

    for group,chans in groups:
        for ch in chans:

            matched=[]

            # 1. 匹配 m3u 解析出来的频道名
            for name,url in all_sources:
                if name and ch in name:
                    matched.append(url)

            # 2. 匹配 mp3/mp4/flac 等 URL（按频道名模糊匹配 URL）
            for name,url in all_sources:
                if name is None and ch in url:
                    matched.append(url)

            if not matched:
                log(f"[MISS] 未找到频道: {ch}")
                continue

            for url in matched:
                f.write(f'#EXTINF:-1 group-title="{group}",{ch}\n{url}\n')

log("[DONE] live.m3u 已生成")
