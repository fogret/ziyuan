import requests
import re
import os
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

    # 写入当前仓库根目录文件
    with open("projects.txt", "w", encoding="utf-8") as f:
        f.write(f"# 更新时间：{now_str}\n")
        for fk in valid_forks:
            f.write(f"https://github.com/{fk}\n")

    with open("urls.txt", "w", encoding="utf-8") as f:
        f.write(f"# 更新时间：{now_str}\n")
        for u in final_urls:
            f.write(u + "\n")

    print("✅ 当前仓库已生成 projects.txt、urls.txt")
    print("=== 完成 ===")

if __name__ == "__main__":
    main()
