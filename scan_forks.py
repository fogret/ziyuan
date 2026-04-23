import requests
import re
import os
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

# 强制实时输出日志
print = lambda *args, **kwargs: __builtins__['print'](*args, **kwargs, flush=True)

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

DAYS = 30
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
    print("【日志】开始获取 forks...")
    forks = []
    page = 1
    while True:
        url = f"{API}/repos/{OWNER}/{REPO}/forks?per_page=100&page={page}"
        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            print("【日志】获取forks失败：", r.text)
            break
        data = r.json()
        if not data:
            break
        forks.extend(data)
        print(f"【日志】已获取第 {page} 页，当前总数：{len(forks)}")
        page += 1
    print(f"【日志】获取 forks 完成，总数：{len(forks)}")
    return forks

def has_daily_commits_for_30_days(full_name):
    print(f"【日志】正在检查 30 天更新：{full_name}")
    try:
        now = datetime.utcnow()
        day_set = set()

        for page in range(1, 5):
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

            if len(day_set) >= DAYS:
                break

        ok = len(day_set) >= DAYS
        print(f"【日志】{full_name} 30 天更新天数：{len(day_set)} → {'符合' if ok else '不符合'}")
        return ok
    except Exception as e:
        print(f"【日志】{full_name} 检查出错：{e}")
        return False

def fetch_subscribe(full_name):
    print(f"【日志】拉取 subscribe.txt：{full_name}")
    raw_url = f"https://raw.githubusercontent.com/{full_name}/master/config/subscribe.txt"
    try:
        r = requests.get(raw_url, timeout=3)
        if r.status_code == 200:
            print(f"【日志】拉取成功：{raw_url}")
            return r.text
        else:
            print(f"【日志】拉取失败 {r.status_code}：{raw_url}")
            return None
    except Exception as e:
        print(f"【日志】拉取异常：{e}")
        return None

def extract_urls(text):
    urls = URL_PATTERN.findall(text)
    res = list(set(u.strip() for u in urls))
    print(f"【日志】提取到链接数：{len(res)}")
    return res

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
    print("【日志】开始推送至目标仓库")
    try:
        repo_url = f"https://{TOKEN}@github.com/{TARGET_OWNER}/{TARGET_REPO}.git"

        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["git", "clone", repo_url, tmpdir], check=True, capture_output=True)
            os.chdir(tmpdir)
            print("【日志】克隆仓库完成")

            os.makedirs("config", exist_ok=True)
            file_path = TARGET_FILE_PATH

            lines = []
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = [line.rstrip("\n") for line in f]

            header = lines[:5]
            whitelist = []
            for i, line in enumerate(lines):
                if line.strip() == "[WHITELIST]":
                    whitelist = lines[i:]
                    break

            insert_part = [
                f"# 更新时间：{now_str}（北京时间）",
                *final_urls,
                ""
            ]
            new_lines = header + insert_part + whitelist

            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines) + "\n")
            print("【日志】文件写入完成")

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

    print("\n========== 【日志】开始运行扫描任务 ==========")

    forks = get_forks()
    print(f"【日志】总 forks：{len(forks)}")

    valid_forks = []
    all_urls = {}

    for idx, f in enumerate(forks):
        full_name = f["full_name"]
        print(f"\n【日志】处理第 {idx+1}/{len(forks)} 个 fork：{full_name}")

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

    print(f"\n【日志】符合 30 天每日更新的仓库：{len(valid_forks)}")
    print(f"【日志】待测速链接总数：{len(all_urls)}")

    final_urls = []
    urls = list(all_urls.keys())
    total = len(urls)

    print("\n【日志】开始测速...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(test_url, url): url for url in all_urls}
        for i, future in enumerate(as_completed(future_to_url)):
            url = future_to_url[future]
            try:
                ok = future.result()
                print(f"【日志】测速进度 {i+1}/{total} | {url} → {'可用' if ok else '不可用'}")
                if ok:
                    final_urls.append(url)
            except Exception as e:
                print(f"【日志】测速失败 {url}：{e}")

    final_urls = sorted(set(final_urls))
    print(f"\n【日志】测速完成，最终可用链接：{len(final_urls)}")

    with open("projects.txt", "w", encoding="utf-8") as f:
        f.write(f"# 更新时间：{now_str}（北京时间）\n")
        for fk in valid_forks:
            f.write(f"https://github.com/{fk}\n")

    with open("urls.txt", "w", encoding="utf-8") as f:
        f.write(f"# 更新时间：{now_str}（北京时间）\n")
        for u in final_urls:
            f.write(u + "\n")

    print("【日志】当前文件已生成：projects.txt、urls.txt")

    if final_urls:
        push_to_target_repo(final_urls, now_str)
    else:
        print("【日志】无可用链接，跳过推送")

    print("\n========== 【日志】任务完成 ==========")

if __name__ == "__main__":
    main()
