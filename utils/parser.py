# -*- coding: utf-8 -*-

"""
通用解析模块
- 解析 URL 列表
- 解析 M3U 文件
- 解析 JSON 结果
"""

import json
from pathlib import Path
from typing import List, Dict


def load_url_list(path: str) -> List[str]:
    """
    从文本文件加载 URL 列表（每行一个）
    """
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(f"URL 列表文件不存在: {path}")

    urls = []
    for line in file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)

    return urls


def load_json(path: str) -> Dict:
    """
    加载 JSON 文件
    """
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(f"JSON 文件不存在: {path}")

    return json.loads(file.read_text(encoding="utf-8"))


def save_json(path: str, data: Dict) -> None:
    """
    保存 JSON 文件
    """
    file = Path(path)
    file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_m3u(path: str) -> List[Dict]:
    """
    解析 M3U 文件，返回频道列表
    每个频道结构：
    {
        "name": "",
        "group": "",
        "url": ""
    }
    """
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(f"M3U 文件不存在: {path}")

    lines = file.read_text(encoding="utf-8").splitlines()
    channels = []
    current = {}

    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF"):
            # 解析频道信息
            name = ""
            group = ""

            if "group-title" in line:
                try:
                    group = line.split('group-title="')[1].split('"')[0]
                except Exception:
                    group = ""

            if "," in line:
                name = line.split(",", 1)[1].strip()

            current = {"name": name, "group": group, "url": ""}
        elif line.startswith("http"):
            current["url"] = line
            channels.append(current)
            current = {}

    return channels
