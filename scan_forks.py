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

# 目标仓库
TARGET_OWNER = "fogret"
TARGET_REPO = "sourt"
TARGET_FILE_PATH = "config/subscribe.txt"

DAYS = 30  # 改为30天
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

# ===================== 新版：检查30天内每天都有提交 =====================
def has_daily_commits_for_30_days(full_name):
    try:
        now = datetime.utcnow()
        day_set = set()

        for page in range(1, 5):  # 最多查几页，避免API超限
            url = f"{API}/repos/{full_name}/commits?per_page=100&page={page}"
            r = requests.get(url, headers=HEADERS, timeout=5)
            if r.status_code != 200:
                break
            commits = r.json()
            if not commits:
                break

            for cm in commits:
                date_str = cm["commit"]["author"]["date"]
                dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                if dt < cutoff_date:
                    continue
                day_key = dt.strftime("%Y-%m-%d")
                day_set.add(day_key)

            # 提前满足就退出
            if len(day_set) >= DAYS:
                break

        return len(day_set) >= DAYS
    except Exception as e:
        return False

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

            # 读取原有内容
            lines = []
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = [line.rstrip("\n") for line in f]

            # 前5行原样保留
            header = lines[:5]

            # 白名单部分原样保留
            whitelist = []
            for i, line in enumerate(lines):
                if line.strip() == "[WHITELIST]":
                    whitelist = lines[i:]
                    break

            # 第6行开始：更新时间 + 最新链接
            insert_part = [
                f"# 更新时间：{now_str}（北京时间）",
                *final_urls,
                ""  # 空一行，隔开链接与白名单
            ]

            # 组合最终内容
            new_lines = header + insert_part + whitelist

            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines) + "\n")

            # Git 提交
            subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
            subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
            subprocess.run(["git", "add", TARGET_FILE_PATH], check=True)
            subprocess.run(["git", "commit", "-m", "Auto update"], check=True)
            subprocess.run(["git", "push", "origin", "HEAD"], check=True)

        print("✅ 推送成功：fogret/sourt/config/subscribe.txt")
    except Exception as e:
        print(f"❌ 推送失败：{e}")

# ===================== 主函数 =====================
def main():
    beijing_tz = timezone(timedelta(hours=8))
    now_str = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")

    print("=== 开始扫描fork（30天每日更新）===")
    forks = get_forks()
    print(f"总fork数：{len(forks)}")

    valid_forks = []
    all_urls = {}

    for f in forks:
        full_name = f["full_name"]

        # 新版：检查是否连续30天都有提交
        if not has_daily_commits_for_30_days(full_name):
            continue

        valid_forks.append(full_name)
        text = fetch_subscribe(full_name)
        if not text:
            continue
        urls = extract_urls(text)
        for u in urls:
            if is_valid_stream(u):
                all_urls[u] = full_name

    print(f"符合30天每日更新的fork：{len(valid_forks)}")
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

    # 写入当前仓库
    with open("projects.txt", "w", encoding="utf-8") as f:
        f.write(f"# 更新时间：{now_str}（北京时间）\n")
        for fk in valid_forks:
            f.write(f"https://github.com/{fk}\n")

    with open("urls.txt", "w", encoding="utf-8") as f:
        f.write(f"# 更新时间：{now_str}（北京时间）\n")
        for u in final_urls:
            f.write(u + "\n")

    print("✅ 当前仓库已生成 projects.txt、urls.txt")

    # 推送到另一个仓库
    if final_urls:
        push_to_target_repo(final_urls, now_str)
    else:
        print("⚠️ 无可用链接")

    print("=== 完成 ===")

if __name__ == "__main__":
    main()
