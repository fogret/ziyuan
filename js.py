import requests
import re
import sys
import time

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    sys.stdout.write(f"[{ts}] {msg}\n")
    sys.stdout.flush()

OWNER = "Guovin"
REPO = "iptv-apifoak"   # ← 修正仓库名

def get_branches():
    log("正在获取所有分支...")
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/branches"
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        log("❌ 获取分支失败")
        return []
    branches = [b["name"] for b in r.json()]
    log(f"✔ 发现分支：{branches}")
    return branches

def fetch_subscribe(branch):
    # ← 修正路径 sourt/config/subscribe.txt
    raw_url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{branch}/sourt/config/subscribe.txt"
    log(f"  → 尝试读取：{raw_url}")
    try:
        r = requests.get(raw_url, timeout=10)
        if r.status_code == 200:
            log("    ✔ 找到 subscribe.txt")
            return r.text
        else:
            log("    ❌ 未找到")
    except:
        log("    ⚠ 请求失败")
    return ""

def extract_urls(text):
    pattern = r'https?://[^\s]+'
    return re.findall(pattern, text)

def main():
    log("===== js.py 开始运行 =====")

    branches = get_branches()
    all_urls = []

    for br in branches:
        log(f"\n扫描分支：{br}")
        content = fetch_subscribe(br)

        if not content:
            log("  ⚠ 跳过（无内容）")
            continue

        urls = extract_urls(content)
        if urls:
            log(f"  ✔ 提取到 {len(urls)} 个地址")
            all_urls.extend(urls)
        else:
            log("  ⚠ 未找到 URL")

    log("\n正在去重...")
    all_urls = list(dict.fromkeys(all_urls))
    log(f"✔ 去重后剩余 {len(all_urls)} 个地址")

    with open("all_subscribe_urls.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(all_urls))

    log("✔ 已保存到 all_subscribe_urls.txt")
    log("===== js.py 运行结束 =====")

if __name__ == "__main__":
    main()
