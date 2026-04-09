#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
IPTV Super Toolkit
- A1: 源探测器
- A2: M3U 自动生成器
- A3: 直播流健康监测系统
"""

import argparse
import sys
from pathlib import Path

from core.scanner.scanner import run_scanner_cli
from core.generator.m3u_generator import run_m3u_generator_cli
from core.monitor.monitor import run_monitor_cli
from config.settings import Settings
from utils.logger import get_logger

BASE_DIR = Path(__file__).resolve().parent
settings = Settings()
logger = get_logger("iptv_toolkit")


def ensure_dirs() -> None:
    output_dir = BASE_DIR / "output"
    logs_dir = BASE_DIR / "logs"
    output_dir.mkdir(exist_ok=True, parents=True)
    logs_dir.mkdir(exist_ok=True, parents=True)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="IPTV Super Toolkit - Scanner / M3U Generator / Monitor"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # A1: 源探测器
    scan_parser = subparsers.add_parser("scan", help="IPTV 源探测器")
    scan_parser.add_argument(
        "-i", "--input",
        help="待探测的 URL 列表文件（每行一个）",
        required=True,
    )
    scan_parser.add_argument(
        "-o", "--output",
        help="探测结果输出 JSON 文件",
        default=str(BASE_DIR / "output" / "scan_result.json"),
    )
    scan_parser.add_argument(
        "--concurrency",
        type=int,
        default=settings.scanner_concurrency,
        help="并发协程数量",
    )
    scan_parser.add_argument(
        "--timeout",
        type=float,
        default=settings.scanner_timeout,
        help="单个请求超时时间（秒）",
    )

    # A2: M3U 生成器
    m3u_parser = subparsers.add_parser("m3u", help="M3U 自动生成器")
    m3u_parser.add_argument(
        "-i", "--input",
        help="可用源 JSON 文件（通常由 scan 结果生成）",
        required=True,
    )
    m3u_parser.add_argument(
        "-o", "--output",
        help="输出 M3U 文件路径",
        default=str(BASE_DIR / "output" / "playlist.m3u"),
    )
    m3u_parser.add_argument(
        "--group",
        help="默认 group-title（如：影视频道）",
        default=settings.default_group_title,
    )
    m3u_parser.add_argument(
        "--tvbox",
        action="store_true",
        help="生成 TVBox 兼容格式",
    )

    # A3: 健康监测
    monitor_parser = subparsers.add_parser("monitor", help="直播流健康监测系统")
    monitor_parser.add_argument(
        "-i", "--input",
        help="待监测的 M3U 或 URL 列表文件",
        required=True,
    )
    monitor_parser.add_argument(
        "-o", "--output",
        help="监测结果输出 JSON 文件",
        default=str(BASE_DIR / "output" / "monitor_result.json"),
    )
    monitor_parser.add_argument(
        "--interval",
        type=int,
        default=settings.monitor_interval,
        help="监测间隔（秒）",
    )
    monitor_parser.add_argument(
        "--rounds",
        type=int,
        default=settings.monitor_rounds,
        help="监测轮数",
    )

    return parser.parse_args(argv)


def main(argv=None) -> int:
    ensure_dirs()
    args = parse_args(argv)

    if args.command == "scan":
        logger.info("启动 IPTV 源探测器")
        return run_scanner_cli(
            input_path=args.input,
            output_path=args.output,
            concurrency=args.concurrency,
            timeout=args.timeout,
        )

    if args.command == "m3u":
        logger.info("启动 M3U 自动生成器")
        return run_m3u_generator_cli(
            input_path=args.input,
            output_path=args.output,
            default_group=args.group,
            tvbox_mode=args.tvbox,
        )

    if args.command == "monitor":
        logger.info("启动直播流健康监测系统")
        return run_monitor_cli(
            input_path=args.input,
            output_path=args.output,
            interval=args.interval,
            rounds=args.rounds,
        )

    logger.error("未知命令")
    return 1


if __name__ == "__main__":
    sys.exit(main())
