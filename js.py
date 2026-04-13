import os
import re
import requests

# 配置请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def parse_playlist(url):
    """解析m3u/m3u8播放列表，返回内部有效地址数量"""
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        content = resp.text
        # 匹配实际播放地址(排除注释行)
        lines = content.splitlines()
        count = 0
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and (line.endswith('.ts') or line.endswith('.m3u8')):
                count += 1
        return count
    except Exception as e:
        return 0

def count_all_urls(file_path='data.txt'):
    if not os.path.exists(file_path):
        print(f"[错误] 文件不存在: {file_path}")
        return

    url_pattern = re.compile(r'https?://[^\s]+', re.IGNORECASE)
    total_line_urls = 0
    total_inner = 0

    print(f"[日志] 开始读取文件： {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"[日志] 文件总行数: {len(lines)}")

        for idx, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            urls = url_pattern.findall(line)
            if not urls:
                continue

            line_url_count = len(urls)
            total_line_urls += line_url_count

            line_inner_count = 0
            for u in urls:
                line_inner_count += parse_playlist(u)
            total_inner += line_inner_count

            print(f"[日志] 第 {idx} 行 → 链接数:{line_url_count} 个, 内部播放地址:{line_inner_count} 个")

    print("\n" + "="*60)
    print(f"[最终统计] 外部链接总数: {total_line_urls} 个")
    print(f"[最终统计] 内部播放地址总数: {total_inner} 个")
    print("="*60)

if __name__ == "__main__":
    count_all_urls()
