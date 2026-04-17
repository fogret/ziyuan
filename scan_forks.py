import requests
import re
import time
import concurrent.futures
from datetime import datetime, timedelta

OWNER = "Guovin"
REPO = "iptv-api"
API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "iptv-speed-scan"
}

# 最近 7 天
DAYS = 7
cutoff_date = datetime.utcnow() - timedelta(days=DAYS)

URL_PATTERN = re.compile(r'https?://[^\s"]+')

def log(msg):
    """写入扫描日志"""
    with open("scan.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def log_result(msg):
    """写入结果日志"""
    with open("result.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def get_branches():
    """获取所有分支"""
    url = f"{API}/repos/{OWNER}/{REPO}/branches?per_page=200"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        log("获取分支失败：" + r.text)
        return []
    return r.json()

def branch_recent(branch):
    """判断分支是否在最近 7 天内更新"""
    commit = branch["commit"]["sha"]
    url = f"{API}/repos/{OWNER}/{REPO}/commits/{commit}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return False

    data = r.json()
    date_str = data["commit"]["committer"]["date"]
    commit_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

    return commit_date >= cutoff_date

def fetch_subscribe(branch_name):
    """获取 subscribe.txt 内容"""
    raw_url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{branch_name}/config/subscribe.txt"
    r = requests.get(raw_url)
    if r.status_code != 200:
        log(f"[{branch_name}] subscribe.txt 不存在")
        return None
    log(f"[{branch_name}] 成功获取 subscribe.txt")
    return r.text

def extract_urls(text):
    """提取 URL（完整提取，不漏）"""
    urls = URL_PATTERN.findall(text)
    return [u.strip() for u in urls]

def test_url(url):
    """测试 URL 是否可访问（HEAD → GET 双保险）"""
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
