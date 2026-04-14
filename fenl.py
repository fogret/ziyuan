import os,re
from difflib import SequenceMatcher

root=os.path.dirname(os.path.abspath(__file__))
ping_file=os.path.join(root,"pingd.txt")
fenl_file=os.path.join(root,"fenl.txt")

def load_local(path):
    with open(path,"r",encoding="utf-8") as f:
        return [i.strip() for i in f if i.strip()]

names=load_local(ping_file)

def sim(a,b):
    return SequenceMatcher(None,a,b).ratio()

clusters=[]

for name in names:
    placed=False
    for group in clusters:
        if sim(name,group[0])>0.35:
            group.append(name)
            placed=True
            break
    if not placed:
        clusters.append([name])

def auto_title(group):
    if not group:
        return "未分类"
    text="".join(group)
    words=re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+",text)
    if not words:
        return "分类"
    freq={}
    for w in words:
        freq[w]=freq.get(w,0)+1
    top=sorted(freq.items(),key=lambda x:-x[1])[0][0]
    return top+"类"

max_len=80
rows=[]

for group in clusters:
    if not group:
        continue

    title=auto_title(group)
    rows.append(title)

    current=""
    for name in group:
        item=name+","
        if len(current)+len(item)>max_len:
            rows.append(current.rstrip(","))
            current=item
        else:
            current+=item
    if current:
        rows.append(current.rstrip(","))

with open(fenl_file,"w",encoding="utf-8") as f:
    for r in rows:
        f.write(r+"\n")
