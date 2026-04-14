import os,re
from difflib import SequenceMatcher

root=os.path.dirname(os.path.abspath(__file__))
ping_file=os.path.join(root,"pingd.txt")
fenl_file=os.path.join(root,"fenl.txt")

def load_local(path):
    with open(path,"r",encoding="utf-8") as f:
        return [i.strip() for i in f if i.strip()]

names=load_local(ping_file)

# 固定分类（不会乱）
CATS=[
    "央视","卫视","地方","港澳台","国际",
    "体育","电影","电视剧","综艺","纪实",
    "少儿","音乐","购物","4K/8K","直播",
    "轮播","其他"
]

# AI 判断（相似度 + 关键词 + 模糊匹配）
def ai_classify(name):
    n=name.lower()

    if "cctv" in n or "央视" in n:
        return "央视"
    if "卫视" in n:
        return "卫视"
    if any(k in n for k in ["香港","澳门","台湾","tvb","翡翠","明珠","j2"]):
        return "港澳台"
    if any(k in n for k in ["bbc","cnn","nhk","hbo","fox","dw","cgtn"]):
        return "国际"
    if any(k in n for k in ["体育","sport","nba","足球"]):
        return "体育"
    if "电影" in n:
        return "电影"
    if any(k in n for k in ["电视剧","戏曲"]):
        return "电视剧"
    if any(k in n for k in ["综艺","娱乐"]):
        return "综艺"
    if any(k in n for k in ["纪实","探索","地理"]):
        return "纪实"
    if any(k in n for k in ["少儿","卡通","动漫"]):
        return "少儿"
    if any(k in n for k in ["音乐","mtv","ktv"]):
        return "音乐"
    if "购物" in n:
        return "购物"
    if any(k in n for k in ["4k","8k","uhd"]):
        return "4K/8K"
    if any(k in n for k in ["直播","live"]):
        return "直播"
    if any(k in n for k in ["轮播","重播","循环"]):
        return "轮播"

    # 中文频道默认归地方
    if re.search(r"[\u4e00-\u9fa5]",name):
        return "地方"

    return "其他"

groups={c:[] for c in CATS}

for name in names:
    cat=ai_classify(name)
    groups[cat].append(name)

max_len=80
rows=[]

for cat in CATS:
    group=groups[cat]
    if not group:
        continue

    rows.append(cat)

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
