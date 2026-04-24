import re
import os
import time
import tempfile
import subprocess
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

# ===================== 推送配置 =====================
TOKEN = os.getenv("YONU")
TARGET_OWNER = "fogret"
TARGET_REPO = "soute"
TARGET_FILE_PATH = "config/whitelist.txt"

# ===================== 推送函数（覆盖旧数据） =====================
def push_to_target_repo(final_ips, now_str):
    try:
        repo_url = f"https://{TOKEN}@github.com/{TARGET_OWNER}/{TARGET_REPO}.git"
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["git", "clone", repo_url, tmpdir], check=True, capture_output=True)
            os.chdir(tmpdir)
            os.makedirs("config", exist_ok=True)
            file_path = TARGET_FILE_PATH

            lines = []
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = [line.rstrip("\n") for line in f]

            # 保留 [KEYWORDS] 以上部分，下面全部覆盖
            top_lines = []
            found_keywords = False
            for line in lines:
                if line.strip() == "[KEYWORDS]":
                    top_lines.append(line)
                    found_keywords = True
                    break
                top_lines.append(line)

            # 新内容：仅有效IP，按速度从高到低
            new_lines = top_lines + [
                "",
                f"# 更新时间：{now_str}（北京时间）",
                *final_ips,
                ""
            ]

            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines) + "\n")

            subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
            subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
            subprocess.run(["git", "add", TARGET_FILE_PATH], check=True)
            subprocess.run(["git", "commit", "-m", "Auto update whitelist"], check=True)
            subprocess.run(["git", "push", "origin", "HEAD"], check=True)

        print("✅ 推送完成（已按速度排序并覆盖旧数据）")
    except Exception as e:
        print(f"❌ 推送失败：{e}")

# ===================== 测速代码 =====================
INPUT_PATH = "data.txt"
OUTPUT_PATH = "zhubo.txt"
INVALID_PATH = "invalid.txt"

line_pattern = re.compile(r'(.+?),(http://\d+\.\d+\.\d+\.\d+:\d+/rtp/\S+)', re.I | re.U)
url_pattern = re.compile(r'http://\d+\.\d+\.\d+\.\d+:\d+/rtp/\S+', re.I)
ip_pattern = re.compile(r'http://(\d+\.\d+\.\d+\.\d+):\d+', re.I)

TIMEOUT = 8
MAX_WORKERS = 80

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

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

unique_items = []
seen_url = set()
for name, url in items:
    if url not in seen_url:
        seen_url.add(url)
        unique_items.append((name, url))

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

# ===================== 关键：按速度从高到低排序 =====================
sorted_valid_ips = sorted(valid_ips, key=lambda ip: ip_data[ip]["speed"], reverse=True)

# 本地输出
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for ip in sorted_valid_ips:
        f.write(ip + "\n")

with open(INVALID_PATH, "w", encoding="utf-8") as f:
    for ip in sorted(ip_data, key=lambda x: ip_data[x]["speed"], reverse=True):
        d = ip_data[ip]
        f.write(f"{ip},#{d['name']},{d['speed']:.2f}MB/s,{d['delay']}ms\n")

log("="*60)
log(f"完成！有效IP：{len(valid_ips)}，已按测速速度降序排列")
log("="*60)

# ===================== 推送排序后的有效IP =====================
if valid_ips:
    tz = timezone(timedelta(hours=8))
    now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    push_to_target_repo(sorted_valid_ips, now_str)
else:
    print("无有效IP，不推送")
