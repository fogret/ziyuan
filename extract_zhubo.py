import re
import os
import time
import requests
from urllib.parse import urlparse

# ===================== 配置 =====================
INPUT_PATH = "urls.txt"
OUTPUT_PATH = "zhubo.txt"

# 匹配 RTP 转发地址
pattern = re.compile(r"http://\d+\.\d+\.\d+\.\d+:\d+/rtp/\S+", re.I)

# 测速超时（秒）
TIMEOUT = 8
# 最小有效速度，低于这个会被过滤
MIN_SPEED_MB = 0.05

all_links = set()
valid_results = []

# ===================== 日志函数 =====================
def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

# ===================== 简单测速 =====================
def test_speed(url):
    try:
        start = time.time()
        resp = requests.get(url, stream=True, timeout=TIMEOUT)
        chunk = next(resp.iter_content(1024 * 256))
        cost = time.time() - start
        size = len(chunk)
        speed_mb = (size / 1024 / 1024) / cost if cost > 0 else 0
        delay_ms = int(cost * 1000)
        return speed_mb, delay_ms
    except Exception as e:
        return 0.0, -1

# ===================== 读取订阅 =====================
log(f"开始读取订阅：{INPUT_PATH}")
with open(INPUT_PATH, "r", encoding="utf-8", errors="ignore") as f:
    raw_urls = [line.strip() for line in f if line.strip()]
log(f"读取到 {len(raw_urls)} 个订阅源")

# ===================== 下载提取 =====================
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

# ===================== 测速 =====================
for idx, url in enumerate(sorted(all_links), 1):
    speed, delay = test_speed(url)
    log(f"[{idx}/{len(all_links)}] {url} | 延迟: {delay}ms | 速度: {speed:.2f}MB/s")

    if speed >= MIN_SPEED_MB and delay != -1:
        valid_results.append((speed, delay, url))

# ===================== 按速度排序 =====================
valid_results.sort(reverse=True, key=lambda x: x[0])

# ===================== 写入文件 =====================
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for sp, dl, url in valid_results:
        f.write(f"{url},# {sp:.2f}MB/s | {dl}ms\n")

log("=" * 50)
log(f"任务完成！有效源：{len(valid_results)} 条")
log(f"已保存到：{OUTPUT_PATH}")
log("=" * 50)
