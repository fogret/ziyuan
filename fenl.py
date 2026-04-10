import re
from collections import defaultdict

INPUT_FILE = "duey.txt"
OUTPUT_FILE = "fenl.txt"

# 每行最多多少个频道（你可以改）
ITEMS_PER_LINE = 8

CATEGORIES = [
    "央视频道","卫视频道","地方频道","港澳频道","国际频道",
    "数字频道","影剧频道","综艺频道","体育频道","音乐频道",
    "动漫频道","少儿频道","记录频道","游戏频道","直播频道",
    "未分类"
]

def classify(name):
    if name.startswith("CCTV-") or name.startswith("CCTV"):
        return "央视频道"
    if "卫视" in name:
        return "卫视频道"
    if any(k in name for k in ["TVB","翡翠","明珠","凤凰","澳视","台视","中视","华视","民视","ViuTV"]):
        return "港澳频道"
    if any(k in name for k in ["CNN","BBC","NHK","TRT","DW","FOX","NEWS","GLOBAL","AL JAZEERA"]):
        return "国际频道"
    if any(k in name for k in ["咪视界","咪视通","BestTV","NewTV","SCTV","黑莓"]):
        return "数字频道"
    if any(k in name for k in ["新闻","都市","公共","文旅","政法","经视","频道","电视台"]):
        return "地方频道"
    if any(k in name for k in ["体育","足球","篮球","赛事","UFC","ESPN"]):
        return "体育频道"
    if any(k in name for k in ["音乐","MTV","演唱会","歌曲"]):
        return "音乐频道"
    if any(k in name for k in ["动漫","动画","柯南","火影","海贼","龙珠","哆啦A梦","小新","丸子"]):
        return "动漫频道"
    if any(k in name for k in ["少儿","卡通","儿童","亲子"]):
        return "少儿频道"
    if any(k in name for k in ["电竞","游戏","英雄联盟","DOTA","CF","DNF","王者荣耀","和平精英"]):
        return "游戏频道"
    if any(k in name for k in ["纪录","纪实","探索","通史","航拍"]):
        return "记录频道"
    if any(k in name for k in ["综艺","娱乐","脱口秀","搞笑"]):
        return "综艺频道"
    if any(k in name for k in ["电影","剧场","影院","影"]):
        return "影剧频道"
    return "未分类"

def load_mapping():
    seen = set()
    mapping = []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "=>" not in line:
                continue

            original, std = line.strip().split("=>")
            original = original.strip()
            std = std.strip()

            # 去重（按标准频道名）
            if std in seen:
                continue
            seen.add(std)

            mapping.append((original, std))

    return mapping

def write_output(result):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for cat in CATEGORIES:
            f.write(f"{cat}：\n")

            items = sorted(result.get(cat, []))

            # 自动换行
            for i in range(0, len(items), ITEMS_PER_LINE):
                line_items = items[i:i + ITEMS_PER_LINE]
                f.write("  " + ", ".join(line_items) + "\n")

            f.write("\n")

if __name__ == "__main__":
    mapping = load_mapping()
    result = defaultdict(list)

    for original, std in mapping:
        cat = classify(std)
        result[cat].append(std)

    write_output(result)
    print("分类完成（去重 + 排序 + 自动换行） → fenl.txt")
