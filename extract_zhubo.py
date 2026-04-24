import re
import os
import logging

# 日志配置（GitHub Actions 友好）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 配置路径
INPUT_PATH = "urls.txt"
OUTPUT_PATH = "zhubo.txt"

# 精准匹配你要的格式：http://ip:port/rtp/数字组播地址
URL_PATTERN = re.compile(
    r"http://\d+\.\d+\.\d+\.\d+:\d+/rtp/\d+\.\d+\.\d+\.\d+:\d+",
    re.IGNORECASE
)

unique_links = []
seen = set()

logging.info("【开始】提取公网 RTP 转发直播源")

# 检查文件是否存在
if not os.path.exists(INPUT_PATH):
    logging.error(f"【失败】未找到 urls.txt 文件，请确认文件已上传")
else:
    logging.info(f"【读取】成功加载 urls.txt")

    # 读取内容
    with open(INPUT_PATH, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # 匹配链接
    raw_links = URL_PATTERN.findall(content)
    logging.info(f"【匹配】原始匹配到链接：{len(raw_links)} 条")

    # 去重
    for link in raw_links:
        link = link.strip()
        if link and link not in seen:
            seen.add(link)
            unique_links.append(link)

    logging.info(f"【去重】最终有效链接：{len(unique_links)} 条")

# 写入文件
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(unique_links))

logging.info(f"【写入】已生成 {OUTPUT_PATH}")
logging.info(f"【完成】RTP 源提取任务结束")
