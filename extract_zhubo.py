import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===================== 配置 =====================
INPUT_PATH = "data.txt"
OUTPUT_PATH = "zhubo.txt"
INVALID_PATH = "invalid.txt"

# 正则
pattern = re.compile(r"http://\d+\.\d+\.\d+\.\d+:\d+/rtp/\S+", re.I)
ip_pattern = re.compile(r"http://(\d+\.\d+\.\d+\.\d+):\d+", re.I)

TIMEOUT = 8
MAX_WORKERS = 80

# 简单国内省份前缀匹配（避免API限流）
province_map = {
    "111.": "北京", "114.": "北京", "106.": "北京",
    "113.58.": "海南", "113.": "广东",
    "110.178.": "山东", "112.192.": "山东",
    "111.196.": "河南", "123.118.": "河南",
    "36.": "上海", "39.": "上海",
    "42.": "湖北", "60.": "安徽", "124.": "辽宁",
    "171.8.": "贵州", "1.58.": "广西"
}

def get_province(ip):
    for prefix, prov in province_map.items():
        if ip.startswith(prefix):
            return prov
    return "未知"

# ===================== 日志 =====================
def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

# ===================== 测速 =====================
def test_speed(url):
    try:
        start = time.time()
        resp = requests.get(url, stream=True, timeout=TIMEOUT)
        chunk = next(resp.iter_content(1024 * 256))
        cost = time.time() - start
        speed = (len(chunk) / 1024 / 1024) / cost if cost > 0 else 0
        delay = int(cost * 1000)
        return url, speed, delay, True
    except:
        return url, 0.0, -1, False

# ===================== 读取订阅 =====================
all_urls = set()
with open(INPUT_PATH, "r", encoding="utf-8", errors="ignore") as f:
    subs = [line.strip() for line in f if line.strip()]

for sub in subs:
    log(f"下载：{sub}")
    try:
        txt = requests.get(sub, timeout=15).text
        urls = pattern.findall(txt)
        for u in urls:
            all_urls.add(u.strip())
    except:
        log(f"下载失败：{sub}")

log(f"共 {len(all_urls)} 个地址待测速")

# ===================== 测速 + IP去重 =====================
ip_info = {}  # 一个IP只保留一条记录
valid_ips = set()

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    future_map = {executor.submit(test_speed, url): url for url in all_urls}
    total = len(future_map)
    for idx, fut in enumerate(as_completed(future_map), 1):
        url, speed, delay, ok = fut.result()
        log(f"[{idx}/{total}] {url} | {speed:.2f}MB/s | {delay}ms")

        ip_match = ip_pattern.search(url)
        if not ip_match:
            continue
        ip = ip_match.group(1)

        # 同一个IP只保留最快的一条，自动去重
        if ip not in ip_info or speed > ip_info[ip][0]:
            prov = get_province(ip)
            ip_info[ip] = (speed, delay, prov)

        if ok and speed > 0:
            valid_ips.add(ip)

# ===================== 写入文件 =====================
# 白名单：纯IP
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for ip in sorted(valid_ips):
        f.write(ip + "\n")

# 有效+失效 去重后写入
with open(INVALID_PATH, "w", encoding="utf-8") as f:
    for ip in sorted(ip_info.keys()):
        speed, delay, prov = ip_info[ip]
        f.write(f"{ip},#{prov},{speed:.2f}MB/s,{delay}ms\n")

log("=" * 60)
log(f"完成！有效IP：{len(valid_ips)} | 总去重后：{len(ip_info)}")
log(f"白名单：{OUTPUT_PATH}")
log(f"全部结果（有效+失效）：{INVALID_PATH}")
log("=" * 60)
