import re
import requests

headers = {
    "User-Agent": "Mozilla/5.0"
}

def count_inner(url):
    try:
        r = requests.get(url, timeout=10, headers=headers)
        r.raise_for_status()
        lines = r.text.splitlines()
        num = 0
        for line in lines:
            l = line.strip()
            if l and not l.startswith('#'):
                num += 1
        return num
    except Exception:
        return 0

def main():
    filename = "data.txt"
    pat = re.compile(r'https?://\S+')

    total_link = 0
    total_inner = 0

    print(f"[日志] 开始读取文件：{filename}")

    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"[日志] 文件总行数: {len(lines)}")

    for idx, line in enumerate(lines, 1):
        line = line.strip()
        urls = pat.findall(line)
        if not urls:
            continue

        total_link += len(urls)
        inner_sum = sum(count_inner(u) for u in urls)
        total_inner += inner_sum

        print(f"[日志] 第 {idx} 行 → 链接数:{len(urls)} 个, 内部播放地址:{inner_sum} 个")

    print("\n========================================")
    print(f"[最终统计] 外部链接总数: {total_link} 个")
    print(f"[最终统计] 内部播放地址总数: {total_inner} 个")
    print("========================================")

if __name__ == "__main__":
    main()
