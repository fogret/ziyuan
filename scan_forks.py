import time
import sys

def beijing_time():
    """返回北京时间字符串"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + 8 * 3600))

def log(msg):
    """标准输出日志"""
    sys.stdout.write(f"[{beijing_time()}] {msg}\n")
    sys.stdout.flush()

def main():
    log("===== 生成 SUBSCRIBE 区域内容（最终测试版） =====")

    output_file = "subscribe_block.txt"

    # 你要写入 SUBSCRIBE 区域的内容（可随时改）
    subscribe_list = [
        "https://example1.com/playlist.m3u",
        "https://example2.com/playlist.m3u",
        "https://example3.com/live.m3u8"
    ]

    log("正在写入订阅源内容...")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# 自动更新订阅源（北京时间：{beijing_time()}）\n")
        f.write("# 以下内容将写入 [SUBSCRIBE] 区域\n")
        for url in subscribe_list:
            f.write(url + "\n")

    log(f"✔ 已生成文件：{output_file}")
    log("===== 完成 =====")

if __name__ == "__main__":
    main()
