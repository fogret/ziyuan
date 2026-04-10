import re

INPUT_FILE = "yings.txt"
OUTPUT_FILE = "duey.txt"

# 去除 emoji / 图标（不是目的，是为了不影响统一）
def remove_icons(name):
    emoji_pattern = re.compile(
        "[" 
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002700-\U000027BF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA70-\U0001FAFF"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub("", name).strip()

# 去掉无意义词
def remove_noise(name):
    noise = [
        "高清","HD","hd","4K","4k","超清","综合","频道","台",
        "直播","专区","专场","系列","轮播","超高清"
    ]
    for n in noise:
        name = name.replace(n, "")
    return name.strip()

# 标准化 CCTV
def normalize_cctv(name):
    up = name.upper()
    m = re.search(r"CCTV[-_ ]?0?(\d+)", up)
    if m:
        return f"CCTV-{m.group(1)}"
    if "CCTV" in up and "5+" in up:
        return "CCTV-5+"
    return None

# 标准化 卫视
def normalize_weishi(name):
    if "卫视" in name:
        return name[:name.index("卫视")+2]
    return None

# 标准化 数字频道
def normalize_digital(name):
    for k in ["咪视界","咪视通","BestTV","NewTV","SCTV","黑莓"]:
        if k in name:
            return k
    return None

# 标准化 港澳台
def normalize_hk(name):
    for k in ["TVB","凤凰","翡翠","明珠","澳视","台视","中视","华视","民视","ViuTV"]:
        if k in name:
            return k
    return None

# 标准化 国际台
def normalize_international(name):
    for k in ["CNN","BBC","NHK","TRT","DW","FOX","Global","News","Al Jazeera"]:
        if k.lower() in name.lower():
            return k.upper()
    return None

# 主标准化函数
def normalize(name):
    n = remove_icons(name)
    n = remove_noise(n)

    # CCTV
    cctv = normalize_cctv(n)
    if cctv:
        return cctv

    # 卫视
    ws = normalize_weishi(n)
    if ws:
        return ws

    # 港澳台
    hk = normalize_hk(n)
    if hk:
        return hk

    # 国际
    intl = normalize_international(n)
    if intl:
        return intl

    # 数字频道
    digi = normalize_digital(n)
    if digi:
        return digi

    # 默认：返回清洗后的原名
    return n

# 读取 yings.txt
def load_yings():
    out = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for raw in f:
            parts = [p.strip() for p in re.split(r"[,\s]+", raw) if p.strip()]
            out.extend(parts)
    return out

# 输出映射表
def write_output(mapping):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for original, standard in mapping:
            f.write(f"{original} => {standard}\n")

if __name__ == "__main__":
    yings = load_yings()
    mapping = []

    for name in yings:
        std = normalize(name)
        mapping.append((name, std))

    write_output(mapping)
    print("频道名标准化映射表已生成 → duey.txt")
