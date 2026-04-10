import re
from sentence_transformers import SentenceTransformer, util

# 你的 15 类
CATEGORIES = [
    "央视频道","付费频道","卫视频道","地方频道","影剧频道",
    "数字频道","音乐频道","综娱频道","记录频道","港澳频道",
    "国际频道","少儿频道","动漫频道","直播频道","游戏频道"
]

# 加载中文语义模型（一次下载，之后永久使用）
model = SentenceTransformer("shibing624/text2vec-base-chinese")

# 编码 15 类
cat_emb = model.encode(CATEGORIES, convert_to_tensor=True)

def normalize(name):
    n = name.strip()
    up = n.upper()

    if "CCTV5+" in up or "CCTV-5+" in up:
        return "CCTV-5+"

    m = re.search(r"CCTV[-_ ]?0?(\d+)", up)
    if m:
        return f"CCTV-{m.group(1)}"

    return n

def load_yings(path="yings.txt"):
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            parts = [p.strip() for p in re.split(r"[,\s]+", raw) if p.strip()]
            out.extend(parts)
    return out

def classify(name):
    emb = model.encode(name, convert_to_tensor=True)
    sim = util.cos_sim(emb, cat_emb)[0]
    idx = sim.argmax().item()
    return CATEGORIES[idx]

def write_output(result, path="duey.txt"):
    with open(path, "w", encoding="utf-8") as f:
        for cat in CATEGORIES:
            f.write(f"{cat}：\n")
            line = "  "
            for name in sorted(set(result.get(cat, []))):
                item = f"{name}, "
                if len(line) + len(item) > 40:
                    f.write(line + "\n")
                    line = "  " + item
                else:
                    line += item
            f.write(line + "\n\n")

if __name__ == "__main__":
    yings = load_yings()
    result = {c: [] for c in CATEGORIES}

    for name in yings:
        clean = normalize(name)
        cat = classify(clean)
        result[cat].append(clean)

    write_output(result)
    print("按 15 类自动分类完成 → duey.txt")
