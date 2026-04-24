import re
import os
import time
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===================== 配置 =====================
INPUT_PATH = "data.txt"
OUTPUT_PATH = "zhubo.txt"
INVALID_PATH = "invalid.txt"

# 匹配 RTP 地址，提取纯 IP
pattern = re.compile(r"http://(\d+\.\d+\.\d+\.\d+):\d+/rtp/\S+", re.I)

# 测速配置
TIMEOUT = 8
MIN_SPEED_MB = 0.05
MAX_WORKERS = 80

all_links = set()
valid_results = []
invalid_links = []

# ===================== 日志函数 =====================
def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

# ===================== 简单获取省份 =====================
def get_province(ip):
    try:
        res = requests.get(f"https://ipapi.co/{ip}/region/", timeout=2)
        return res.text.strip() or "未知"
    except:
        return "未知"

# ===================== 测速 =====================
def test_speed(url):
    try:
        start = time.time()
        resp = requests.get(url, stream=True, timeout=TIMEOUT)
        chunk = next(resp.iter_content(1024 * 256))
        cost = time.time() - start
        speed_mb = (len(chunk) / 1024 / 1024) / cost if cost > 0 else 0
        delay_ms = int(cost * 1000)
        return url, speed_mb, delay_ms
    except Exception as e:
        return url, 0.0, -1

# ===================== 读取订阅 =====================
log(f"开始读取订阅：{INPUT_PATH}")
with open(INPUT_PATH, "r", encoding="utf-8", errors="ignore") as f:
    raw_urls = [line.strip() for line in f if line.strip()]
log(f"读取到 {len(raw_urls)} 个订阅源")

# ===================== 下载并提取【纯IP】 =====================
ip_set = set()
for sub in raw_urls:
    log(f"下载：{sub}")
    try:
        resp = requests.get(sub, timeout=15)
        matches = pattern.findall(resp.text)
        for ip in matches:
            ip_set.add(ip.strip())
    except Exception as e:
        log(f"下载失败：{sub}")

ip_list = sorted(ip_set)
log(f"去重完成，共 {len(ip_list)} 条IP待测速")

# ===================== 并发80测速 =====================
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    future_map = {executor.submit(test_speed, f"http://{ip}"): ip for ip in ip_list}
    total = len(future_map)
    for idx, future in enumerate(as_completed(future_map), 1):
        ip = future_map[future]
        url, speed, delay = future.result()
        log(f"[{idx}/{total}] {ip} | 延迟: {delay}ms | 速度: {speed:.2f}MB/s")

        province = get_province(ip)
        if speed >= MIN_SPEED_MB and delay != -1:
            # 白名单格式：纯IP
            valid_results.append(ip)
            # 备注格式：IP,#省份,速度,延时
            with open("result_temp.txt", "a", encoding="utf-8") as f:
                f.write(f"{ip},#{province},{speed:.2f}MB/s,{delay}ms\n")
        else:
            invalid_links.append(ip)

# ===================== 写入白名单格式 zhubo.txt =====================
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for ip in valid_results:
        f.write(f"{ip}\n")

# ===================== 写入失效地址 =====================
with open(INVALID_PATH, "w", encoding="utf-8") as f:
    for ip in invalid_links:
        f.write(f"{ip}\n")

log("=" * 60)
log(f"任务完成！有效：{len(valid_results)} 条 | 失效：{len(invalid_links)} 条")
log(f"白名单格式：{OUTPUT_PATH}")
log(f"失效地址：{INVALID_PATH}")
log("=" * 60)
