import requests
import re
import os
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone

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

DAYS = 7
cutoff_date = datetime.utcnow() - timedelta(days=DAYS)
URL_PATTERN = re.compile(r'https?://[^\s"\'<>]+')


def is_valid_stream(url):
    url = url.lower()
    allow_ext = (".m3u", ".m3u8", ".txt")
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


def push_to_target_repo(new_urls):
    try:
        repo_url = f"https://{TOKEN}@github.com/{TARGET_OWNER}/{TARGET_REPO}.git"

        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["git", "clone", repo_url, tmpdir], check=True, capture_output=True)
            os.chdir(tmpdir)

            file_path = TARGET_FILE_PATH
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

            # 北京时间
            beijing_tz = timezone(timedelta(hours=8))
            now = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")
            time_line = f"# 更新时间：{now}（北京时间）"

            # 组合文件内容
            new_content = "\n".join(top_lines) + "\n" + time_line + "\n" + "\n".join(new_urls) + "\n\n" + "\n".join(bottom_lines)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            # Git 提交
            subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
            subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
            subprocess.run(["git", "add", file_path], check=True)
            subprocess.run(["git", "commit", "-m", f"Update {now}"], check=True)
            subprocess.run(["git", "push", "origin", "HEAD"], check=True)

        log("✅ 已推送到 fogret/sourt/config/subscribe.txt")
    except Exception as e:
        log(f"❌ 推送失败：{str(e)}")


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
        log(f"[{full_name}] 最近7天内更新，处理中…")
        valid_forks.append(full_name)

        content = fetch_subscribe(full_name)
        if not content:
            log(f"[{full_name}] 无 subscribe.txt")
            continue

        urls = extract_urls(content)
        log(f"[{full_name}] 提取到 {len(urls)} 个URL")

        for u in urls:
            if not is_valid_stream(u):
                continue
            if u not in all_urls:
                all_urls[u] = full_name

    log(f"共提取 {len(all_urls)} 个URL，开始检测可用性…")
    final_urls = []

    import concurrent.futures
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

    # ================= 生成根目录两个文件 =================
    # 项目地址
    with open("projects.txt", "w", encoding="utf-8") as f:
        for fk in valid_forks:
            f.write(f"https://github.com/{fk}\n")

    # 链接地址
    with open("urls.txt", "w", encoding="utf-8") as f:
        for u in final_urls:
            f.write(u + "\n")
    # =====================================================

    if final_urls:
        push_to_target_repo(final_urls)
    else:
        log("⚠️ 无可用链接，不推送")

    log("=== 全部完成 ===")


if __name__ == "__main__":
    main()
