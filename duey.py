import re
from sentence_transformers import SentenceTransformer, util

# 你的 15 类
CATEGORIES = [
    "央视频道","付费频道","卫视频道","地方频道","影剧频道",
    "数字频道","音乐频道","综娱频道","记录频道","港澳频道",
    "国际频道","少儿频道","动漫频道","直播频道","游戏频道"
]

# ============================
# 第一层：增强规则（只覆盖模型容易误判的 5%）
# ============================
def enhanced_rules(name):
    up = name.upper()

    # CCTV
    if up.startswith("CCTV") or "中央" in name:
        return "央视频道"

    # 卫视
    if "卫视" in name:
        return "卫视频道"

    # 港澳台
    if any(x in name for x in ["TVB","凤凰","澳门","香港","台视","中视","民视","华视","ViuTV"]):
        return "港澳频道"

    # 少儿
    if any(x in name for x in ["卡通","少儿","宝宝","亲子","育乐","嘉佳"]):
        return "少儿频道"

    # 动漫
    if any(x in name for x in ["动漫","动画","柯南","火影","海贼","龙珠","哆啦","小丸子"]):
        return "动漫频道"

    # 游戏
    if any(x in name for x in ["LOL","DOTA","CF","王者","游戏","电竞"]):
        return "游戏频道"

    return None


# ============================
# 第二层：模式识别（自动识别内容类型）
# ============================
def pattern_rules(name):

    # 专场 → 直播
    if "专场" in name:
        return "直播频道"

    # 系列 → 影剧
    if "系列" in name:
        return "影剧频道"

    # 精选 / 点播 → 音乐
    if "精选" in name or "点播" in name:
        return "音乐频道"

    # 纪录 / 纪实
    if "纪录" in name or "纪实" in name:
        return "记录频道"

    # 电影 / 影院
    if "电影" in name or "影院" in name:
        return "影剧频道"

    # 体育
    if "体育" in name:
        return "直播频道"

    # 新闻
    if "新闻" in name:
        return "地方频道"

    return None


# ============================
# 标准化
# ============================
def normalize(name):
    n = name.strip()
    up = n.upper()

    if "CCTV5+" in up or "CCTV-5+" in up:
        return "CCTV-5+"

    m = re.search(r"CCTV[-_ ]?0?(\d+)", up)
    if m:
        return f"CCTV-{m.group(1)}"

    n = re.sub(r"(高清|HD|4K|超清|频道|台)$", "", n).strip()
    return n


# ============================
# 提取频道
# ============================
def extract_channels():
    out = []
    with open("yings.txt","r",encoding="utf-8") as f:
        for line in f:
            parts = line.split(",") if "," in line else [line]
            for p in parts:
                p = p.strip()
                if p and not p.endswith("："):
                    out.append(p)
    return out


# ============================
# 主流程（终极版）
# ============================
if __name__ == "__main__":
    raw = extract_channels()
    clean = [normalize(x) for x in raw]

    # 加载最强中文语义模型
    model = SentenceTransformer("shibing624/text2vec-base-chinese")

    # 编码分类
    cat_emb = model.encode(CATEGORIES, convert_to_tensor=True)

    result = {c: [] for c in CATEGORIES}

    for name in clean:

        # 第一层：增强规则
        cat = enhanced_rules(name)
        if cat:
            result[cat].append(name)
            continue

        # 第二层：模式识别
        cat = pattern_rules(name)
        if cat:
            result[cat].append(name)
            continue

        # 第三层：语义分类（核心）
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

    print("终极版分类完成 → duey.txt")
