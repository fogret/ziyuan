import time

def beijing_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + 8*3600))

def main():
    # 这里输出你要写入 subscribe.txt 的内容
    print("# 自动测速结果（测试版）")
    print("# 时间：", beijing_time())
    print("https://example1.com/playlist.m3u")
    print("https://example2.com/playlist.m3u")
    print("https://example3.com/live.m3u8")

if __name__ == "__main__":
    main()
