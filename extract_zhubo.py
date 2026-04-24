import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===================== 配置 =====================
INPUT_PATH = "data.txt"
OUTPUT_PATH = "zhubo.txt"
INVALID_PATH = "invalid.txt"

# 匹配 #频道名 或 频道名,地址 这类格式
line_pattern = re.compile(r'(.+?),(http://\d+\.\d+\.\d+\.\d+:\d+/rtp/\S+)', re.I | re.U)
url_pattern = re.compile(r'http://\d+\.\d+\.\d+\.\d+:\d+/rtp/\S+', re.I)
ip_pattern = re.compile(r'http://(\d+\.\d+\.\d+\.\d+):\d+', re.I)

TIMEOUT = 8
MAX_WORKERS = 80

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

# ===================== 读取订阅，提取 名称+地址 =====================
items = []
url_to_name = {}

with open(INPUT_PATH, "r", encoding="utf-8", errors="ignore") as f:
    subs = [line.strip() for line in f if line.strip()]

for sub in subs:
    log(f"下载：{sub}")
    try:
        r = requests.get(sub, timeout=15)
        text = r.text
        lines = text.splitlines()

        for line in lines:
            line = line.strip()
            # 匹配 频道名,http://...
            m = line_pattern.match(line)
            if m:
                name = m.group(1).strip()
                url = m.group(2).strip()
                items.append((name, url))
                url_to_name[url] = name
            else:
                # 只匹配到地址，名称留空
                m2 = url_pattern.search(line)
                if m2:
                    url = m2.group()
                    items.append(("", url))
                    url_to_name[url] = ""
    except Exception as e:
        log(f"下载失败：{sub}")

# 去重URL
unique_items = []
seen_url = set()
for name, url in items:
    if url not in seen_url:
        seen_url.add(url)
        unique_items.append((name, url))

log(f"去重后共 {len(unique_items)} 条待测速")

# ===================== 并发测速 =====================
ip_data = {}  # ip -> {name, speed, delay}
valid_ips = set()

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    future_to_url = {
        executor.submit(test_speed, url): (name, url)
        for name, url in unique_items
    }

    total = len(future_to_url)
    for idx, fut in enumerate(as_completed(future_to_url), 1):
        name, url = future_to_url[fut]
        url, speed, delay, ok = fut.result()
        log(f"[{idx}/{total}] {url} | {speed:.2f}MB/s | {delay}ms")

        ip_match = ip_pattern.search(url)
        if not ip_match:
            continue
        ip = ip_match.group(1)

        # 同一个IP只保留一条最好的
        if ip not in ip_data or speed > ip_data[ip]["speed"]:
            ip_data[ip] = {
                "name": name or "未知",
                "speed": speed,
                "delay": delay
            }

        if ok and speed > 0:
            valid_ips.add(ip)

# ===================== 写入文件 =====================
# 白名单纯IP
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for ip in sorted(valid_ips):
        f.write(ip + "\n")

# 有效+失效都写，去重，格式：IP,#名称,速度,延时
with open(INVALID_PATH, "w", encoding="utf-8") as f:
    for ip in sorted(ip_data.keys()):
        data = ip_data[ip]
        name = data["name"]
        speed = data["speed"]
        delay = data["delay"]
        f.write(f"{ip},#{name},{speed:.2f}MB/s,{delay}ms\n")

log("=" * 60)
log(f"完成！有效IP：{len(valid_ips)} | 去重后总条数：{len(ip_data)}")
log(f"白名单：{OUTPUT_PATH}")
log(f"有效+失效：{INVALID_PATH}")
log("=" * 60)
