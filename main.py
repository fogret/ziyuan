import os
import re

def log(msg):
    print(msg, flush=True)

extinf_re = re.compile(
    r'#EXTINF:[^\n]*group-title="(?P<group>[^"]*)"[^\n]*,(?P<name>.+)$'
)

def extract_channels():
    log("开始读取 data.txt")
    root = os.getcwd()
    data_file = os.path.join(root, "data.txt")

    if not os.path.exists(data_file):
        log("data.txt 不存在")
        return {}

    categories = {}

    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line.startswith("#EXTINF"):
                continue

            m = extinf_re.match(line)
            if not m:
                log(f"未匹配到 EXTINF 格式: {line}")
                continue

            group = m.group("group").strip() or "未分类"
            name = m.group("name").strip() or "未命名"

            log(f"分类: {group}  频道: {name}")

            if group not in categories:
                categories[group] = []
            categories[group].append(name)

    log(f"共解析到 {len(categories)} 个分类")
    return categories


def build_yings_txt():
    log("开始生成 yings.txt")
    categories = extract_channels()

    out_file = os.path.join(os.getcwd(), "yings.txt")
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
