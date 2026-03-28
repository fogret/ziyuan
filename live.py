import asyncio
import aiohttp
import datetime
import re

DATA_FILE = "data.txt"
OUT_FILE = "live.txt"

MAX_CONCURRENT = 50
TIMEOUT = 8

KEEP_MULTICAST = 5   # ⭐ 组播保留 5 条
KEEP_PUBLIC = 5      # ⭐ 公网保留 5 条

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

CHANNEL_MAP = {
    "CCTV1": ["CCTV-1","CCTV1","CCTV1综合"],
    "CCTV2": ["CCTV-2","CCTV2","CCTV2财经"],
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

def classify_channel(name):
    for cate, lst in CHANNEL_CATEGORIES.items():
        if name in lst:
            return cate
    return None

def is_multicast(url):
    return url.startswith("rtp://") or url.startswith("udp://") or "239." in url

def is_public(url):
    return url.startswith("http")

# ===========================
# 真实 HLS 分片测速
# ===========================
async def test_speed(session, url, sem):
    async with sem:
        try:
            # 1. 获取 m3u8
            async with session.get(url, timeout=TIMEOUT) as r:
                if r.status != 200:
                    return 999999
                text = await r.text()

            # 2. 找到第一个 ts 分片
            ts_list = [l.strip() for l in text.splitlines() if l.strip().endswith(".ts")]
            if not ts_list:
                return 999999

            ts_url = ts_list[0]
            if not ts_url.startswith("http"):
                base = url.rsplit("/",1)[0]
                ts_url = base + "/" + ts_url

            # 3. 下载 200KB 测速
            start = asyncio.get_event_loop().time()
            async with session.get(ts_url, timeout=TIMEOUT) as r:
                await r.content.read(200*1024)
            end = asyncio.get_event_loop().time()

            speed = int(200 / (end - start))  # KB/s
            return speed

        except:
            return 999999

# ===========================
# 主流程
# ===========================
async def main():
    urls = load_data()
    if not urls:
        print("❌ data.txt 为空")
        return

    sem = asyncio.Semaphore(MAX_CONCURRENT)

    async with aiohttp.ClientSession(headers=HEADERS) as session:

        # ======================
        # 1. 抓取频道
        # ======================
        all_channels = []

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
                name = name.strip()
                link = link.strip()

                # 映射频道名
                for k, vs in CHANNEL_MAP.items():
                    if name in vs:
                        name = k
                        break

                all_channels.append((name, link))

        print(f"📺 抓到频道源：{len(all_channels)}")

        # ======================
        # 2. 真实测速
        # ======================
        print("🚀 开始真实 HLS 分片测速...")

        tasks = [test_speed(session, u, sem) for _, u in all_channels]
        speeds = await asyncio.gather(*tasks)

        all_channels = [(n, u, s) for (n, u), s in zip(all_channels, speeds)]

        # ======================
        # 3. 分类 + 组播/公网分开排序
        # ======================
        result = {c: [] for c in CHANNEL_CATEGORIES}

        for name, url, speed in all_channels:
            cate = classify_channel(name)
            if not cate:
                continue
            result[cate].append((name, url, speed))

        # ======================
        # 4. 输出
        # ======================
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        with open(OUT_FILE,"w",encoding="utf-8") as f:
            f.write(f"# 更新: {now}\n\n")

            for cate, ch_list in result.items():
                f.write(f"{cate},#genre#\n")

                # 组播
                multicast = sorted(
                    [x for x in ch_list if is_multicast(x[1])],
                    key=lambda x: x[2]
                )[:KEEP_MULTICAST]

                # 公网
                public = sorted(
                    [x for x in ch_list if is_public(x[1])],
                    key=lambda x: x[2]
                )[:KEEP_PUBLIC]

                final = multicast + public

                for name, url, speed in final:
                    f.write(f"{name}_HD264,{url}\n")

                f.write("\n")

        print("🎉 完成：live.txt 已生成（组播5 + 公网5）")

if __name__ == "__main__":
    asyncio.run(main())
