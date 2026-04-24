import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===================== 配置 =====================
INPUT_PATH = "data.txt"
OUTPUT_PATH = "zhubo.txt"
INVALID_PATH = "invalid.txt"

# 匹配完整地址
pattern = re.compile(r"http://\d+\.\d+\.\d+\.\d+:\d+/rtp/\S+", re.I)
ip_pattern = re.compile(r"http://(\d+\.\d+\.\d+\.\d+):\d+", re.I)

TIMEOUT = 8
MAX_WORKERS = 80

# ===================== 日志 =====================
def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

# ===================== 省份 =====================
def get_province(ip):
    try:
        r = requests.get(f"https://ipapi.co/{ip}/region/", timeout=2)
        return r.text.strip() or "未知"
    except:
        return "未知"

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

# ===================== 并发测速 =====================
ip_set = set()
result_lines = []

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

        prov = get_province(ip)
        line = f"{ip},#{prov},{speed:.2f}MB/s,{delay}ms"
        result_lines.append(line)

        if ok and speed > 0:
            ip_set.add(ip)

# ===================== 输出文件 =====================
# 白名单：纯IP
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for ip in sorted(ip_set):
        f.write(ip + "\n")

# 有效+失效都写这里
with open(INVALID_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(result_lines))

log("=" * 60)
log(f"完成！有效IP：{len(ip_set)}")
log(f"白名单：{OUTPUT_PATH}")
log(f"全部结果（有效+失效）：{INVALID_PATH}")
log("=" * 60)
