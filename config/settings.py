# -*- coding: utf-8 -*-

"""
全局配置 Settings
"""

from dataclasses import dataclass


@dataclass
class Settings:
    # A1 源探测器
    scanner_concurrency: int = 50          # 默认并发协程数量
    scanner_timeout: float = 3.5           # 单个请求超时时间（秒）

    # A2 M3U 生成器
    default_group_title: str = "影视频道"   # 默认 group-title

    # A3 健康监测系统
    monitor_interval: int = 10             # 每轮监测间隔（秒）
    monitor_rounds: int = 3                # 默认监测轮数
