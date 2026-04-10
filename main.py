import requests
import re

def extract_channel_names():
    url = "https://raw.githubusercontent.com/Jsnzkpg/Jsnzkpg/Jsnzkpg/Jsnzkpg1.m3u"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        lines = resp.text.splitlines()

        channels = []
        for line in lines:
            line = line.strip()
            if line.startswith("#EXTINF"):
                # 取逗号后面的频道名
                parts = line.split(",", 1)
                if len(parts) == 2:
                    name = parts[1].strip()
                    if name:
                        channels.append(name)

        # 去重
        channels = list(dict.fromkeys(channels))

        # 写入当前目录 yings.txt
        with open("yings.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(channels))

        print(f"成功提取 {len(channels)} 个频道名，已保存到 yings.txt")

    except Exception as e:
        print("获取失败：", e)
        print("可能是网络问题，可以手动复制m3u内容保存为 Jsnzkpg1.m3u 放同目录，我再给你读本地文件的版本")

if __name__ == "__main__":
    extract_channel_names()
