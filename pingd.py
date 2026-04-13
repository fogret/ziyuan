import os,sys

root=os.path.dirname(os.path.abspath(__file__))
data_file=os.path.join(root,"data.txt")
pingd_file=os.path.join(root,"pingd.txt")
out_file=os.path.join(root,"live.m3u")

def log(x):
    print(x,flush=True)

def load(path,name):
    if not os.path.exists(path):
        log(f"[ERR] {name} 不存在")
        return []
    with open(path,"r",encoding="utf-8") as f:
        lines=[i.strip() for i in f if i.strip()]
    log(f"[OK] 读取 {name} {len(lines)} 行")
    return lines

log("[START] pingd.py 开始执行")

data=load(data_file,"data.txt")
pingd_lines=load(pingd_file,"pingd.txt")

groups=[]  # [(分类, [频道列表])]
for line in pingd_lines:
    parts=line.replace("，"," ").replace(","," ").split()
    if len(parts) > 1:
        group=parts[0]
        chans=parts[1:]
        groups.append((group,chans))

log(f"[OK] 分类 {len(groups)} 组")

try:
    with open(out_file,"w",encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for group,chans in groups:
            for ch in chans:
                for src in data:
                    f.write(f'#EXTINF:-1 group-title="{group}",{ch}\n{src}\n')
    log("[DONE] live.m3u 已生成")
except Exception as e:
    log(f"[ERR] 写入 live.m3u 失败: {e}")
    sys.exit(1)

log("[END] pingd.py 执行完毕")
