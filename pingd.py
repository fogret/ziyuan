import os,sys,requests

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

def load_m3u(url):
    try:
        r=requests.get(url,timeout=10)
        if r.status_code!=200:
            log(f"[WARN] 无法读取 m3u: {url}")
            return []
        lines=r.text.splitlines()
        urls=[i.strip() for i in lines if i.strip().startswith("http")]
        log(f"[OK] 解析 m3u {url} 共 {len(urls)} 条播放地址")
        return urls
    except Exception as e:
        log(f"[ERR] 请求失败 {url}: {e}")
        return []

log("[START] pingd.py 开始执行")

raw_data=load_local(data_file,"data.txt")
data=[]

for src in raw_data:
    if src.endswith(".m3u") or src.endswith(".m3u8"):
        data.extend(load_m3u(src))
    else:
        data.append(src)

log(f"[OK] 最终播放源数量 {len(data)}")

pingd_lines=load_local(pingd_file,"pingd.txt")

groups=[]
for line in pingd_lines:
    parts=line.replace("，"," ").replace(","," ").split()
    if len(parts)>1:
        groups.append((parts[0],parts[1:]))

log(f"[OK] 分类 {len(groups)} 组")

with open(out_file,"w",encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for group,chans in groups:
        for ch in chans:
            for src in data:
                f.write(f'#EXTINF:-1 group-title="{group}",{ch}\n{src}\n')

log("[DONE] live.m3u 已生成")
