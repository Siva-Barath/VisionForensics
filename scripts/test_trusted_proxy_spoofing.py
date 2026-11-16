"""
test_trusted_proxy_spoofing.py — Rigorous verification of trusted proxy configuration and anti-spoofing defense.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config.settings import get_settings
from app.core.network import get_client_ip, is_ip_trusted, _parse_trusted_networks

print("=" * 70)
print("VERIFYING TRUSTED PROXY CONFIGURATION & ANTI-SPOOFING CONTROLS")
print("=" * 70)

settings = get_settings()
print(f"Configured TRUSTED_PROXIES: {settings.trusted_proxies}")
trusted_nets = _parse_trusted_networks(settings.trusted_proxies_list)
print(f"Parsed Trusted Networks:    {[str(n) for n in trusted_nets]}")

# 1. Verification that ONLY Nginx (172.28.0.10) and localhost are trusted
assert is_ip_trusted("172.28.0.10", trusted_nets) is True, "Nginx proxy IP 172.28.0.10 must be trusted!"
assert is_ip_trusted("127.0.0.1", trusted_nets) is True, "Localhost 127.0.0.1 must be trusted!"
assert is_ip_trusted("172.28.0.20", trusted_nets) is False, "Backend IP 172.28.0.20 must NOT be trusted!"
assert is_ip_trusted("172.28.0.50", trusted_nets) is False, "Arbitrary container IP must NOT be trusted!"
assert is_ip_trusted("192.168.1.100", trusted_nets) is False, "LAN IP must NOT be trusted!"
assert is_ip_trusted("198.51.100.25", trusted_nets) is False, "Public IP must NOT be trusted!"
print("  * Proxy IP Authorization:   CONFIRMED (Only Nginx 172.28.0.10 and localhost 127.0.0.1 are trusted)")

# 2. Test Case 1: Untrusted Direct Peer with Spoofed Header
mock_req_untrusted = MagicMock()
mock_req_untrusted.client.host = "198.51.100.77"
mock_req_untrusted.headers = {
    "X-Forwarded-For": "8.8.8.8",
    "X-Real-IP": "8.8.8.8",
}
ip1 = get_client_ip(mock_req_untrusted)
print(f"\n[TEST 1] Direct Untrusted Peer (198.51.100.77) with Spoofed X-Forwarded-For: 8.8.8.8")
print(f"  * Resolved Client IP:       {ip1}")
assert ip1 == "198.51.100.77", f"Spoofing vulnerability! Expected 198.51.100.77, got {ip1}"
print("  --> PASS: Spoofed headers from untrusted connection were completely ignored.")

# 3. Test Case 2: Arbitrary Container Peer with Spoofed Header
mock_req_rogue_container = MagicMock()
mock_req_rogue_container.client.host = "172.28.0.99"
mock_req_rogue_container.headers = {
    "X-Forwarded-For": "1.1.1.1",
    "X-Real-IP": "1.1.1.1",
}
ip2 = get_client_ip(mock_req_rogue_container)
print(f"\n[TEST 2] Rogue Container Peer (172.28.0.99) with Spoofed X-Forwarded-For: 1.1.1.1")
print(f"  * Resolved Client IP:       {ip2}")
assert ip2 == "172.28.0.99", f"Spoofing vulnerability! Expected 172.28.0.99, got {ip2}"
print("  --> PASS: Unapproved container connection cannot spoof client IP.")

# 4. Test Case 3: Legitimate Nginx Proxy Forwarding Client Request
mock_req_nginx = MagicMock()
mock_req_nginx.client.host = "172.28.0.10"
mock_req_nginx.headers = {
    "X-Forwarded-For": "203.0.113.195",
    "X-Real-IP": "203.0.113.195",
}
ip3 = get_client_ip(mock_req_nginx)
print(f"\n[TEST 3] Trusted Nginx Proxy (172.28.0.10) Forwarding Upstream Client: 203.0.113.195")
print(f"  * Resolved Client IP:       {ip3}")
assert ip3 == "203.0.113.195", f"Expected upstream client 203.0.113.195, got {ip3}"
print("  --> PASS: Legitimate upstream client IP successfully resolved through trusted proxy.")

# 5. Test Case 4: Client Attempting Header Injection through Nginx
# An attacker sends X-Forwarded-For: 10.0.0.1, which Nginx appends the client IP to:
mock_req_chain = MagicMock()
mock_req_chain.client.host = "172.28.0.10"
mock_req_chain.headers = {
    "X-Forwarded-For": "10.0.0.1, 203.0.113.195",
}
ip4 = get_client_ip(mock_req_chain)
print(f"\n[TEST 4] Attacker Injected X-Forwarded-For Chain through Nginx: '10.0.0.1, 203.0.113.195'")
print(f"  * Resolved Client IP:       {ip4}")
assert ip4 == "203.0.113.195", f"Header injection vulnerability! Expected 203.0.113.195, got {ip4}"
print("  --> PASS: Right-to-left traversal correctly extracted genuine peer and ignored injected prefix.")

print("\n" + "=" * 70)
print("ALL TRUSTED PROXY ANTI-SPOOFING TESTS PASSED (100%)")
print("=" * 70)
