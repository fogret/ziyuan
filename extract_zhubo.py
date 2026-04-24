import re
import os
import time
import tempfile
import subprocess
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

# ===================== 目标仓库配置 =====================
TOKEN = os.getenv("YONU")
TARGET_OWNER = "fogret"
TARGET_REPO = "soute"
TARGET_FILE_PATH = "config/whitelist.txt"

# ===================== 本地文件配置 =====================
INPUT_PATH = "data.txt"
OUTPUT_PATH = "zhubo.txt"
INVALID_PATH = "invalid.txt"

# ===================== 正则 =====================
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

# ===================== 读取订阅 =====================
items = []
with open(INPUT_PATH, "r", encoding="utf-8", errors="ignore") as f:
    subs = [line.strip() for line in f if line.strip()]

for sub in subs:
    log(f"下载：{sub}")
    try:
        r = requests.get(sub, timeout=15)
        lines = r.text.splitlines()
        for line in lines:
            line = line.strip()
            m = line_pattern.match(line)
            if m:
                name = m.group(1).strip()
                url = m.group(2).strip()
                items.append((name, url))
            else:
                m2 = url_pattern.search(line)
                if m2:
                    items.append(("", m2.group()))
    except Exception as e:
        log(f"下载失败：{sub}")

# URL去重
unique_items = []
seen_url = set()
for name, url in items:
    if url not in seen_url:
        seen_url.add(url)
        unique_items.append((name, url))

# ===================== 并发测速 =====================
ip_data = {}
valid_ips = set()

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    future_to_url = {executor.submit(test_speed, url): (name, url) for name, url in unique_items}
    total = len(future_to_url)
    for idx, fut in enumerate(as_completed(future_to_url), 1):
        name, url = future_to_url[fut]
        url, speed, delay, ok = fut.result()
        log(f"[{idx}/{total}] {url} | {speed:.2f}MB/s | {delay}ms")
        ip_match = ip_pattern.search(url)
        if not ip_match:
            continue
        ip = ip_match.group(1)
        if ip not in ip_data or speed > ip_data[ip]["speed"]:
            ip_data[ip] = {"name": name or "未知", "speed": speed, "delay": delay}
        if ok and speed > 0:
            valid_ips.add(ip)

# ===================== 按速度降序 =====================
sorted_ips = sorted(valid_ips, key=lambda ip: ip_data[ip]["speed"], reverse=True)

# ===================== 本地写入 =====================
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for ip in sorted_ips:
        f.write(ip + "\n")

with open(INVALID_PATH, "w", encoding="utf-8") as f:
    for ip in sorted(ip_data, key=lambda x: ip_data[x]["speed"], reverse=True):
        d = ip_data[ip]
        f.write(f"{ip},#{d['name']},{d['speed']:.2f}MB/s,{d['delay']}ms\n")

log("="*60)
log(f"本地完成：有效IP {len(sorted_ips)}")
log("="*60)

# ===================== 推送到另一个仓库：fogret/soute =====================
def push_whitelist(ips):
    try:
        repo_url = f"https://{TOKEN}@github.com/{TARGET_OWNER}/{TARGET_REPO}.git"
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["git", "clone", repo_url, tmpdir], check=True, capture_output=True)
            os.chdir(tmpdir)
            os.makedirs("config", exist_ok=True)

            tz = timezone(timedelta(hours=8))
            now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

            lines = []
            if os.path.exists(TARGET_FILE_PATH):
                with open(TARGET_FILE_PATH, "r", encoding="utf-8") as f:
                    lines = [l.rstrip("\n") for l in f]

            # 保留 [KEYWORDS] 以上，下面全部覆盖
            top = []
            found = False
            for line in lines:
                if line.strip() == "[KEYWORDS]":
                    top.append(line)
                    found = True
                    break
                top.append(line)
            if not found:
                top = ["[KEYWORDS]"]

            new_content = [
                *top,
                "",
                f"# 更新时间：{now_str}（北京时间）",
                *ips,
                ""
            ]

            with open(TARGET_FILE_PATH, "w", encoding="utf-8") as f:
                f.write("\n".join(new_content))

            subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
            subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
            subprocess.run(["git", "add", TARGET_FILE_PATH], check=True)
            subprocess.run(["git", "commit", "-m", "Auto update whitelist"], check=True)
            subprocess.run(["git", "push", "origin", "HEAD"], check=True)

        log("✅ 已推送到另一个仓库：fogret/soute")
    except Exception as e:
        log(f"❌ 推送失败：{e}")

if sorted_ips:
    push_whitelist(sorted_ips)
else:
    log("⚠️ 无有效IP，不推送")
