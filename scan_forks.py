import requests
import re
import time
import os
import concurrent.futures
from datetime import datetime, timedelta

# 仓库信息
OWNER = "Guovin"
REPO = "iptv-api"

# GitHub API
API = "https://api.github.com"

# 从环境变量读取 Token（workflow 会注入 secrets.YONU）
TOKEN = os.getenv("YONU")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "iptv-speed-scan",
    "Authorization": f"Bearer {TOKEN}"
}

# 最近 7 天
DAYS = 7
cutoff_date = datetime.utcnow() - timedelta(days=DAYS)

# 完整 URL 提取（不漏、不截断）
URL_PATTERN = re.compile(r'https?://[^\s"\'<>]+')

# 日志函数
def log(msg):
    with open("scan.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def log_result(msg):
    with open("result.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# 获取所有分支
def get_branches():
    url = f"{API}/repos/{OWNER}/{REPO}/branches?per_page=200"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        log("获取分支失败：" + r.text)
        return []
    return r.json()

# 判断分支是否在最近 7 天更新
def branch_recent(branch):
    commit = branch["commit"]["sha"]
    url = f"{API}/repos/{OWNER}/{REPO}/commits/{commit}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return False

    data = r.json()
    date_str = data["commit"]["committer"]["date"]
    commit_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

    return commit_date >= cutoff_date

# 获取 subscribe.txt
def fetch_subscribe(branch_name):
    raw_url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{branch_name}/config/subscribe.txt"
    r = requests.get(raw_url)
    if r.status_code != 200:
        log(f"[{branch_name}] subscribe.txt 不存在")
        return None
    log(f"[{branch_name}] 成功获取 subscribe.txt")
    return r.text

# 提取 URL
def extract_urls(text):
    urls = URL_PATTERN.findall(text)
    return [u.strip() for u in urls]

# 测试 URL（HEAD → GET 双保险）
def test_url(url):
    try:
        r = requests.head(url, timeout=4)
        if r.status_code == 200:
            return True
    except:
        pass

    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except:
        return False

# 主程序
def main():
    # 清空日志
    open("scan.log", "w").close()
    open("result.log", "w").close()

    log("=== 开始扫描分支（极速 + 100% 准确率） ===")

    branches = get_branches()
    log(f"共找到 {len(branches)} 个分支")

    valid_branches = []
    all_urls = {}

    # 过滤最近 7 天分支
    for b in branches:
        name = b["name"]

        if not branch_recent(b):
            log(f"[{name}] 超过 7 天，跳过")
            continue

        log(f"[{name}] 在 7 天内更新，开始处理…")
        valid_branches.append(name)

        content = fetch_subscribe(name)
        if not content:
            continue

        urls = extract_urls(content)
        log(f"[{name}] 提取到 {len(urls)} 个 URL")

        for u in urls:
            all_urls[u] = name  # 记录来源分支

    log(f"共提取到 {len(all_urls)} 个唯一 URL，开始测速…")

    final_urls = []

    # 并发测速（10 线程）
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(test_url, all_urls.keys())
        for url, ok in zip(all_urls.keys(), results):
            if ok:
                final_urls.append(url)
                log(f"[OK] {url}")
                log_result(f"{url}    # 来自分支：{all_urls[url]}")
            else:
                log(f"[FAIL] {url}")

    final_urls.sort()

    # 写入 projects.txt（根目录）
    with open("projects.txt", "w", encoding="utf-8") as f:
        for br in valid_branches:
            f.write(f"https://github.com/{OWNER}/{REPO}/tree/{br}\n")

    # 写入 urls.txt（根目录）
    with open("urls.txt", "w", encoding="utf-8") as f:
        for u in final_urls:
            f.write(u + "\n")

    log("=== 完成！已生成 projects.txt、urls.txt、scan.log、result.log（全部在根目录） ===")

if __name__ == "__main__":
    main()
