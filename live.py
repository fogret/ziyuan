import asyncio
import aiohttp
import datetime
from urllib.parse import urljoin

# ================= 配置 =================
DATA_FILE = "data.txt"
OUT_FILE = "live.txt"
MAX_CONCURRENT = 150
TIMEOUT = 2
KEEP_PER_CHANNEL = 20

# ================= 频道列表 =================
# 央视全频道
CCTV_ALL = [
    "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV4欧洲", "CCTV4美洲",
    "CCTV5", "CCTV5+", "CCTV6", "CCTV7", "CCTV8", "CCTV9", "CCTV10",
    "CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15", "CCTV16", "CCTV17",
    "兵器科技", "风云音乐", "风云足球", "风云剧场", "怀旧剧场", "第一剧场",
    "女性时尚", "世界地理", "央视台球", "高尔夫网球", "央视文化精品",
    "卫生健康", "电视指南", "老故事", "中学生", "发现之旅", "书法频道",
    "国学频道", "环球奇观"
]

# 全国卫视完整列表
WEISHI_ALL = [
    "湖南卫视", "浙江卫视", "江苏卫视", "东方卫视", "北京卫视",
    "广东卫视", "广西卫视", "东南卫视", "海南卫视", "河北卫视",
    "河南卫视", "湖北卫视", "江西卫视", "四川卫视", "重庆卫视",
    "云南卫视", "天津卫视", "安徽卫视", "山东卫视", "辽宁卫视",
    "黑龙江卫视", "吉林卫视", "内蒙古卫视", "宁夏卫视", "山西卫视",
    "陕西卫视", "甘肃卫视", "青海卫视", "新疆卫视", "西藏卫视",
    "三沙卫视", "兵团卫视", "延边卫视", "安多卫视", "康巴卫视",
    "农林卫视", "山东教育卫视",
    "中国教育1台", "中国教育2台", "中国教育3台", "中国教育4台", "早期教育"
]

# 贵州本地频道（只保留这些）
GUIZHOU_LOCAL = [
    "贵州卫视", "贵州公共", "贵州影视文艺", "贵州大众生活",
    "贵州生态乡村", "贵州科教健康", "贵州经济"
]

CHANNEL_CATEGORIES = {
    "央视频道": CCTV_ALL,
    "全国卫视": WEISHI_ALL,
    "贵州地方": GUIZHOU_LOCAL
}

# 名称标准化映射
CHANNEL_MAP = {
    "CCTV1": ["CCTV-1", "CCTV1综合", "CCTV1HD", "CCTV-1 综合"],
    "CCTV2": ["CCTV-2", "CCTV2财经", "CCTV2HD", "CCTV-2 财经"],
    "CCTV3": ["CCTV-3", "CCTV3综艺", "CCTV3HD", "CCTV-3 综艺"],
    "CCTV4": ["CCTV-4", "CCTV4中文国际", "CCTV4HD"],
    "CCTV4欧洲": ["CCTV-4欧洲", "CCTV4欧洲HD"],
    "CCTV4美洲": ["CCTV-4美洲", "CCTV4美洲HD"],
    "CCTV5": ["CCTV-5", "CCTV5体育", "CCTV5HD"],
    "CCTV5+": ["CCTV-5+", "CCTV5+赛事", "CCTV5+HD"],
    "CCTV6": ["CCTV-6", "CCTV6电影", "CCTV6HD"],
    "CCTV7": ["CCTV-7", "CCTV7国防军事", "CCTV7HD"],
    "CCTV8": ["CCTV-8", "CCTV8电视剧", "CCTV8HD"],
    "CCTV9": ["CCTV-9", "CCTV9纪录", "CCTV9HD"],
    "CCTV10": ["CCTV-10", "CCTV10科教", "CCTV10HD"],
    "CCTV11": ["CCTV-11", "CCTV11戏曲", "CCTV11HD"],
    "CCTV12": ["CCTV-12", "CCTV12社会与法", "CCTV12HD"],
    "CCTV13": ["CCTV-13", "CCTV13新闻", "CCTV13HD"],
    "CCTV14": ["CCTV-14", "CCTV14少儿", "CCTV14HD"],
    "CCTV15": ["CCTV-15", "CCTV15音乐", "CCTV15HD"],
    "CCTV16": ["CCTV-16", "CCTV16奥林匹克", "CCTV16HD"],
    "CCTV17": ["CCTV-17", "CCTV17农业农村", "CCTV17HD"],
    "贵州卫视": ["贵州", "贵州卫视高清"],
}

# ================= 工具 =================
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]
    except:
        print("❌ 读取 data.txt 失败")
        return []

def is_valid_url(u):
    if not u.startswith("http"):
        return False
    bad = ["rtp://", "udp://", "239.", "192.168.", "10.", "16."]
    if any(x in u for x in bad):
        return False
    return any(ext in u for ext in [".m3u8", ".ts", ".flv"])

# ================= 异步 =================
async def check_api(ses, url, sem):
    async with sem:
        try:
            async with ses.get(url, timeout=TIMEOUT) as r:
                return url if r.status == 200 else None
        except:
            return None

async def get_channels(ses, url, sem):
    async with sem:
        try:
            async with ses.get(url, timeout=TIMEOUT) as r:
                data = await r.json()
                res = []
                for item in data.get("data", []):
                    n = item.get("name", "")
                    u = item.get("url", "")
                    if not n or not u or "," in u:
                        continue
                    if not u.startswith("http"):
                        u = urljoin(url, u)
                    for std, ali in CHANNEL_MAP.items():
                        if n in ali:
                            n = std
                            break
                    res.append((n, u))
                return res
        except:
            return []

# ================= 主逻辑 =================
async def main():
    print("🚀 开始生成直播源")
    lines = load_data()
    if not lines:
        return

    sem = asyncio.Semaphore(MAX_CONCURRENT)
    async with aiohttp.ClientSession() as ses:
        tasks = [check_api(ses, u, sem) for u in lines]
        ok_api = [x for x in await asyncio.gather(*tasks) if x]
        print(f"✅ 可用接口：{len(ok_api)}")

        tasks = [get_channels(ses, u, sem) for u in ok_api]
        all_ch = []
        for chunk in await asyncio.gather(*tasks):
            all_ch.extend(chunk)

        all_ch = [x for x in all_ch if is_valid_url(x[1])]
        print(f"📺 有效频道：{len(all_ch)}")

    cate = {c: [] for c in CHANNEL_CATEGORIES}
    for n, u in all_ch:
        for c_name, c_list in CHANNEL_CATEGORIES.items():
            if n in c_list:
                cate[c_name].append((n, u))
                break

    tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("更新时间,#genre#\n")
        f.write(f"{now},http://kakaxi.indevs.in/LOGO/Disclaimer.mp4\n\n")

        for c_name, c_list in CHANNEL_CATEGORIES.items():
            f.write(f"{c_name},#genre#\n")
            for ch in c_list:
                items = [x for x in cate[c_name] if x[0] == ch]
                for item in items[:KEEP_PER_CHANNEL]:
                    f.write(f"{item[0]},{item[1]}\n")

    print(f"🎉 完成：{OUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
