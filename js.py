import os
import re

def count_playback_urls(file_path='data.txt'):
    if not os.path.exists(file_path):
        print(f"[错误] 文件 {file_path} 不存在!")
        return 0

    # 匹配http/https链接
    url_pattern = re.compile(r'https?://[^\s]+', re.IGNORECASE)
    # 匹配m3u8内部的播放地址(ts切片、二级m3u8)
    inner_url_pattern = re.compile(r'https?://[^\s]+(?:\.ts|\.m3u8)', re.IGNORECASE)

    valid_urls = []
    total_inner = 0
    print(f"[日志] 开始读取文件： {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            total_lines = len(lines)
            print(f"[日志] 文件总行数: {total_lines}")

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # 统计当前行外部链接数
                found_urls = url_pattern.findall(line)
                line_inner_count = 0

                if found_urls:
                    valid_urls.extend(found_urls)
                    # 解析每个链接内部包含的播放地址
                    for url in found_urls:
                        inner_count = len(inner_url_pattern.findall(url))
                        line_inner_count += inner_count

                    total_inner += line_inner_count
                    print(f"[日志] 第 {line_num:2d} 行 → 链接数:{len(found_urls)} 个, 内含播放地址:{line_inner_count} 个")

    except Exception as e:
        print(f"[错误] 读取失败: {str(e)}")
        return 0

    print("\n" + "="*60)
    print(f"[最终统计] 有效链接总数: {len(valid_urls)} 个")
    print(f"[最终统计] 所有链接内含播放地址总数: {total_inner} 个")
    print("="*60)

    return len(valid_urls), total_inner

if __name__ == "__main__":
    count_playback_urls()
