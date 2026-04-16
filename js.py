import requests
import re

OWNER = "Guovin"
REPO = "iptv-api"

def get_branches():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/branches"
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return []
    return [b["name"] for b in r.json()]

def fetch_subscribe(branch):
    raw_url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{branch}/source/config/subscribe.txt"
    try:
        r = requests.get(raw_url, timeout=10)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return ""

def extract_urls(text):
    pattern = r'https?://[^\s]+'
    return re.findall(pattern, text)

def main():
    branches = get_branches()
    print("发现分支：", branches)

    all_urls = []

    for br in branches:
        print(f"\n扫描分支：{br}")
        content = fetch_subscribe(br)
        if not content:
            print("  ❌ 未找到 subscribe.txt")
            continue

        urls = extract_urls(content)
        if urls:
            print(f"  ✔ 找到 {len(urls)} 个地址")
            all_urls.extend(urls)
        else:
            print("  ⚠ subscribe.txt 中没有 URL")

    # 去重（保持顺序）
    all_urls = list(dict.fromkeys(all_urls))

    print("\n=== 去重后的总订阅地址 ===")
    for u in all_urls:
        print(u)

    with open("all_subscribe_urls.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(all_urls))

    print("\n已保存到 all_subscribe_urls.txt")

if __name__ == "__main__":
    main()
