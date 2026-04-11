import re

INPUT_FILE = "yings.txt"
OUTPUT_FILE = "duey.txt"

# -------------------------
# 标准化频道名（核心功能）
# -------------------------
def clean_name(name):

    name = name.strip()

    # -------------------------
    # CCTV 主频道（1~17）
    # -------------------------
    m = re.match(r"^CCTV[- ]?(\d+)", name, re.I)
    if m:
        num = int(m.group(1))
        if 1 <= num <= 17:
            return f"CCTV-{num}"

    # cctv1 → CCTV-1
    m = re.match(r"^cctv(\d+)$", name, re.I)
    if m:
        num = int(m.group(1))
        if 1 <= num <= 17:
            return f"CCTV-{num}"

    # 中央11台 → CCTV-11
    m = re.match(r"^中央(\d+)台$", name)
    if m:
        num = int(m.group(1))
        if 1 <= num <= 17:
            return f"CCTV-{num}"

    # -------------------------
    # CCTV 付费频道（全部保留主名）
    # -------------------------
    if name.upper().startswith("CCTV"):
        return name.replace("高清", "").replace("HD", "").strip()

    # -------------------------
    # 卫视频道（统一格式）
    # -------------------------
    if "卫视" in name:
        return name.replace("高清", "").replace("HD", "").strip()

    # -------------------------
    # 咪视界 / 咪视通 / 百视通 / NewTV / SCTV
    # -------------------------
    if name.startswith("咪视界"):
        return "咪视界"

    if name.startswith("咪视通"):
        return "咪视通"

    if name.startswith("百视通"):
        return "百视通"

    if name.startswith("NewTV"):
        return name

    if re.match(r"^SCTV\d+$", name):
        return "SCTV"

    # -------------------------
    # 音乐频道（去掉数字）
    # -------------------------
    name = re.sub(r"精选\d+首", "精选", name)
    name = name.replace("完整版", "")

    # -------------------------
    # 美女展示类（去掉数字）
    # -------------------------
    if re.match(r"^美女.*\d+$", name):
        return re.sub(r"\d+$", "", name)

    # -------------------------
    # 默认清洗
    # -------------------------
    name = name.replace("高清", "")
    name = name.replace("频道", "")
    name = name.replace("电视台", "")
    name = name.replace("综合", "")
    name = name.replace("娱乐", "")
    name = name.strip()

    return name

# -------------------------
# 主程序：读取 yings.txt → 输出 duey.txt
# -------------------------
if __name__ == "__main__":

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for line in lines:
            if "=>" not in line:
                continue

            raw, _ = line.strip().split("=>")
            raw = raw.strip()

            std = clean_name(raw)

            f.write(f"{raw} => {std}\n")

    print("频道名标准化完成 → duey.txt")
