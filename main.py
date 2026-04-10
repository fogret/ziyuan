import os
import re
from urllib.parse import urlparse

def log(msg):
    print(msg, flush=True)

def extract_links():
    log("开始读取 data.txt")
    root = os.getcwd()
    data_file = os.path.join(root, "data.txt")

    if not os.path.exists(data_file):
        log("data.txt 不存在")
        return []

    pattern = re.compile(r'https?://[^\s\'"]+', re.IGNORECASE)

    links = []
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            found = pattern.findall(line)
            if found:
                log(f"匹配到链接: {found}")
            links.extend(found)

    log(f"总共提取到 {len(links)} 个链接")
    return links


def get_name_from_url(url):
    path = urlparse(url).path
    base = os.path.basename(path)
    name = os.path.splitext(base)[0]
    return name if name else "未命名"


def build_yings_txt():
    log("开始生成 yings.txt")
    links = extract_links()

    if not links:
        log("没有任何链接，yings.txt 将为空")
    else:
        log("开始解析分类名称")

    categories = {}

    for url in links:
        name = get_name_from_url(url)
        category = name
        log(f"分类: {category}  名称: {name}")

        if category not in categories:
            categories[category] = []

        categories[category].append(name)

    root = os.getcwd()
    out_file = os.path.join(root, "yings.txt")

    with open(out_file, 'w', encoding='utf-8') as f:
        for cat, names in categories.items():
            f.write(f"{cat}\n")
            for n in names:
                f.write(f"  {n}\n")
            f.write("\n")

    log("yings.txt 写入完成")
    log(f"文件路径: {out_file}")


if __name__ == "__main__":
    log("开始执行 main.py")
    build_yings_txt()
    log("main.py 执行结束")
