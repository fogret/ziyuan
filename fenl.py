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
# CCTV 自然排序
# -------------------------
def cctv_sort_key(name):
    m = re.match(r"CCTV-(\d+)", name)
    if m:
        return (0, int(m.group(1)))
    return (1, name)

# -------------------------
# 卫视排序（按省份顺序）
# -------------------------
province_order = [
    "北京","天津","河北","山西","内蒙古","辽宁","吉林","黑龙江",
    "上海","江苏","浙江","安徽","福建","江西","山东","河南",
    "湖北","湖南","广东","广西","海南","重庆","四川","贵州",
    "云南","西藏","陕西","甘肃","青海","宁夏","新疆","兵团","大湾区"
]

def weishi_sort_key(name):
    for i, p in enumerate(province_order):
        if p in name:
            return (i, name)
    return (999, name)

# -------------------------
# 分类规则（专业级）
# -------------------------
def classify(name):

    # -------------------------
    # 央视频道（含 CCTV 数字频道）
    # -------------------------
    if re.match(r"^CCTV(-\d+)?$", name):
        return "央视频道"

    if name.startswith("CCTV-"):
        num = name.replace("CCTV-", "")
        if num.isdigit():
            return "央视频道"
        return "数字频道"  # CCTV 付费频道

    # -------------------------
    # 卫视频道（含高清）
    # -------------------------
    if "卫视" in name:
        return "卫视频道"

    # -------------------------
    # 港澳台
    # -------------------------
    if any(k in name for k in ["TVB","翡翠","明珠","凤凰","澳视","台视","中视","华视","民视","ViuTV"]):
        return "港澳频道"

    # -------------------------
    # 国际频道
    # -------------------------
    if any(k in name for k in ["CNN","BBC","NHK","TRT","DW","FOX","GLOBAL","ALJAZEERA","NEWS24"]):
        return "国际频道"

    # -------------------------
    # 数字频道（央视付费 + NewTV + BesTV）
    # -------------------------
    if any(k in name for k in [
        "风云","怀旧","兵器","世界地理","女性时尚","第一剧场","电视指南","高尔夫",
        "NewTV","SCTV","黑莓","精品","睛彩","专区"
    ]):
        return "数字频道"

    # -------------------------
    # 地方频道（严格）
    # -------------------------
    if any(k in name for k in ["新闻","都市","公共","文旅","政法","经视","电视台","综合"]) and len(name) <= 10:
        return "地方频道"

    # -------------------------
    # 体育频道（含主题频道）
    # -------------------------
    if any(k in name for k in ["体育","足球","篮球","赛事","UFC","ESPN","羽毛球","拳击","竞技"]):
        return "体育频道"

    # -------------------------
    # 音乐频道（含主题频道）
    # -------------------------
    if any(k in name for k in ["音乐","演唱会","歌曲","DJ","精选","点歌"]):
        return "音乐频道"

    # -------------------------
    # 动漫频道（含主题频道）
    # -------------------------
    if any(k in name for k in ["动漫","动画","柯南","火影","海贼","龙珠","哆啦A梦","小新","丸子"]):
        return "动漫频道"

    # -------------------------
    # 少儿频道
    # -------------------------
    if any(k in name for k in ["少儿","卡通","儿童","亲子"]):
        return "少儿频道"

    # -------------------------
    # 游戏频道（含手游/端游）
    # -------------------------
    if any(k in name for k in ["电竞","游戏","王者荣耀","和平精英","DOTA","CF","DNF","LOL","端游","手游"]):
        return "游戏频道"

    # -------------------------
    # 记录频道（含主题频道）
    # -------------------------
    if any(k in name for k in ["纪录","纪实","探索","通史","航拍"]):
        return "记录频道"

    # -------------------------
    # 综艺频道（含主题频道）
    # -------------------------
    if any(k in name for k in ["综艺","娱乐","搞笑","脱口秀"]):
        return "综艺频道"

    # -------------------------
    # 影剧频道（含主题频道）
    # -------------------------
    if any(k in name for k in ["电影","剧场","影院","影","大片","恐怖片","动作片","喜剧片"]):
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

            _, std = line.strip().split("=>")
            std = std.strip()

            if std in seen:
                continue
            seen.add(std)

            mapping.append(std)

    return mapping

# -------------------------
# 分类内部排序（自然排序）
# -------------------------
def sort_items(cat, items):
    if cat == "央视频道":
        return sorted(items, key=cctv_sort_key)
    if cat == "卫视频道":
        return sorted(items, key=weishi_sort_key)
    return sorted(items)

# -------------------------
# 输出 fenl.txt（自动换行）
# -------------------------
def write_output(result):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for cat in CATEGORIES:
            f.write(f"{cat}：\n")

            items = sort_items(cat, result.get(cat, []))

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
    print("分类完成（专业级规则 + 自然排序 + 自动换行） → fenl.txt")
