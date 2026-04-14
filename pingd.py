import os,re

root=os.path.dirname(os.path.abspath(__file__))
yings_file=os.path.join(root,"yings.txt")
pingd_file=os.path.join(root,"pingd.txt")

def load_local(path):
    with open(path,"r",encoding="utf-8") as f:
        return [i.strip() for i in f if i.strip()]

lines=load_local(yings_file)

names=[]
for line in lines:
    clean=re.sub(r"[^\w\u4e00-\u9fa5]+"," ",line)
    parts=clean.split()
    for p in parts:
        if p:
            names.append(p)

seen=set()
ordered=[]
for n in names:
    if n not in seen:
        seen.add(n)
        ordered.append(n)

max_len=80
current=""
rows=[]

for name in ordered:
    item=(name+",")
    if len(current)+len(item)>max_len:
        rows.append(current.rstrip(","))
        current=item
    else:
        current+=item

if current:
    rows.append(current.rstrip(","))

with open(pingd_file,"w",encoding="utf-8") as f:
    for r in rows:
        f.write(r+"\n")
