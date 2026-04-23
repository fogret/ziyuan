import requests
import re
import os
import subprocess
import tempfile
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
from collections import defaultdict
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

DAYS = 7
cutoff_date = datetime.utcnow() - timedelta(days=DAYS)
URL_PATTERN = re.compile(r'https?://[^\s"\'<>]+')

# 代理清洗正则
PROXY_CLEAN_PAT = re.compile(
    r"^(https?://(ghfast\.top|ghproxy\.[^/]+|cdn\.jsdelivr\.net/gh|fastly\.jsdelivr\.net/gh)/)+",
    re.IGNORECASE
)

def clean_github_proxy(url: str) -> str:
    """剥离GH代理前缀"""
    return PROXY_CLEAN_PAT.sub("", url.strip())

def get_channel_set(text):
    """提取频道名集合，只用来判断内容重复"""
    ch_set = set()
    if not text:
        return ch_set
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "http", "https")):
            continue
        if "," in line:
            ch_set.add(line.split(",")[0].strip())
    return ch_set

def safe_unique_process(url_list):
    # 1. 去除代理
    clean_list = [clean_github_proxy(u) for u in url_list]

    # 2. 一模一样URL去重：重复只留1条（修复全删问题）
    unique_list = []
    seen_url = set()
    for link in clean_list:
        if link not in seen_url:
            seen_url.add(link)
            unique_list.append(link)

    # 3. 按域名/IP分组
    host_group = defaultdict(list)
    for link in unique_list:
        try:
            host = urlparse(link).netloc.lower()
        except:
            host = "other"
        host_group[host].append(link)

    final_list = []
    # 4. 同域名：仅判断频道是否重复，不比数量
    for host, links in host_group.items():
        keep = []
        for link in links:
            try:
                res = requests.get(link, timeout=5)
                if res.status_code != 200:
                    keep.append(link)
                    continue
                now_ch = get_channel_set(res.text)
                if not now_ch:
                    keep.append(link)
                    continue
                # 检测是否内容高度重复
                is_same = False
                for exist_link in keep:
                    exist_ch = get_channel_set(requests.get(exist_link, timeout=3).text)
                    if len(now_ch) == 0 or len(exist_ch) == 0:
                        continue
                    # 包含关系判定为重复
                    if now_ch.issubset(exist_ch) or exist_ch.issubset(now_ch):
                        is_same = True
                        break
                if not is_same:
                    keep.append(link)
            except:
                keep.append(link)
        final_list.extend(keep)
    return sorted(final_list)

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
    unique_map = {}
    for u in urls:
        raw_link = u.strip()
        if raw_link not in unique_map:
            unique_map[raw_link] = raw_link
    return list(unique_map.values())

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
            insert_part = [f"# 更新时间：{now_str}（北京时间）", *final_urls, ""]
            new_lines = header + insert_part + whitelist
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines) + "\n")
            subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
            subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
            subprocess.run(["git", "add", TARGET_FILE_PATH], check=True)
            subprocess.run(["git", "commit", "-m", "Auto update"], check=True)
            subprocess.run(["git", "push", "origin", "HEAD"], check=True)
    except Exception as e:
        print(f"推送失败：{e}")

# ===================== 主函数 =====================
def main():
    beijing_tz = timezone(timedelta(hours=8))
    now_str = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")
    forks = get_forks()
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
    url_list = list(all_urls.keys())
    # 核心处理
    url_list = safe_unique_process(url_list)
    final_urls = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(test_url, url): url for url in url_list}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                if future.result():
                    final_urls.append(url)
            except:
                pass
    final_urls = sorted(set(final_urls))
    # 保存文件
    with open("projects.txt", "w", encoding="utf-8") as f:
        f.write(f"# 更新时间：{now_str}（北京时间）\n")
        for fk in valid_forks:
            f.write(f"https://github.com/{fk}\n")
    with open("urls.txt", "w", encoding="utf-8") as f:
        f.write(f"# 更新时间：{now_str}（北京时间）\n")
        for u in final_urls:
            f.write(u + "\n")
    # 推送
    if final_urls:
        push_to_target_repo(final_urls, now_str)

if __name__ == "__main__":
    main()
