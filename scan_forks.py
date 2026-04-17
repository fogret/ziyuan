import sys
import time
from datetime import datetime
import os

def beijing_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + 8*3600))

def log(msg):
    ts = beijing_time()
    sys.stdout.write(f"[{ts}] {msg}\n")
    sys.stdout.flush()

def main():
    log("===== 测试模式：不扫描 forks，只输出固定 URL =====")
    log(f"北京时间：{beijing_time()}")

    PROJECTS_PATH = "projects.txt"
    URLS_PATH = "urls.txt"

    # ⭐ 写项目地址文件（随便写一条）
    with open(PROJECTS_PATH, "w", encoding="utf-8") as f:
        f.write(f"# 更新时间（北京时间）：{beijing_time()}\n")
        f.write("https://github.com/fogret/test-project\n")

    # ⭐ 写 URL 文件（只写一条固定可访问的 URL）
    with open(URLS_PATH, "w", encoding="utf-8") as f:
        f.write(f"# 更新时间（北京时间）：{beijing_time()}\n")
        f.write("https://www.baidu.com\n")

    log(f"✔ 已保存 {PROJECTS_PATH}")
    log(f"✔ 已保存 {URLS_PATH}")
    log("===== 测试模式：已写入固定 URL =====")

if __name__ == "__main__":
    main()
