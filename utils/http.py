# -*- coding: utf-8 -*-

"""
HTTP 工具模块
用于 IPTV 源探测、健康监测等功能
"""

import asyncio
import aiohttp
from typing import Optional, Tuple


class HttpClient:
    def __init__(self, timeout: float = 3.5, user_agent: Optional[str] = None):
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )

    async def fetch_head(self, session: aiohttp.ClientSession, url: str) -> Tuple[bool, int]:
        """
        发送 HEAD 请求，用于快速判断直播流是否可用
        返回 (是否成功, HTTP 状态码)
        """
        try:
            async with session.head(url, timeout=self.timeout) as resp:
                return True, resp.status
        except Exception:
            return False, 0

    async def fetch_stream_probe(self, session: aiohttp.ClientSession, url: str) -> Tuple[bool, int]:
        """
        用 GET 请求探测直播流是否可访问
        只读取前 1KB，不消耗带宽
        """
        try:
            async with session.get(url, timeout=self.timeout) as resp:
                await resp.content.read(1024)
                return True, resp.status
        except Exception:
            return False, 0

    async def create_session(self) -> aiohttp.ClientSession:
        """
        创建带 UA 的 aiohttp 会话
        """
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "*/*",
            "Connection": "keep-alive",
        }
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        return aiohttp.ClientSession(headers=headers, timeout=timeout)


async def quick_probe(url: str, timeout: float = 3.5) -> bool:
    """
    单 URL 快速探测（给健康监测用）
    """
    client = HttpClient(timeout=timeout)
    session = await client.create_session()

    try:
        ok, status = await client.fetch_stream_probe(session, url)
        return ok and (200 <= status < 400)
    finally:
        await session.close()
