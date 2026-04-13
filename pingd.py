import os

root=os.path.dirname(os.path.abspath(__file__))
data_file=os.path.join(root,"data.txt")
pingd_file=os.path.join(root,"pingd.txt")
out_file=os.path.join(root,"live.m3u")

def load_lines(path):
    if not os.path.exists(path):
        return []
    with open(path,"r",encoding="utf-8") as f:
        return [i.strip() for i in f if i.strip()]

data=load_lines(data_file)
pingd=load_lines(pingd_file)

channels=[]
for line in pingd:
    parts=line.replace("，"," ").replace(","," ").split()
    for p in parts:
        if p not in channels:
            channels.append(p)

with open(out_file,"w",encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for ch in channels:
        for src in data:
            f.write(f"#EXTINF:-1,{ch}\n{src}\n")
