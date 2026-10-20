"""本地 Web 服务的客户端与来源校验。"""

from __future__ import annotations

import ipaddress
import re


LOCAL_ORIGIN_PATTERN = re.compile(
    r"(?i)^https?://(?:localhost|127\.0\.0\.1|\[::1\])(?::\d{1,5})?$"
)
LOCAL_ORIGIN_REGEX = LOCAL_ORIGIN_PATTERN.pattern


def is_loopback_host(host: str | None) -> bool:
    """仅接受 IPv4/IPv6 回环地址，不信任转发头。"""
    if not host:
        return False

    normalized = host.strip().strip("[]")
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError:
        return False

    if address.is_loopback:
        return True
    mapped = getattr(address, "ipv4_mapped", None)
    return bool(mapped and mapped.is_loopback)


def is_allowed_origin(origin: str | None) -> bool:
    """允许无 Origin 的本机客户端，以及明确的本机浏览器来源。"""
    return origin is None or LOCAL_ORIGIN_PATTERN.fullmatch(origin.strip()) is not None
