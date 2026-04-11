import re
from collections import defaultdict

INPUT_FILE = "duey.txt"
OUTPUT_FILE = "fenl.txt"

ITEMS_PER_LINE = 8

CATEGORIES = [
    "央视频道","付费频道","卫视频道","地方频道","港澳频道","国际频道",
    "数字频道","影剧频道","综艺频道","体育频道","音乐频道",
    "动漫频道","少儿频道","记录频道","游戏频道","直播频道"
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
# 分类规则（央视频道 + 付费频道 + 卫视频道）
# -------------------------
def classify(name):

    # -----------------------------------
    # 央视频道（严格 CCTV 1~17）
    # -----------------------------------
    m = re.match(r"^CCTV-(\d+)", name, re.I)
    if m:
        num = int(m.group(1))
        if 1 <= num <= 17:
            return "央视频道"

    # 兼容：cctv1 / 中央11台
    if re.match(r"^cctv(\d+)$", name, re.I):
        num = int(re.findall(r"\d+", name)[0])
        if 1 <= num <= 17:
            return "央视频道"

    if re.match(r"^中央(\d+)台$", name):
        num = int(re.findall(r"\d+", name)[0])
        if 1 <= num <= 17:
            return "央视频道"

    # -----------------------------------
    # 付费频道（所有 CCTV 付费频道）
    # -----------------------------------
    if name.upper().startswith("CCTV"):
        return "付费频道"

    # -----------------------------------
    # 卫视频道（所有含“卫视”）
    # -----------------------------------
    if "卫视" in name:
        return "卫视频道"

    # -----------------------------------
    # 其它全部归入直播频道（未匹配也列出）
    # -----------------------------------
    return "直播频道"

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
# 分类内部排序
# -------------------------
def sort_items(cat, items):
    if cat == "央视频道":
        return sorted(items, key=cctv_sort_key)
    if cat == "卫视频道":
        return sorted(items, key=weishi_sort_key)
    return sorted(items)

# -------------------------
# 输出 fenl.txt
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
    print("分类完成（央视频道 + 付费频道 + 卫视频道 + 未匹配也列出） → fenl.txt")
