import re
from collections import defaultdict

INPUT_FILE = "duey.txt"
OUTPUT_FILE = "fenl.txt"

ITEMS_PER_LINE = 8

CATEGORIES = [
    "央视频道","卫视频道","地方频道","港澳频道","国际频道",
    "数字频道","影剧频道","综艺频道","体育频道","音乐频道",
    "动漫频道","少儿频道","记录频道","游戏频道","直播频道",
    "未分类"
]

# -------------------------
# 精准分类规则（重写）
# -------------------------
def classify(name):

    # 央视频道（含 CCTV 数字频道）
    if re.match(r"^CCTV(-\d+)?$", name):
        return "央视频道"
    if name.startswith("CCTV-"):
        num = name.replace("CCTV-", "")
        if num.isdigit():
            return "央视频道"
        return "数字频道"  # CCTV 数字频道（怀旧剧场、风云足球等）

    # 卫视频道（严格识别）
    if name.endswith("卫视"):
        return "卫视频道"

    # 港澳台
    if any(k in name for k in ["TVB","翡翠","明珠","凤凰","澳视","台视","中视","华视","民视","ViuTV"]):
        return "港澳频道"

    # 国际频道（严格）
    if any(k in name for k in ["CNN","BBC","NHK","TRT","DW","FOX","GLOBAL","AL JAZEERA"]):
        return "国际频道"

    # 数字频道（央视付费频道 + NewTV + BesTV）
    if any(k in name for k in ["风云","怀旧","兵器","世界地理","女性时尚","第一剧场","电视指南","高尔夫","NewTV","BestTV","SCTV","黑莓"]):
        return "数字频道"

    # 地方频道（严格）
    if any(k in name for k in ["新闻","都市","公共","文旅","政法","经视","频道","电视台"]) and len(name) <= 6:
        return "地方频道"

    # 体育频道
    if any(k in name for k in ["体育","足球","篮球","赛事","UFC","ESPN"]):
        return "体育频道"

    # 音乐频道
    if any(k in name for k in ["音乐","MTV","演唱会","歌曲"]):
        return "音乐频道"

    # 动漫频道
    if any(k in name for k in ["动漫","动画","柯南","火影","海贼","龙珠","哆啦A梦","小新","丸子"]):
        return "动漫频道"

    # 少儿频道
    if any(k in name for k in ["少儿","卡通","儿童","亲子"]):
        return "少儿频道"

    # 游戏频道
    if any(k in name for k in ["电竞","游戏","英雄联盟","DOTA","CF","DNF","王者荣耀","和平精英"]):
        return "游戏频道"

    # 记录频道
    if any(k in name for k in ["纪录","纪实","探索","通史","航拍"]):
        return "记录频道"

    # 综艺频道
    if any(k in name for k in ["综艺","娱乐","脱口秀","搞笑"]):
        return "综艺频道"

    # 影剧频道
    if any(k in name for k in ["电影","剧场","影院","影"]):
        return "影剧频道"

    return "未分类"

# -------------------------
# 读取 duey.txt + 去重
# -------------------------
def load_mapping():
    seen = set()
    mapping = []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "=>" not in line:
                continue

            original, std = line.strip().split("=>")
            std = std.strip()

            if std in seen:
                continue
            seen.add(std)

            mapping.append(std)

    return mapping

# -------------------------
# 输出 fenl.txt（自动换行）
# -------------------------
def write_output(result):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for cat in CATEGORIES:
            f.write(f"{cat}：\n")

            items = sorted(result.get(cat, []))

            for i in range(0, len(items), ITEMS_PER_LINE):
                f.write("  " + ", ".join(items[i:i+ITEMS_PER_LINE]) + "\n")

            f.write("\n")

# -------------------------
# 主程序
# -------------------------
if __name__ == "__main__":
    mapping = load_mapping()
    result = defaultdict(list)

    for std in mapping:
        cat = classify(std)
        result[cat].append(std)

    write_output(result)
    print("分类完成（重写规则 + 自动换行 + 去重） → fenl.txt")
