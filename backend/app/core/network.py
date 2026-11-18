"""
network.py — Network security, trusted proxy IP resolution, and CSRF Origin validation.
"""

from __future__ import annotations
import ipaddress
from typing import List, Optional
from urllib.parse import urlparse
from fastapi import Request

from app.config.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _parse_trusted_networks(trusted_list: List[str]) -> List[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    networks = []
    for item in trusted_list:
        try:
            if "/" in item:
                networks.append(ipaddress.ip_network(item, strict=False))
            else:
                ip = ipaddress.ip_address(item)
                networks.append(ipaddress.ip_network(f"{ip}/{32 if ip.version == 4 else 128}", strict=False))
        except ValueError as exc:
            logger.warning("Invalid trusted proxy network configuration '%s': %s", item, exc)
    return networks


def is_ip_trusted(ip_str: str, trusted_networks: List[ipaddress.IPv4Network | ipaddress.IPv6Network]) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in net for net in trusted_networks)
    except ValueError:
        return False


def get_client_ip(request: Optional[Request]) -> str:
    """
    Extracts and verifies the genuine client IP address.
    If the immediate peer (request.client.host) is a configured trusted proxy,
    traverses X-Forwarded-For from right to left to locate the first untrusted upstream client.
    Never trusts client-supplied forwarded headers from untrusted connections.
    """
    if not request or not request.client or not request.client.host:
        return "127.0.0.1"

    settings = get_settings()
    peer_ip_str = request.client.host
    trusted_networks = _parse_trusted_networks(settings.trusted_proxies_list)

    # 1. If direct connection is NOT from a trusted proxy, return peer IP immediately.
    # Completely ignores any client-supplied X-Forwarded-For to prevent header spoofing.
    if not is_ip_trusted(peer_ip_str, trusted_networks):
        return peer_ip_str

    # 2. Connection is from a trusted proxy — inspect X-Forwarded-For
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        raw_ips = [ip.strip() for ip in forwarded_for.split(",") if ip.strip()]
        # Traverse right-to-left: the rightmost entries are appended by intermediate proxies
        for candidate in reversed(raw_ips):
            try:
                candidate_ip = ipaddress.ip_address(candidate)
                # Return the first IP that is NOT one of our trusted proxies
                if not any(candidate_ip in net for net in trusted_networks):
                    return str(candidate_ip)
            except ValueError:
                continue

        # If all IPs in chain are trusted, return the leftmost valid IP
        if raw_ips:
            try:
                return str(ipaddress.ip_address(raw_ips[0]))
            except ValueError:
                pass

    # 3. Fallback to X-Real-IP if forwarded_for wasn't present
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        try:
            return str(ipaddress.ip_address(x_real_ip.strip()))
        except ValueError:
            pass

    return peer_ip_str


def validate_request_origin(request: Request) -> bool:
    """
    Validates Origin and Referer headers on state-changing cookie-authenticated endpoints
    to prevent Cross-Site Request Forgery (CSRF).
    """
    settings = get_settings()
    origin = request.headers.get("Origin")
    referer = request.headers.get("Referer")
    allowed = [o.rstrip("/") for o in settings.allowed_origins_list]

    # If Origin is present, must match allowed origins or loopback
    if origin:
        clean_origin = origin.rstrip("/")
        if clean_origin in allowed:
            return True
        parsed = urlparse(clean_origin)
        if parsed.hostname in ("localhost", "127.0.0.1", "::1"):
            return True
        return False

    # If Referer is present, parse origin from it
    if referer:
        parsed = urlparse(referer)
        ref_origin = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
        if ref_origin in allowed:
            return True
        if parsed.hostname in ("localhost", "127.0.0.1", "::1"):
            return True
        return False

    # Check Sec-Fetch-Site (modern browsers)
    sec_fetch_site = request.headers.get("Sec-Fetch-Site")
    if sec_fetch_site in ("cross-site",):
        return False

    # In development or direct API tool (curl/postman with no browser headers), permit
    return True
