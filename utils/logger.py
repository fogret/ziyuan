# -*- coding: utf-8 -*-

"""
统一日志模块
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    log_dir = Path(__file__).resolve().parents[1] / "logs"
    log_dir.mkdir(exist_ok=True, parents=True)

    log_file = log_dir / f"{name}.log"

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
