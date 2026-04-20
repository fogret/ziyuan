import requests
import re
import os
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===================== 配置 =====================
OWNER = "Guovin"
REPO = "iptv-api"
API = "https://api.github.com"
TOKEN = os.getenv("YONU")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "iptv-fork-scan",
    "Authorization": f"Bearer {TOKEN}"
}

# 目标仓库（推送到这里）
TARGET_OWNER = "fogret"
TARGET_REPO = "sourt"
TARGET_FILE_PATH = "config/subscribe.txt"

DAYS = 7
cutoff_date = datetime.utcnow() - timedelta(days=DAYS)
URL_PATTERN = re.compile(r'https?://[^\s"\'<>]+')

def is_valid_stream(url):
    url = url.lower()
    deny_exts = [
        ".m3u8", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
        ".php", ".html", ".htm", ".json", ".xml",
        ".zip", ".rar", ".7z", ".tar", ".gz",
        ".mp4", ".flv", ".ts"
    ]
    allow_exts = [".m3u", ".txt"]
    for ext in deny_exts:
        if ext in url:
            return False
    for ext in allow_exts:
        if ext in url:
            return True
    return False

def get_forks():
    forks = []
    page = 1
    while True:
        url = f"{API}/repos/{OWNER}/{REPO}/forks?per_page=100&page={page}"
        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            print("获取forks失败：", r.text)
            break
        data = r.json()
        if not data:
            break
        forks.extend(data)
        page += 1
    return forks

def fork_recent(fork):
    update_date = datetime.strptime(fork["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
    return update_date >= cutoff_date

def fetch_subscribe(full_name):
    raw_url = f"https://raw.githubusercontent.com/{full_name}/master/config/subscribe.txt"
    try:
        r = requests.get(raw_url, timeout=3)
        return r.text if r.status_code == 200 else None
    except:
        return None

def extract_urls(text):
    urls = URL_PATTERN.findall(text)
    return list(set(u.strip() for u in urls))

def test_url(url):
    try:
        r = requests.head(url, timeout=3)
        if r.status_code == 200:
            return True
    except:
        pass
    try:
        r = requests.get(url, timeout=3, stream=True)
        r.close()
        return r.status_code == 200
    except:
        return False

# ===================== 推送到目标仓库 =====================
def push_to_target_repo(final_urls, now_str):
    try:
        repo_url = f"https://{TOKEN}@github.com/{TARGET_OWNER}/{TARGET_REPO}.git"

        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["git", "clone", repo_url, tmpdir], check=True, capture_output=True)
            os.chdir(tmpdir)

            os.makedirs("config", exist_ok=True)
            file_path = TARGET_FILE_PATH

            header = []
            whitelist = []

            # 保留原有格式
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.read().splitlines(keepends=False)

                idx = None
                for i, line in enumerate(lines):
                    if line.strip() == "[WHITELIST]":
                        idx = i
                        break
                if idx is not None:
                    header = lines[:idx]
                    whitelist = lines[idx:]
                else:
                    header = lines
            else:
                header = [
                    "# 这是订阅源列表，每行一个订阅地址",
                    "# 支持设置UA：https://xxx.com/subscribe.m3u UA=\"xxx\"",
                    "# This is a list of subscription sources, with one subscription address per line",
                    "# Supports setting UA: https://xxx.com/subscribe.m3u UA=\"xxx\"",
                    ""
                ]
                whitelist = [
                    "",
                    "[WHITELIST]",
                    "# 以下是订阅源的白名单",
                    "# This is the whitelist"
                ]

            # 写入北京时间更新时间 + urls.txt 的内容
            time_line = f"# 更新时间：{now_str}（北京时间）"
            new_content = "\n".join(header).rstrip() + "\n" + time_line + "\n" + "\n".join(final_urls) + "\n" + "\n".join(whitelist)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content.strip() + "\n")

            # Git 提交
            subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
            subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
            subprocess.run(["git", "add", TARGET_FILE_PATH], check=True)
            subprocess.run(["git", "commit", "-m", "Auto update subscribe.txt"], check=True)
            subprocess.run(["git", "push", "origin", "HEAD"], check=True)

        print("✅ 推送成功：fogret/sourt/config/subscribe.txt")
    except Exception as e:
        print(f"❌ 推送失败：{e}")

# ===================== 主函数 =====================
def main():
    beijing_tz = timezone(timedelta(hours=8))
    now_str = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")

    print("=== 开始扫描fork ===")
    forks = get_forks()
    print(f"总fork数：{len(forks)}")

    valid_forks = []
    all_urls = {}

    for f in forks:
        full_name = f["full_name"]
        if not fork_recent(f):
            continue
        valid_forks.append(full_name)
        text = fetch_subscribe(full_name)
        if not text:
            continue
        urls = extract_urls(text)
        for u in urls:
            if is_valid_stream(u):
                all_urls[u] = full_name

    print(f"提取URL数：{len(all_urls)}")
    final_urls = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(test_url, url): url for url in all_urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                if future.result():
                    final_urls.append(url)
            except:
                pass

    final_urls = sorted(set(final_urls))
    print(f"可用链接：{len(final_urls)}")

    # ===================== 写入当前仓库 =====================
    with open("projects.txt", "w", encoding="utf-8") as f:
        f.write(f"# 更新时间：{now_str}（北京时间）\n")
        for fk in valid_forks:
            f.write(f"https://github.com/{fk}\n")

    with open("urls.txt", "w", encoding="utf-8") as f:
        f.write(f"# 更新时间：{now_str}（北京时间）\n")
        for u in final_urls:
            f.write(u + "\n")

    print("✅ 当前仓库已生成 projects.txt、urls.txt")

    # ===================== 推送到另一个仓库 =====================
    if final_urls:
        push_to_target_repo(final_urls, now_str)
    else:
        print("⚠️ 无可用链接")

    print("=== 完成 ===")

if __name__ == "__main__":
    main()
