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

DAYS = 7
cutoff_date = datetime.utcnow() - timedelta(days=DAYS)

URL_PATTERN = re.compile(r'https?://[^\s"\'<>]+')


# ★ 你要求：只要 m3u / m3u8 / txt，其它全部不要
def is_valid_stream(url):
    url = url.lower()

    # 允许的 IPTV 格式
    allow_ext = (".m3u", ".m3u8", ".txt")

    # 禁止的所有其它格式
    deny_ext = (
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
        ".php", ".html", ".htm", ".json", ".xml",
        ".zip", ".rar", ".7z", ".tar", ".gz",
        ".mp4", ".flv", ".ts"
    )

    if url.endswith(deny_ext):
        return False

    if url.endswith(allow_ext):
        return True

    # 特殊情况：有些 IPTV 链接没有后缀，但以 /live/ 结尾
    if "/live/" in url:
        return True

    return False


def log(msg):
    with open("scan.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)


def log_result(msg):
    with open("result.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")


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
    open("scan.log", "w").close()
    open("result.log", "w").close()

    log("=== 开始扫描所有 fork ===")

    forks = get_forks()
    log(f"共找到 {len(forks)} 个 fork")

    valid_forks = []
    all_urls = {}

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
        log(f"[{full_name}] 提取到 {len(urls)} 个 URL")

        for u in urls:
            if not is_valid_stream(u):
                continue
            if u not in all_urls:
                all_urls[u] = full_name

    log(f"共提取到 {len(all_urls)} 个 IPTV URL，开始测速…")

    final_urls = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(test_url, url): url for url in all_urls.keys()}

        for future in concurrent.futures.as_completed(futures, timeout=600):
            url = futures[future]
            try:
                ok = future.result(timeout=6)
                if ok:
                    final_urls.append(url)
                    log(f"[OK] {url}")
                    log_result(f"{url}    # 来自 fork：{all_urls[url]}")
                else:
                    log(f"[FAIL] {url}")
            except Exception:
                log(f"[TIMEOUT] {url}")

    final_urls = sorted(set(final_urls))

    with open("projects.txt", "w", encoding="utf-8") as f:
        for fk in valid_forks:
            f.write(f"https://github.com/{fk}\n")

    with open("urls.txt", "w", encoding="utf-8") as f:
        for u in final_urls:
            f.write(u + "\n")

    log("=== 完成 ===")


if __name__ == "__main__":
    main()
