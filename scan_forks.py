import sys
import time

def beijing_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + 8*3600))

def log(msg):
    ts = beijing_time()
    sys.stdout.write(f"[{ts}] {msg}\n")
    sys.stdout.flush()

def main():
    log("===== 写固定数据到目标仓库 =====")
    log(f"北京时间：{beijing_time()}")

    PROJECTS_PATH = "projects.txt"
    URLS_PATH = "urls.txt"

    # 写项目文件（带时间戳，保证每次不同）
    with open(PROJECTS_PATH, "w", encoding="utf-8") as f:
        f.write(f"# 更新时间：{beijing_time()}\n")
        f.write("固定项目地址：https://github.com/fogret/test-project\n")
        f.write(f"时间戳：{time.time()}\n")

    # 写 URL 文件（带时间戳，保证每次不同）
    with open(URLS_PATH, "w", encoding="utf-8") as f:
        f.write(f"# 更新时间：{beijing_time()}\n")
        f.write("固定 URL：https://www.baidu.com\n")
        f.write(f"时间戳：{time.time()}\n")

    log(f"✔ 已写入 {PROJECTS_PATH}")
    log(f"✔ 已写入 {URLS_PATH}")
    log("===== 写入完成 =====")

if __name__ == "__main__":
    main()
