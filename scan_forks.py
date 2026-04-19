import requests
import re
import os
import concurrent.futures
from datetime import datetime, timedelta, timezone

# 配置
OWNER = "Guovin"
REPO = "iptv-api"
API = "https://api.github.com"
TOKEN = os.getenv("YONU")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "iptv-fork-scan",
    "Authorization": f"Bearer {TOKEN}"
}

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
            print("获取 forks 失败：" + r.text)
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
        r = requests.get(raw_url, timeout=(3, 3))
        if r.status_code != 200:
            return None
        return r.text
    except:
        return None


def extract_urls(text):
    urls = URL_PATTERN.findall(text)
    return list(set(u.strip() for u in urls))


def test_url(url):
    try:
        r = requests.head(url, timeout=(3, 3))
        if r.status_code == 200:
            return True
    except:
        pass
    try:
        r = requests.get(url, timeout=(3, 3), stream=True)
        r.close()
        return r.status_code == 200
    except:
        return False


def main():
    beijing_tz = timezone(timedelta(hours=8))
    now_str = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")

    print("=== 开始扫描所有 fork ===")
    forks = get_forks()
    print(f"共找到 {len(forks)} 个 fork")

    valid_forks = []
    all_urls = {}

    for f in forks:
        full_name = f["full_name"]
        if not fork_recent(f):
            print(f"[{full_name}] 超过 7 天未更新，跳过")
            continue
        print(f"[{full_name}] 最近7天内更新，处理中…")
        valid_forks.append(full_name)

        content = fetch_subscribe(full_name)
        if not content:
            print(f"[{full_name}] 无 subscribe.txt")
            continue

        urls = extract_urls(content)
        print(f"[{full_name}] 提取到 {len(urls)} 个URL")

        for u in urls:
            if not is_valid_stream(u):
                continue
            if u not in all_urls:
                all_urls[u] = full_name

    print(f"共提取 {len(all_urls)} 个URL，开始检测可用性…")
    final_urls = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(test_url, url): url for url in all_urls.keys()}
        for future in concurrent.futures.as_completed(futures, timeout=600):
            url = futures[future]
            try:
                ok = future.result(timeout=6)
                if ok:
                    final_urls.append(url)
                    print(f"[OK] {url}")
                else:
                    print(f"[FAIL] {url}")
            except Exception:
                print(f"[TIMEOUT] {url}")

    final_urls = sorted(set(final_urls))

    # 写入 projects.txt
    with open("projects.txt", "w", encoding="utf-8") as f:
        f.write(f"# 更新时间：{now_str}（北京时间）\n")
        for fk in valid_forks:
            f.write(f"https://github.com/{fk}\n")

    # 写入 urls.txt
    with open("urls.txt", "w", encoding="utf-8") as f:
        f.write(f"# 更新时间：{now_str}（北京时间）\n")
        for u in final_urls:
            f.write(u + "\n")

    # 写入 config/subscribe.txt
    if final_urls:
        os.makedirs("config", exist_ok=True)
        file_path = "config/subscribe.txt"
        top_lines = []
        bottom_lines = []

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines(keepends=False)

            whitelist_idx = None
            for i, line in enumerate(lines):
                if line.strip() == "[WHITELIST]":
                    whitelist_idx = i
                    break

            top_lines = lines[:5]
            if whitelist_idx is not None:
                bottom_lines = lines[whitelist_idx:]

        time_line = f"# 更新时间：{now_str}（北京时间）"
        new_content = "\n".join(top_lines) + "\n" + time_line + "\n" + "\n".join(final_urls) + "\n\n" + "\n".join(bottom_lines)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("✅ 已写入本地 config/subscribe.txt")
    else:
        print("⚠️ 无可用链接，不生成")

    print("=== 全部完成 ===")


if __name__ == "__main__":
    main()
