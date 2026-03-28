import asyncio
import aiohttp
import datetime
from urllib.parse import urljoin

# ================= 配置 =================
DATA_FILE = "data.txt"
OUT_FILE = "live.txt"
MAX_CONCURRENT = 100
TIMEOUT = 8
KEEP_PER_CHANNEL = 5

# 安卓4.4.2 UA
HEADERS = {
    "User-Agent": "Dalvik/1.6.0 (Linux; U; Android 4.4.2; Build/KVT49L)"
}

# ================= 频道列表 =================
CCTV_ALL = [
    "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV5", "CCTV5+", "CCTV6",
    "CCTV7", "CCTV8", "CCTV9", "CCTV10", "CCTV11", "CCTV12",
    "CCTV13", "CCTV14", "CCTV15", "CCTV16", "CCTV17"
]

WEISHI_ALL = [
    "湖南卫视", "浙江卫视", "江苏卫视", "东方卫视", "北京卫视",
    "广东卫视", "广西卫视", "东南卫视", "海南卫视", "河北卫视",
    "河南卫视", "湖北卫视", "江西卫视", "四川卫视", "重庆卫视",
    "云南卫视", "天津卫视", "安徽卫视", "山东卫视", "辽宁卫视",
    "黑龙江卫视", "吉林卫视", "内蒙古卫视", "宁夏卫视", "山西卫视",
    "陕西卫视", "甘肃卫视", "青海卫视", "新疆卫视", "西藏卫视"
]

GUIZHOU_LOCAL = [
    "贵州卫视", "贵州公共", "贵州影视文艺", "贵州大众生活",
    "贵州生态乡村", "贵州科教健康", "贵州经济"
]

CHANNEL_CATEGORIES = {
    "央视频道": CCTV_ALL,
    "全国卫视": WEISHI_ALL,
    "贵州地方": GUIZHOU_LOCAL
}

CHANNEL_MAP = {
    "CCTV1": ["CCTV-1", "CCTV1", "CCTV1综合"],
    "CCTV2": ["CCTV-2", "CCTV2", "CCTV2财经"],
    "CCTV3": ["CCTV-3", "CCTV3", "CCTV3综艺"],
    "CCTV4": ["CCTV-4", "CCTV4", "CCTV4中文国际"],
    "CCTV5": ["CCTV-5", "CCTV5", "CCTV5体育"],
    "CCTV5+": ["CCTV-5+", "CCTV5+", "CCTV5+赛事"],
    "CCTV6": ["CCTV-6", "CCTV6", "CCTV6电影"],
    "CCTV7": ["CCTV-7", "CCTV7", "CCTV7国防军事"],
    "CCTV8": ["CCTV-8", "CCTV8", "CCTV8电视剧"],
    "CCTV9": ["CCTV-9", "CCTV9", "CCTV9纪录"],
    "CCTV10": ["CCTV-10", "CCTV10", "CCTV10科教"],
    "CCTV11": ["CCTV-11", "CCTV11", "CCTV11戏曲"],
    "CCTV12": ["CCTV-12", "CCTV12", "CCTV12社会与法"],
    "CCTV13": ["CCTV-13", "CCTV13", "CCTV13新闻"],
    "CCTV14": ["CCTV-14", "CCTV14", "CCTV14少儿"],
    "CCTV15": ["CCTV-15", "CCTV15", "CCTV15音乐"],
    "CCTV16": ["CCTV-16", "CCTV16", "CCTV16奥林匹克"],
    "CCTV17": ["CCTV-17", "CCTV17", "CCTV17农业农村"],
    "贵州卫视": ["贵州卫视", "贵州"],
}

# ================= 工具 =================
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]
    except:
        return []

def is_valid(u):
    if not u.startswith("http"):
        return False
    if any(x in u for x in ["rtp://", "udp://", "239.", "192.168", "10."]):
        return False
    return any(e in u for e in [".m3u8", ".ts", ".m3u"])

# ================= 异步 =================
async def check(ses, url, sem):
    async with sem:
        try:
            async with ses.get(url, timeout=TIMEOUT, headers=HEADERS) as r:
                return url if r.status == 200 else None
        except:
            return None

async def grab(ses, url, sem):
    async with sem:
        try:
            async with ses.get(url, timeout=TIMEOUT, headers=HEADERS) as r:
                text = await r.text()
                res = []
                for line in text.splitlines():
                    line = line.strip()
                    if not line or "," not in line:
                        continue
                    parts = line.split(",", 1)
                    if len(parts) != 2:
                        continue
                    name = parts[0].strip()
                    urlx = parts[1].strip()
                    for k, vs in CHANNEL_MAP.items():
                        if name in vs or name == k:
                            name = k
                            break
                    res.append((name, urlx))
                return res
        except:
            return []

async def test_speed(ses, url, sem):
    async with sem:
        try:
            start = asyncio.get_event_loop().time()
            async with ses.head(url, timeout=3, headers=HEADERS) as r:
                if r.status in (200, 302):
                    return int((asyncio.get_event_loop().time() - start) * 1000)
        except:
            pass
        return 99999

# ================= 主函数 =================
async def main():
    urls = load_data()
    if not urls:
        print("❌ data.txt 为空")
        return

    sem = asyncio.Semaphore(MAX_CONCURRENT)
    async with aiohttp.ClientSession(headers=HEADERS) as ses:
        tasks = [check(ses, u, sem) for u in urls]
        ok = [x for x in await asyncio.gather(*tasks) if x]
        print(f"✅ 可用接口: {len(ok)}")

        tasks = [grab(ses, u, sem) for u in ok]
        all_ch = []
        for chunk in await asyncio.gather(*tasks):
            all_ch.extend(chunk)

        all_ch = [x for x in all_ch if is_valid(x[1])]
        print(f"📺 有效频道: {len(all_ch)}")

        # 测速
        print("🚀 开始测速...")
        speed_tasks = [test_speed(ses, u, sem) for n, u in all_ch]
        speeds = await asyncio.gather(*speed_tasks)
        all_ch = [(n, u, s) for (n, u), s in zip(all_ch, speeds)]

        # 去重：每个频道只保留最快一条
        ch_map = {}
        for n, u, s in sorted(all_ch, key=lambda x: x[2]):
            if n not in ch_map:
                ch_map[n] = (n, u, s)
        all_ch = list(ch_map.values())

    # 分类
    cate = {c: [] for c in CHANNEL_CATEGORIES}
    for n, u, s in all_ch:
        for c_name, c_list in CHANNEL_CATEGORIES.items():
            if n in c_list:
                cate[c_name].append((n, u, s))
                break

    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# 更新: {now}\n\n")
        for c_name, c_list in CHANNEL_CATEGORIES.items():
            f.write(f"{c_name},#genre#\n")
            for ch in c_list:
                items = [x for x in cate[c_name] if x[0] == ch]
                for item in items[:KEEP_PER_CHANNEL]:
                    title = f"{item[0]}_HD264"
                    f.write(f"{title},{item[1]}\n")
            f.write("\n")
    print("🎉 完成: live.txt")

if __name__ == "__main__":
    asyncio.run(main())
