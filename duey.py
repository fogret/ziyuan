import re

# ============================
# 1. 标准化：CCTV / 卫视 / 画质后缀
# ============================
def normalize(name):
    n = name.strip()

    # 统一大小写
    up = n.upper()

    # --- CCTV 系列 ---
    # CCTV5+ / CCTV-5+ / CCTV5PLUS
    if "CCTV5+" in up or "CCTV-5+" in up or "CCTV5PLUS" in up:
        return "CCTV-5+"

    # CCTV 数字
    m = re.search(r"CCTV[-_ ]?0?(\d+)", up)
    if m:
        return f"CCTV-{m.group(1)}"

    # --- 卫视系列 ---
    if "卫视" in n:
        return n.replace("高清", "").replace("HD", "").replace("4K", "").strip()

    # --- CHC 系列 ---
    if n.startswith("CHC"):
        return re.sub(r"(高清|HD|超清)", "", n).strip()

    # --- CGTN 系列 ---
    if up.startswith("CGTN"):
        return n

    # --- 去掉画质后缀 ---
    n = re.sub(r"(高清|HD|4K|超清|频道|台)$", "", n).strip()

    return n


# ============================
# 2. 15 大类关键词
# ============================
CATEGORIES = {
    "央视频道": ["CCTV", "央视", "中央", "CGTN"],
    "付费频道": ["CHC", "风云", "第一剧场", "怀旧剧场", "女性时尚", "兵器科技", "电视指南"],
    "卫视频道": ["卫视"],
    "地方频道": [
        "新闻", "综合", "都市", "公共", "影视", "生活", "经济", "科教",
        "贵州","上海","北京","天津","重庆","广东","深圳","江苏","浙江","湖南","湖北",
        "安徽","江西","山东","山西","河南","河北","福建","厦门","四川","云南","广西",
        "海南","黑龙江","吉林","辽宁","内蒙古","宁夏","青海","甘肃","新疆","西藏"
    ],
    "影剧频道": ["电影", "影院", "剧场", "大片", "影"],
    "数字频道": ["数字", "高清", "超清", "4K", "8K"],
    "音乐频道": ["音乐", "MTV", "KTV", "歌"],
    "综娱频道": ["综艺", "娱乐", "秀"],
    "记录频道": ["纪录", "纪实", "探索", "地理"],
    "港澳频道": ["香港", "澳门", "TVB", "凤凰", "ViuTV"],
    "国际频道": ["BBC", "CNN", "NHK", "FOX", "HBO"],
    "少儿频道": ["少儿", "卡通", "亲子", "宝宝"],
    "动漫频道": ["动漫", "动画", "柯南", "火影", "海贼", "龙珠", "哆啦A梦"],
    "直播频道": ["体育", "赛事", "专场", "直播"],
    "游戏频道": ["LOL", "英雄联盟", "DOTA", "CF", "王者", "游戏"],
}


# ============================
# 3. 分类函数
# ============================
def classify(name):
    for cat, kws in CATEGORIES.items():
        for kw in kws:
            if kw in name:
                return cat
    return "未分类"


# ============================
# 4. 遍历 yings.txt → 提取频道
# ============================
def extract_channels():
    channels = []
    with open("yings.txt", "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            # 有逗号 → 多个频道
            if "," in line:
                parts = line.split(",")
            else:
                parts = [line]

            for p in parts:
                p = p.strip()
                # 跳过标题行（以：结尾）
                if p.endswith("："):
                    continue
                if p:
                    channels.append(p)
    return channels


# ============================
# 5. 主流程：标准化 → 分类
# ============================
def process():
    raw = extract_channels()
    result = {}

    for item in raw:
        clean = normalize(item)
        cat = classify(clean)

        if cat not in result:
            result[cat] = []
        if clean not in result[cat]:
            result[cat].append(clean)

    return result


# ============================
# 6. 输出 duey.txt（横向自动换行）
# ============================
def write_output(data):
    with open("duey.txt", "w", encoding="utf-8") as f:
        for cat, names in data.items():
            f.write(f"{cat}：\n")

            line = "  "
            for name in names:
                item = f"{name}, "
                if len(line) + len(item) > 40:
                    f.write(line.rstrip() + "\n")
                    line = "  " + item
                else:
                    line += item

            if line.strip():
                f.write(line.rstrip() + "\n")
            f.write("\n")


# ============================
# 7. 入口
# ============================
if __name__ == "__main__":
    data = process()
    write_output(data)
    print("分类完成 → duey.txt")
