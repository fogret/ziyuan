import re
from collections import defaultdict, OrderedDict

# 输入文件：就是你发的这种带「央视频道：」「付费频道：」的大文件
INPUT_FILE = "_cctv-1_cctv_1775827272916.txt"
OUTPUT_FILE = "duey.txt"

# 允许的分类名（顺序可改）
CATEGORY_ORDER = [
    "央视频道","付费频道","卫视频道","地方频道","影剧频道",
    "数字频道","音乐频道","综娱频道","记录频道","港澳频道",
    "国际频道","少儿频道","动漫频道","直播频道","游戏频道"
]

def normalize_name(name: str) -> str:
    n = name.strip()
    if not n:
        return ""
    # 去掉结尾常见修饰
    n = re.sub(r"[，,。.\s]+$", "", n)
    return n

def parse_file(path: str):
    """
    遍历整个文件：
    - 遇到「xxx频道：」就切换当前分类
    - 其它行按逗号拆分频道名，归到当前分类
    """
    name_to_cats = defaultdict(set)
    current_cat = None

    cat_pattern = re.compile(r"^\s*(.+?)频道：\s*$")

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")

            # 1. 判断是不是「xxx频道：」
            m = cat_pattern.match(line)
            if m:
                title = m.group(1).strip()
                # 只接受在我们预设里的分类
                if title in CATEGORY_ORDER:
                    current_cat = title
                else:
                    # 其它类似「港澳频道」「国际频道」也可以自动接入
                    current_cat = title
                    if title not in CATEGORY_ORDER:
                        CATEGORY_ORDER.append(title)
                continue

            # 2. 普通行：在当前分类下拆频道名
            if current_cat is None:
                continue

            # 去掉前导缩进
            line = line.strip()
            if not line:
                continue

            # 有些行是「xxx频道：」的延续，这里再防一手
            if line.endswith("频道："):
                continue

            parts = [p for p in line.split(",") if p.strip()]
            for p in parts:
                name = normalize_name(p)
                if not name:
                    continue
                # 排除类似「更新时间2026.4.10」这种
                if "更新时间" in name:
                    continue
                name_to_cats[name].add(current_cat)

    return name_to_cats

def invert_mapping(name_to_cats):
    """
    把「频道名 → 多个分类」反转成
    「分类 → 频道名列表」
    """
    cat_to_names = defaultdict(list)
    for name, cats in name_to_cats.items():
        for c in cats:
            cat_to_names[c].append(name)
    # 去重 + 排序
    for c in cat_to_names:
        cat_to_names[c] = sorted(set(cat_to_names[c]))
    return cat_to_names

def write_output(cat_to_names, path: str):
    with open(path, "w", encoding="utf-8") as f:
        # 按预设顺序输出
        for cat in CATEGORY_ORDER:
            if cat not in cat_to_names:
                continue
            f.write(f"{cat}：\n")
            line = "  "
            for name in cat_to_names[cat]:
                item = f"{name}, "
                if len(line) + len(item) > 40:
                    f.write(line + "\n")
                    line = "  " + item
                else:
                    line += item
            if line.strip():
                f.write(line + "\n\n")

if __name__ == "__main__":
    name_to_cats = parse_file(INPUT_FILE)
    cat_to_names = invert_mapping(name_to_cats)
    write_output(cat_to_names, OUTPUT_FILE)
    print(f"分类抽取完成 → {OUTPUT_FILE}")
