from sentence_transformers import SentenceTransformer, util
import re

# 你的 15 类
CATEGORIES = [
    "央视频道","付费频道","卫视频道","地方频道","影剧频道",
    "数字频道","音乐频道","综娱频道","记录频道","港澳频道",
    "国际频道","少儿频道","动漫频道","直播频道","游戏频道"
]

# 标准化
def normalize(name):
    n = name.strip()
    up = n.upper()

    if "CCTV5+" in up or "CCTV-5+" in up or "CCTV5PLUS" in up:
        return "CCTV-5+"

    m = re.search(r"CCTV[-_ ]?0?(\d+)", up)
    if m:
        return f"CCTV-{m.group(1)}"

    n = re.sub(r"(高清|HD|4K|超清|频道|台)$", "", n).strip()
    return n

# 提取频道
def extract_channels():
    out = []
    with open("yings.txt","r",encoding="utf-8") as f:
        for line in f:
            if "," in line:
                parts = line.split(",")
            else:
                parts = [line]
            for p in parts:
                p = p.strip()
                if p and not p.endswith("："):
                    out.append(p)
    return out

# 主流程
if __name__ == "__main__":
    raw = extract_channels()
    clean = [normalize(x) for x in raw]

    # 加载最强中文语义模型
    model = SentenceTransformer("shibing624/text2vec-base-chinese")

    # 编码分类
    cat_emb = model.encode(CATEGORIES, convert_to_tensor=True)

    result = {c: [] for c in CATEGORIES}

    # 对每个频道进行语义分类
    for name in clean:
        emb = model.encode(name, convert_to_tensor=True)
        sim = util.cos_sim(emb, cat_emb)[0]
        idx = sim.argmax().item()
        result[CATEGORIES[idx]].append(name)

    # 输出
    with open("duey.txt","w",encoding="utf-8") as f:
        for cat, items in result.items():
            f.write(f"{cat}：\n")
            line = "  "
            for name in items:
                item = f"{name}, "
                if len(line)+len(item)>40:
                    f.write(line+"\n")
                    line = "  "+item
                else:
                    line += item
            f.write(line+"\n\n")

    print("最准确分类完成 → duey.txt")
