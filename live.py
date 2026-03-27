import asyncio
import aiohttp
import datetime
from urllib.parse import urljoin

# ================= 配置 =================
DATA_FILE = "data.txt"
OUT_FILE = "live.txt"
MAX_CONCURRENT = 100    # 调低一点，避免被封
TIMEOUT = 5             # 延长超时时间，提高成功率
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

# 贵州本地频道
GUIZHOU_LOCAL = [
    "贵州卫视", "贵州公共", "贵州影视文艺", "贵州大众生活",
    "贵州生态乡村", "贵州科教健康", "贵州经济"
]

CHANNEL_CATEGORIES = {
    "央视频道": CCTV_ALL,
    "全国卫视": WEISHI_ALL,
    "贵州地方": GUIZHOU_LOCAL
}

# 名称标准化映射（更宽松）
CHANNEL_MAP = {
    "CCTV1": ["CCTV-1", "CCTV1综合", "CCTV1HD", "CCTV-1 综合", "cctv1"],
    "CCTV2": ["CCTV-2", "CCTV2财经", "CCTV2HD", "CCTV-2 财经", "cctv2"],
    "CCTV3": ["CCTV-3", "CCTV3综艺", "CCTV3HD", "CCTV-3 综艺", "cctv3"],
    "CCTV4": ["CCTV-4", "CCTV4中文国际", "CCTV4HD", "CCTV-4 中文国际", "cctv4"],
    "CCTV4欧洲": ["CCTV-4欧洲", "CCTV4欧洲HD", "CCTV-4 欧洲", "cctv4欧洲"],
    "CCTV4美洲": ["CCTV-4美洲", "CCTV4美洲HD", "CCTV-4 美洲", "cctv4美洲"],
    "CCTV5": ["CCTV-5", "CCTV5体育", "CCTV5HD", "CCTV-5 体育", "cctv5"],
    "CCTV5+": ["CCTV-5+", "CCTV5+赛事", "CCTV5+HD", "CCTV5+体育赛事", "cctv5+"],
    "CCTV6": ["CCTV-6", "CCTV6电影", "CCTV6HD", "CCTV-6 电影", "cctv6"],
    "CCTV7": ["CCTV-7", "CCTV7国防军事", "CCTV7HD", "CCTV-7 国防军事", "cctv7"],
    "CCTV8": ["CCTV-8", "CCTV8电视剧", "CCTV8HD", "CCTV-8 电视剧", "cctv8"],
    "CCTV9": ["CCTV-9", "CCTV9纪录", "CCTV9HD", "CCTV-9 纪录", "cctv9"],
    "CCTV10": ["CCTV-10", "CCTV10科教", "CCTV10HD", "CCTV-10 科教", "cctv10"],
    "CCTV11": ["CCTV-11", "CCTV11戏曲", "CCTV11HD", "CCTV-11 戏曲", "cctv11"],
    "CCTV12": ["CCTV-12", "CCTV12社会与法", "CCTV12HD", "CCTV-12 社会与法", "cctv12"],
    "CCTV13": ["CCTV-13", "CCTV13新闻", "CCTV13HD", "CCTV-13 新闻", "cctv13"],
    "CCTV14": ["CCTV-14", "CCTV14少儿", "CCTV14HD", "CCTV-14 少儿", "cctv14"],
    "CCTV15": ["CCTV-15", "CCTV15音乐", "CCTV15HD", "CCTV-15 音乐", "cctv15"],
    "CCTV16": ["CCTV-16", "CCTV16奥林匹克", "CCTV16HD", "CCTV-16 奥林匹克", "cctv16"],
    "CCTV17": ["CCTV-17", "CCTV17农业农村", "CCTV17HD", "CCTV-17 农业农村", "cctv17"],
    "贵州卫视": ["贵州", "贵州卫视高清", "贵州卫视HD", "Guizhou TV"],
}

# ================= 工具函数 =================
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]
    except Exception as e:
        print(f"❌ 读取 data.txt 失败: {e}")
        return []

def is_valid_url(u):
    if not u.startswith("http"):
        return False
    # 放宽过滤：只过滤明显无效的地址
    bad = ["rtp://", "udp://", "rtsp://", "239.", "192.168.", "10.", "16."]
    if any(x in u for x in bad):
        return False
    return any(ext in u.lower() for ext in [".m3u8", ".ts", ".flv", ".mp4"])

# ================= 异步核心 =================
async def check_api(session, url, sem):
    async with sem:
        try:
            async with session.get(url, timeout=TIMEOUT) as resp:
                if resp.status == 200:
                    print(f"✅ 可用接口: {url}")
                    return url
                else:
                    print(f"❌ 接口失效: {url} (状态码: {resp.status})")
                    return None
        except Exception as e:
            print(f"❌ 接口访问失败: {url} ({str(e)[:50]})")
            return None

async def fetch_channels(session, url, sem):
    async with sem:
        try:
            async with session.get(url, timeout=TIMEOUT) as resp:
                data = await resp.json()
                res = []
                for item in data.get("data", []):
                    name = item.get("name", "").strip()
                    urlx = item.get("url", "").strip()
                    if not name or not urlx:
                        continue
                    if "," in urlx:
                        continue
                    if not urlx.startswith("http"):
                        urlx = urljoin(url, urlx)
                    # 宽松匹配：只要包含别名就算匹配
                    for std_name, aliases in CHANNEL_MAP.items():
                        if any(alias in name for alias in aliases):
                            name = std_name
                            break
                    res.append((name, urlx))
                print(f"📥 从 {url} 抓到 {len(res)} 条频道")
                return res
        except Exception as e:
            print(f"❌ 抓取频道失败: {url} ({str(e)[:50]})")
            return []

# ================= 主逻辑 =================
async def main():
    print("🚀 开始生成直播源...")
    base_urls = load_data()
    if not base_urls:
        print("❌ data.txt 为空或读取失败，请检查配置")
        return
    print(f"📄 加载到 {len(base_urls)} 个接口地址")

    sem = asyncio.Semaphore(MAX_CONCURRENT)
    async with aiohttp.ClientSession() as session:
        # 1. 检测可用接口
        print("🔍 开始检测可用接口...")
        tasks = [check_api(session, u, sem) for u in base_urls]
        valid_apis = [r for r in await asyncio.gather(*tasks) if r]
        print(f"\n✅ 最终可用接口: {len(valid_apis)} 个\n")

        if not valid_apis:
            print("❌ 没有可用接口，请更换 data.txt 里的地址")
            return

        # 2. 抓取所有频道
        print("📥 开始抓取频道数据...")
        tasks = [fetch_channels(session, u, sem) for u in valid_apis]
        all_channels = []
        for chunk in await asyncio.gather(*tasks):
            all_channels.extend(chunk)
        print(f"\n📺 原始抓到频道: {len(all_channels)} 条")

        # 3. 过滤有效地址
        valid_channels = [x for x in all_channels if is_valid_url(x[1])]
        print(f"✅ 过滤后有效频道: {len(valid_channels)} 条")

        if not valid_channels:
            print("❌ 没有有效频道，请检查接口地址或过滤规则")
            return

    # 4. 分类整理
    category_map = {cat: [] for cat in CHANNEL_CATEGORIES}
    for name, url in valid_channels:
        for cat, ch_list in CHANNEL_CATEGORIES.items():
            if name in ch_list:
                category_map[cat].append((name, url))
                break

    # 5. 写入输出文件（已去掉 MP4 链接）
    tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# 更新时间: {now}\n\n")
        for cat, ch_list in CHANNEL_CATEGORIES.items():
            f.write(f"{cat},#genre#\n")
            for ch in ch_list:
                items = [x for x in category_map[cat] if x[0] == ch]
                for item in items[:KEEP_PER_CHANNEL]:
                    f.write(f"{item[0]},{item[1]}\n")
            f.write("\n")

    print(f"\n🎉 完成！已生成 {OUT_FILE}，共 {len(valid_channels)} 条有效频道")

if __name__ == "__main__":
    asyncio.run(main())
