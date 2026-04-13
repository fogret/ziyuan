import re
import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def get_inner_count(url):
    try:
        res = requests.get(url, headers=headers, timeout=8)
        res.raise_for_status()
        lines = res.text.splitlines()
        cnt = 0
        for line in lines:
            s = line.strip()
            if s and not s.startswith('#'):
                cnt += 1
        return cnt
    except:
        return 0

def main():
    path = "data.txt"
    url_re = re.compile(r'https?://\S+')

    total_url = 0
    total_inner = 0

    print(f"[日志] 开始读取文件：{path}")

    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"[日志] 文件总行数: {len(lines)}")

    for i, line in enumerate(lines, 1):
        line = line.strip()
        urls = url_re.findall(line)
        if not urls:
            continue

        total_url += len(urls)
        inner = sum(get_inner_count(u) for u in urls)
        total_inner += inner

        print(f"[日志] 第 {i} 行 → 链接数:{len(urls)} 个, 内部地址:{inner} 个")

    print("\n================================================")
    print(f"[最终统计] 外部链接总数: {total_url} 个")
    print(f"[最终统计] 内部播放地址总数: {total_inner} 个")
    print("================================================")

if __name__ == "__main__":
    main()
