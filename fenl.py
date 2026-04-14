import os,re

root=os.path.dirname(os.path.abspath(__file__))
ping_file=os.path.join(root,"ping.txt")
fenl_file=os.path.join(root,"fenl.txt")

def load_local(path):
    with open(path,"r",encoding="utf-8") as f:
        return [i.strip() for i in f if i.strip()]

lines=load_local(ping_file)

rules={
    "央视":r"^CCTV|央视",
    "卫视":r"卫视",
    "地方":r"(北京|上海|广东|深圳|湖南|湖北|福建|厦门|江苏|浙江|四川|重庆|云南|贵州|广西|江西|安徽|河南|河北|山东|山西|天津|黑龙江|吉林|辽宁|内蒙古|宁夏|青海|西藏|新疆)",
    "港澳台":r"(香港|澳门|台湾|TVB|翡翠|明珠|J2|中视|华视|民视)",
    "国际":r"(BBC|CNN|NHK|HBO|FOX|DW|CGTN|Discovery|National Geographic|NGC)",
    "体育":r"(体育|sport|NBA|足球|CCTV5)",
    "电影":r"(电影|cinema|movie|影)",
    "电视剧":r"(电视剧|戏曲|影视频道)",
    "综艺":r"(综艺|娱乐)",
    "纪实":r"(纪实|探索|地理|自然|CCTV9)",
    "少儿":r"(少儿|卡通|动漫|CCTV14)",
    "音乐":r"(音乐|MTV|KTV)",
    "购物":r"(购物|导购)",
    "4K/8K":r"(4K|8K|UHD)",
    "轮播":r"(轮播|频道\d+|直播室)",
    "宗教":r"(佛|道|宗教|维语|藏语)",
    "新闻":r"(新闻|CCTV13)",
    "测试":r"(测试|test)"
}

groups={k:[] for k in rules}
groups["其他"]=[]

for line in lines:
    parts=re.split(r"[，, ]+",line)
    for name in parts:
        if not name:
            continue
        matched=False
        for g,pat in rules.items():
            if re.search(pat,name,re.I):
                groups[g].append(name)
                matched=True
                break
        if not matched:
            groups["其他"].append(name)

rows=[]
for g,names in groups.items():
    seen=set()
    ordered=[]
    for n in names:
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    if ordered:
        rows.append(g+","+",".join(ordered))

with open(fenl_file,"w",encoding="utf-8") as f:
    for r in rows:
        f.write(r+"\n")
