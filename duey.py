import re
from collections import defaultdict

INPUT_FILE = "yings.txt"
OUTPUT_FILE = "duey.txt"

# 解析 yings.txt
def parse_file(path):
    name_to_cats = defaultdict(set)
    current_cat = None

    # 匹配 “xxx频道：”
    cat_pattern = re.compile(r"^\s*(.+?)频道：\s*$")

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")

            # 1. 判断是否是分类标题
            m = cat_pattern.match(line)
            if m:
                current_cat = m.group(1).strip()
                continue

            # 2. 普通行（频道名）
            if not current_cat:
                continue

            parts = [p.strip() for p in line.split(",") if p.strip()]
            for p in parts:
                if p.endswith("："):
                    continue
                name_to_cats[p].add(current_cat)

    return name_to_cats

# 反转映射：分类 → 频道列表
def invert_mapping(name_to_cats):
    cat_to_names = defaultdict(list)
    for name, cats in name_to_cats.items():
        for c in cats:
            cat_to_names[c].append(name)
    # 去重 + 排序
    for c in cat_to_names:
        cat_to_names[c] = sorted(set(cat_to_names[c]))
    return cat_to_names

# 输出 duey.txt
def write_output(cat_to_names):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for cat, items in cat_to_names.items():
            f.write(f"{cat}频道：\n")
            line = "  "
            for name in items:
                item = f"{name}, "
                if len(line) + len(item) > 40:
                    f.write(line + "\n")
                    line = "  " + item
                else:
                    line += item
            f.write(line + "\n\n")

if __name__ == "__main__":
    name_to_cats = parse_file(INPUT_FILE)
    cat_to_names = invert_mapping(name_to_cats)
    write_output(cat_to_names)
    print("分类完成 → duey.txt")
