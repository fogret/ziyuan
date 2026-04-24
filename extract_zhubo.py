import re
import os
import time
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===================== 配置 =====================
INPUT_PATH = "data.txt"          # 改这里
OUTPUT_PATH = "zhubo.txt"        # 不变
INVALID_PATH = "invalid.txt"     # 失效地址

# 匹配 RTP 转发地址
pattern = re.compile(r"http://\d+\.\d+\.\d+\.\d+:\d+/rtp/\S+", re.I)

# 测速超时（秒）
TIMEOUT = 8
MIN_SPEED_MB = 0.05
MAX_WORKERS = 80  # 并发80

all_links = set()
valid_results = []
invalid_links = []

# ===================== 日志函数 =====================
def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

# ===================== 测速 =====================
def test_speed(url):
    try:
        start = time.time()
        resp = requests.get(url, stream=True, timeout=TIMEOUT)
        chunk = next(resp.iter_content(1024 * 256))
        cost = time.time() - start
        size = len(chunk)
        speed_mb = (size / 1024 / 1024) / cost if cost > 0 else 0
        delay_ms = int(cost * 1000)
        return url, speed_mb, delay_ms
    except Exception as e:
        return url, 0.0, -1

# ===================== 读取 data.txt 订阅 =====================
log(f"开始读取订阅：{INPUT_PATH}")
with open(INPUT_PATH, "r", encoding="utf-8", errors="ignore") as f:
    raw_urls = [line.strip() for line in f if line.strip()]
log(f"读取到 {len(raw_urls)} 个订阅源")

# ===================== 下载并提取频道地址 =====================
for sub in raw_urls:
    log(f"下载：{sub}")
    try:
        resp = requests.get(sub, timeout=15)
        found = pattern.findall(resp.text)
        for u in found:
            u = u.strip()
            if u:
                all_links.add(u)
    except Exception as e:
        log(f"下载失败：{sub} | {str(e)}")

log(f"去重完成，共 {len(all_links)} 条待测速")

# ===================== 并发80测速 =====================
sorted_links = sorted(all_links)
total = len(sorted_links)

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    future_to_url = {executor.submit(test_speed, url): url for url in sorted_links}
    for idx, future in enumerate(as_completed(future_to_url), 1):
        url, speed, delay = future.result()
        log(f"[{idx}/{total}] {url} | 延迟: {delay}ms | 速度: {speed:.2f}MB/s")

        if speed >= MIN_SPEED_MB and delay != -1:
            valid_results.append((speed, delay, url))
        else:
            invalid_links.append(url)

# ===================== 按速度排序 =====================
valid_results.sort(reverse=True, key=lambda x: x[0])

# ===================== 写入有效地址 =====================
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for sp, dl, url in valid_results:
        f.write(f"{url},# {sp:.2f}MB/s | {dl}ms\n")

# ===================== 写入失效地址 =====================
with open(INVALID_PATH, "w", encoding="utf-8") as f:
    for url in invalid_links:
        f.write(url + "\n")

log("=" * 60)
log(f"任务完成！有效源：{len(valid_results)} 条 | 失效源：{len(invalid_links)} 条")
log(f"有效地址：{OUTPUT_PATH}")
log(f"失效地址：{INVALID_PATH}")
log("=" * 60)
