import asyncio
import aiohttp
import datetime
import re

DATA_FILE = "data.txt"
OUT_FILE_TXT = "live.txt"
OUT_FILE_M3U = "live.m3u"

MAX_CONCURRENT = 50
TIMEOUT = 8

HEADERS = {
    "User-Agent": "Dalvik/1.6.0 (Linux; U; Android 4.4.2; Build/KVT49L)"
}

# ===========================
# 频道分类
# ===========================
CCTV_ALL = [
    "CCTV1","CCTV2","CCTV3","CCTV4","CCTV5","CCTV5+","CCTV6",
    "CCTV7","CCTV8","CCTV9","CCTV10","CCTV11","CCTV12",
    "CCTV13","CCTV14","CCTV15","CCTV16","CCTV17"
]

WEISHI_ALL = [
    "湖南卫视","浙江卫视","江苏卫视","东方卫视","北京卫视",
    "广东卫视","广西卫视","东南卫视","海南卫视","河北卫视",
    "河南卫视","湖北卫视","江西卫视","四川卫视","重庆卫视",
    "云南卫视","天津卫视","安徽卫视","山东卫视","辽宁卫视",
    "黑龙江卫视","吉林卫视","内蒙古卫视","宁夏卫视","山西卫视",
    "陕西卫视","甘肃卫视","青海卫视","新疆卫视","西藏卫视"
]

GUIZHOU_LOCAL = [
    "贵州卫视","贵州公共","贵州影视文艺","贵州大众生活",
    "贵州生态乡村","贵州科教健康","贵州经济"
]

CHANNEL_CATEGORIES = {
    "央视频道": CCTV_ALL,
    "全国卫视": WEISHI_ALL,
    "贵州地方": GUIZHOU_LOCAL
}

# 强力频道名纠正规则
CHANNEL_MAP = {
    "CCTV1": ["CCTV-1","CCTV1","CCTV1综合","CCTV1HD","CCTV-1综合频道"],
    "CCTV2": ["CCTV-2","CCTV2","CCTV2财经","CCTV2HD"],
    "CCTV3": ["CCTV-3","CCTV3","CCTV3综艺"],
    "CCTV4": ["CCTV-4","CCTV4","CCTV4中文国际"],
    "CCTV5": ["CCTV-5","CCTV5","CCTV5体育"],
    "CCTV5+": ["CCTV-5+","CCTV5+","CCTV5+赛事"],
    "CCTV6": ["CCTV-6","CCTV6","CCTV6电影"],
    "CCTV7": ["CCTV-7","CCTV7","CCTV7国防军事"],
    "CCTV8": ["CCTV-8","CCTV8","CCTV8电视剧"],
    "CCTV9": ["CCTV-9","CCTV9","CCTV9纪录"],
    "CCTV10": ["CCTV-10","CCTV10","CCTV10科教"],
    "CCTV11": ["CCTV-11","CCTV11","CCTV11戏曲"],
    "CCTV12": ["CCTV-12","CCTV12","CCTV12社会与法"],
    "CCTV13": ["CCTV-13","CCTV13","CCTV13新闻"],
    "CCTV14": ["CCTV-14","CCTV14","CCTV14少儿"],
    "CCTV15": ["CCTV-15","CCTV15","CCTV15音乐"],
    "CCTV16": ["CCTV-16","CCTV16","CCTV16奥林匹克"],
    "CCTV17": ["CCTV-17","CCTV17","CCTV17农业农村"],
    "贵州卫视": ["贵州卫视","贵州"]
}

# ===========================
# 工具函数
# ===========================
def load_data():
    try:
        with open(DATA_FILE,"r",encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]
    except:
        return []

def fix_url(url):
    if not url:
        return None
    if url.startswith(("javascript:", "data:", "blob:", "about:", "null")):
        return None
    if url.startswith("http://") or url.startswith("https://") or url.startswith("rtmp://") or url.startswith("rtp://") or url.startswith("udp://"):
        return url
    if re.match(r"^\d+\.\d+\.\d+\.\d+", url):
        return "http://" + url
    return url

def normalize_name(name):
    for k, vs in CHANNEL_MAP.items():
        for v in vs:
            if v in name:
                return k
    return name.strip()

def classify_channel(name):
    for cate, lst in CHANNEL_CATEGORIES.items():
        if name in lst:
            return cate
    return None

# ===========================
# 主流程
# ===========================
async def main():
    urls = load_data()
    if not urls:
        print("❌ data.txt 为空", flush=True)
        return

    async with aiohttp.ClientSession(headers=HEADERS) as session:

        all_channels = []

        print("📡 开始抓取频道源...", flush=True)

        for api in urls:
            try:
                async with session.get(api, timeout=TIMEOUT) as r:
                    text = await r.text()
            except:
                continue

            for line in text.splitlines():
                if "," not in line:
                    continue

                name, link = line.split(",",1)
                name = normalize_name(name.strip())
                link = fix_url(link.strip())

                if not link:
                    continue

                all_channels.append((name, link))

        print(f"📺 抓到频道源：{len(all_channels)}", flush=True)

        # 去重（同名频道保留不同 URL）
        unique = {}
        for name, url in all_channels:
            unique.setdefault(name, set()).add(url)

        # 分类
        result = {c: [] for c in CHANNEL_CATEGORIES}

        for name, urls in unique.items():
            cate = classify_channel(name)
            if not cate:
                continue
            for u in urls:
                result[cate].append((name, u))

        # 排序 + 每类保留 5 条
        for cate in result:
            result[cate] = sorted(result[cate], key=lambda x: x[0])[:5]

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        # ===========================
        # 输出 TXT
        # ===========================
        with open(OUT_FILE_TXT,"w",encoding="utf-8") as f:
            f.write(f"# 更新: {now}\n\n")
            for cate, ch_list in result.items():
                f.write(f"{cate},#genre#\n")
                for name, url in ch_list:
                    f.write(f"{name},{url}\n")
                f.write("\n")

        # ===========================
        # 输出 M3U（TVBox 标准格式 A）
        # ===========================
        with open(OUT_FILE_M3U,"w",encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for cate, ch_list in result.items():
                for name, url in ch_list:
                    f.write(f'#EXTINF:-1 tvg-name="{name}" group-title="{cate}",{name}\n')
                    f.write(f"{url}\n")

        print("🎉 完成：live.txt + live.m3u 已生成（每类保留 5 条）", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
