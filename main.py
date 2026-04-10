import os
import re
from urllib.parse import urlparse

def extract_links():
    root = os.getcwd()
    data_file = os.path.join(root, "data.txt")

    pattern = re.compile(r'https?://[^\s\'"]+', re.IGNORECASE)

    links = []
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            links.extend(pattern.findall(line))

    return links


def get_name_from_url(url):
    path = urlparse(url).path
    base = os.path.basename(path)
    name = os.path.splitext(base)[0]
    return name if name else "未命名"


def build_yings_txt():
    links = extract_links()

    categories = {}

    for url in links:
        name = get_name_from_url(url)
        category = name  # 分类名称 = 原链接里的名称

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
