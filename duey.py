import re

INPUT_FILE = "yings.txt"
OUTPUT_FILE = "duey.txt"

def clean_name(name):

    name = name.strip()

    m = re.match(r"^CCTV[- ]?(\d+)", name, re.I)
    if m:
        num = int(m.group(1))
        if 1 <= num <= 17:
            return f"CCTV-{num}"

    m = re.match(r"^cctv(\d+)$", name, re.I)
    if m:
        num = int(m.group(1))
        if 1 <= num <= 17:
            return f"CCTV-{num}"

    m = re.match(r"^中央(\d+)台$", name)
    if m:
        num = int(m.group(1))
        if 1 <= num <= 17:
            return f"CCTV-{num}"

    if name.upper().startswith("CCTV"):
        return name.replace("高清", "").replace("HD", "").strip()

    if "卫视" in name:
        return name.replace("高清", "").replace("HD", "").strip()

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

    name = re.sub(r"精选\d+首", "精选", name)
    name = name.replace("完整版", "")

    if re.match(r"^美女.*\d+$", name):
        return re.sub(r"\d+$", "", name)

    name = name.replace("高清", "")
    name = name.replace("频道", "")
    name = name.replace("电视台", "")
    name = name.replace("综合", "")
    name = name.replace("娱乐", "")
    name = name.strip()

    return name


if __name__ == "__main__":

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for line in lines:

            if "," not in line:
                continue

            raw = line.split(",")[0].strip()

            std = clean_name(raw)

            f.write(f"{raw} => {std}\n")

    print("频道名标准化完成 → duey.txt")
