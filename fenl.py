import os,re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

root=os.path.dirname(os.path.abspath(__file__))
ping_file=os.path.join(root,"pingd.txt")
fenl_file=os.path.join(root,"fenl.txt")

def load_local(path):
    with open(path,"r",encoding="utf-8") as f:
        return [i.strip() for i in f if i.strip()]

names=load_local(ping_file)

vectorizer=TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
X=vectorizer.fit_transform(names)

k=max(3,min(12,len(names)//5))
model=KMeans(n_clusters=k,random_state=0,n_init="auto").fit(X)
labels=model.labels_

clusters={}
for name,label in zip(names,labels):
    clusters.setdefault(label,[]).append(name)

def auto_title(group):
    text=" ".join(group)
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

for label,group in clusters.items():
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
