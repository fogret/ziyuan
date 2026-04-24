import re
import os
import time
import tempfile
import subprocess
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

# ===================== 配置 =====================
TOKEN = os.getenv("YONU")
TARGET_OWNER = "fogret"
TARGET_REPO = "soute"
TARGET_FILE_PATH = "config/whitelist.txt"

# ===================== 本地配置 =====================
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

# 读取源
items = []
with open(INPUT_PATH, "r", encoding="utf-8", errors="ignore") as f:
    subs = [line.strip() for line in f if line.strip()]

for sub in subs:
    try:
        r = requests.get(sub, timeout=15)
        for line in r.text.splitlines():
            line = line.strip()
            m = line_pattern.match(line)
            if m:
                items.append((m.group(1).strip(), m.group(2).strip()))
            else:
                m2 = url_pattern.search(line)
                if m2:
                    items.append(("", m2.group()))
    except:
        continue

# 去重
unique = []
seen = set()
for n, u in items:
    if u not in seen:
        seen.add(u)
        unique.append((n, u))

# 测速
ip_data = {}
valid_ips = set()

with ThreadPoolExecutor(MAX_WORKERS) as executor:
    futures = {executor.submit(test_speed, u): (n, u) for n, u in unique}
    for fut in as_completed(futures):
        name, url = futures[fut]
        url, speed, delay, ok = fut.result()
        ip_match = ip_pattern.search(url)
        if not ip_match: continue
        ip = ip_match.group(1)
        if ip not in ip_data or speed > ip_data[ip]["speed"]:
            ip_data[ip] = {"name": name, "speed": speed}
        if ok and speed > 0:
            valid_ips.add(ip)

# 按速度排序
sorted_list = sorted(valid_ips, key=lambda x: ip_data[x]["speed"], reverse=True)

# 本地写入
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(sorted_list))

with open(INVALID_PATH, "w", encoding="utf-8") as f:
    for ip in sorted(ip_data, key=lambda x: ip_data[x]["speed"], reverse=True):
        d = ip_data[ip]
        f.write(f"{ip},#{d['name']},{d['speed']:.2f}MB/s\n")

# ===================== 推送函数（用你原版结构，只改文件名） =====================
def push_to_target_repo(final_urls, now_str):
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

            # 保留 [KEYWORDS] 以上内容，下面全部覆盖
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if line.strip() == "[KEYWORDS]":
                    break

            # 写入新内容
            new_lines += [
                "",
                f"# 更新时间：{now_str}（北京时间）",
                *final_urls,
                ""
            ]

            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines) + "\n")

            subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
            subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
            subprocess.run(["git", "add", TARGET_FILE_PATH], check=True)
            subprocess.run(["git", "commit", "-m", "Auto update whitelist"], check=True)
            subprocess.run(["git", "push", "origin", "HEAD"], check=True)
    except Exception as e:
        print(f"推送失败：{e}")

# ===================== 执行推送 =====================
if sorted_list:
    beijing_tz = timezone(timedelta(hours=8))
    now_str = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")
    push_to_target_repo(sorted_list, now_str)
    print("✅ 已推送到另一个仓库 fogret/soute")
else:
    print("无有效IP，不推送")
