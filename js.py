import os
import re

def count_playback_urls(file_path='data.txt'):
    """
    读取data.txt文件，统计各类播放地址数量
    """
    if not os.path.exists(file_path):
        print(f"[错误] 文件 {file_path} 不存在，请先创建该文件!")
        return 0, []
    
    # 匹配各类直播流地址
    url_pattern = re.compile(
        r'https?://[^\s]+(?:\.(?:m3u8?|txt|ts|flv|mp4)|/live/|/stream/)\b',
        re.IGNORECASE
    )
    
    valid_urls = []
    print(f"[日志] 开始读取文件: {os.path.abspath(file_path)}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            total_lines = len(lines)
            print(f"[日志] 文件总行数: {total_lines}")
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                found_urls = url_pattern.findall(line)
                if found_urls:
                    valid_urls.extend(found_urls)
                    print(f"[日志] 第 {line_num:4d} 行 → 找到 {len(found_urls)} 个播放地址")
    
    except Exception as e:
        print(f"[错误] 读取失败: {str(e)}")
        return 0, []
    
    print(f"\n{'='*50}")
    print(f"[最终统计] 有效播放地址总数: {len(valid_urls)} 个")
    print(f"{'='*50}")
    
    return len(valid_urls), valid_urls

if __name__ == "__main__":
    total_count, urls = count_playback_urls()
