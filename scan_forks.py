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
    """剥离GH代理前缀，返回原生链接"""
    return PROXY_CLEAN_PAT.sub("", url.strip())

def get_channel_name_set(text):
    """提取纯净频道名集合，用于对比是否重复"""
    channel_set = set()
    if not text:
        return channel_set
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith(("#", "http", "https")):
            continue
        if "," in s:
            name = s.split(",")[0].strip()
            if name:
                channel_set.add(name)
    return channel_set

# ========== 整合所有去重：代理去重+完全URL去重+同域名频道重复去重 ==========
def all_keep_unique(url_list):
    # 1. 统一去除代理
    clean_urls = [clean_github_proxy(u) for u in url_list]
    # 2. 完全相同URL去重（保留原有）
    unique_urls = list(dict.fromkeys(clean_urls))
    # 3. 按域名/IP分组
    host_group = defaultdict(list)
    for link in unique_urls:
        try:
            host = urlparse(link).netloc.lower()
        except:
            host = "other"
        host_group[host].append(link)

    final = []
    # 同域名内：只删频道重复的，频道不同全部保留
    for host, links in host_group.items():
        if len(links) == 1:
            final.append(links[0])
            continue

        temp = []
        for link in links:
            try:
                res = requests.get(link, timeout=5)
                if res.status_code != 200:
                    continue
                chs = get_channel_name_set(res.text)
                if not chs:
                    continue
                # 对比已保留列表，频道重复才丢弃
                repeat = False
                for exist in temp:
                    inter = chs & exist["chs"]
                    union = chs | exist["chs"]
                    if len(union) == 0:
                        continue
                    # 重合度过高判定为重复源
                    if len(inter) / len(union) >= 0.7:
                        repeat = True
                        break
                if not repeat:
                    temp.append({"url": link, "chs": chs})
            except:
                continue
        final.extend([item["url"] for item in temp])
    return sorted(final)

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

            insert_part = [
                f"# 更新时间：{now_str}（北京时间）",
                *final_urls,
                ""
            ]

            new_lines = header + insert_part + whitelist

            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines) + "\n")

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

    print(f"提取URL原始数量：{len(all_urls)}")
    url_list = list(all_urls.keys())

    # 统一入口：全部去重逻辑在这里，原有全部保留
    url_list = all_keep_unique(url_list)
    print(f"去代理+URL去重+同域名频道去重后：{len(url_list)}")

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
    print(f"最终可用链接数量：{len(final_urls)}")

    # 写入本地文件
    with open("projects.txt", "w", encoding="utf-8") as f:
        f.write(f"# 更新时间：{now_str}（北京时间）\n")
        for fk in valid_forks:
            f.write(f"https://github.com/{fk}\n")

    with open("urls.txt", "w", encoding="utf-8") as f:
        f.write(f"# 更新时间：{now_str}（北京时间）\n")
        for u in final_urls:
            f.write(u + "\n")

    print("✅ 已生成 projects.txt、urls.txt")

    # 推送仓库
    if final_urls:
        push_to_target_repo(final_urls, now_str)
    else:
        print("⚠️ 无可用链接，跳过推送")

    print("=== 执行完成 ===")

if __name__ == "__main__":
    main()
