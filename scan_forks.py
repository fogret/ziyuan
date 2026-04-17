import requests
import re
import os
import concurrent.futures
from datetime import datetime, timedelta

OWNER = "Guovin"
REPO = "iptv-api"
API = "https://api.github.com"

TOKEN = os.getenv("YONU")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "iptv-fork-scan",
    "Authorization": f"Bearer {TOKEN}"
}

# 最近 7 天
DAYS = 7
cutoff_date = datetime.utcnow() - timedelta(days=DAYS)

# 完整 URL 提取
URL_PATTERN = re.compile(r'https?://[^\s"\'<>]+')

def log(msg):
    with open("scan.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def log_result(msg):
    with open("result.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# 获取所有 fork
def get_forks():
    forks = []
    page = 1
    while True:
        url = f"{API}/repos/{OWNER}/{REPO}/forks?per_page=100&page={page}"
        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            log("获取 forks 失败：" + r.text)
            break
        data = r.json()
        if not data:
            break
        forks.extend(data)
        page += 1
    return forks

# 判断 fork 是否在最近 7 天更新
def fork_recent(fork):
    date_str = fork["updated_at"]
    update_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    return update_date >= cutoff_date

# 获取 subscribe.txt
def fetch_subscribe(full_name):
    raw_url = f"https://raw.githubusercontent.com/{full_name}/master/config/subscribe.txt"
    try:
        r = requests.get(raw_url, timeout=(3, 3))
        if r.status_code != 200:
            return None
        return r.text
    except:
        return None

# 提取 URL（单文件去重）
def extract_urls(text):
    urls = URL_PATTERN.findall(text)
    return list(set(u.strip() for u in urls))

# 测试 URL（防卡死）
def test_url(url):
    try:
        r = requests.head(url, timeout=(3, 3))
        if r.status_code == 200:
            return True
    except:
        pass

    try:
        r = requests.get(url, timeout=(3, 3))
        return r.status_code == 200
    except:
        return False

def main():
    open("scan.log", "w").close()
    open("result.log", "w").close()

    log("=== 开始扫描所有 fork（极速 + 去重 + 防卡死） ===")

    forks = get_forks()
    log(f"共找到 {len(forks)} 个 fork")

    valid_forks = []
    all_urls = {}  # URL → 来源 fork

    for f in forks:
        full_name = f["full_name"]

        if not fork_recent(f):
            log(f"[{full_name}] 超过 7 天未更新，跳过")
            continue

        log(f"[{full_name}] 最近 7 天有更新，开始处理…")
        valid_forks.append(full_name)

        content = fetch_subscribe(full_name)
        if not content:
            log(f"[{full_name}] 无 subscribe.txt")
            continue

        urls = extract_urls(content)
        log(f"[{full_name}] 提取到 {len(urls)} 个 URL（单文件去重）")

        for u in urls:
            if u not in all_urls:  # 跨 fork 去重
                all_urls[u] = full_name

    log(f"共提取到 {len(all_urls)} 个唯一 URL（跨 fork 去重），开始测速…")

    final_urls = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(test_url, all_urls.keys())
        for url, ok in zip(all_urls.keys(), results):
            if ok:
                final_urls.append(url)
                log(f"[OK] {url}")
                log_result(f"{url}    # 来自 fork：{all_urls[url]}")
            else:
                log(f"[FAIL] {url}")

    final_urls = sorted(set(final_urls))  # 最终去重

    # 写入 projects.txt
    with open("projects.txt", "w", encoding="utf-8") as f:
        for fk in valid_forks:
            f.write(f"https://github.com/{fk}\n")

    # 写入 urls.txt
    with open("urls.txt", "w", encoding="utf-8") as f:
        for u in final_urls:
            f.write(u + "\n")

    log("=== 完成！已生成 projects.txt、urls.txt、scan.log、result.log（全部去重 + 防卡死） ===")

if __name__ == "__main__":
    main()
