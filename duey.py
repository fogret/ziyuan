import re

INPUT_FILE = "yings.txt"
OUTPUT_FILE = "duey.txt"

# 会被删除的垃圾标签（来源、线路、协议、平台等）
REMOVE_TAGS = [
    r"\[.*?\]", r"\(.*?\)", r"（.*?）",
    r"电信", r"移动", r"联通", r"广电", r"酒店",
    r"A三网", r"B三网", r"rtmp协议",
    r"HD", r"FHD", r"4K", r"8K",
    r"源", r"线路", r"频道", r"直播", r"超清", r"蓝光"
]

# 会被替换为空的符号
REMOVE_SYMBOLS = [
    r"-HD", r"-FHD", r"-4K", r"-8K",
    r"_HD", r"_FHD", r"_4K", r"_8K",
    r"HD", r"FHD", r"4K", r"8K",
    r" ", r"　"
]

def clean_name(name):
    # 删除标签
    for tag in REMOVE_TAGS:
        name = re.sub(tag, "", name, flags=re.IGNORECASE)

    # 删除符号
    for sym in REMOVE_SYMBOLS:
        name = name.replace(sym, "")

    # 删除多余符号
    name = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9\-]+", "", name)

    # 特殊修正：CCTV
    name = name.replace("CCTV", "CCTV-")
    name = name.replace("CCTV--", "CCTV-")
    name = re.sub(r"CCTV-$", "", name)

    # 去掉重复的 "-"
    name = re.sub(r"-+", "-", name)

    return name.strip()

def process():
    seen = set()
    out = []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "," not in line:
                continue

            name, url = line.strip().split(",", 1)
            name = clean_name(name)

            if not name:
                continue

            # 去重（按清洗后的标准名）
            if name in seen:
                continue
            seen.add(name)

            out.append(f"{name} => {name}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print("已生成 duey.txt（重写版：彻底清洗 + 去重）")

if __name__ == "__main__":
    process()
