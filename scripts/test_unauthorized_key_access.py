"""
test_unauthorized_key_access.py — Verify Host DACL Security, Read-Only Enforcement,
and Client CA Trust Rejection/Acceptance.
"""

import os
import sys
import ssl
import socket
import threading
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent.parent
key_path = root / "frontend" / "certs" / "pilot.key"
crt_path = root / "frontend" / "certs" / "pilot.crt"
ca_crt_path = root / "ca" / "pilot_ca.crt"

print("=" * 70)
print("TESTING UNAUTHORIZED ACCESS & CA TRUST BOUNDARIES")
print("=" * 70)

# Test 1: Write Prevention on Private Key
print("\n[Test 1] Attempting Direct Modification of pilot.key...")
try:
    with open(key_path, "a") as f:
        f.write("\n# unauthorized modification attempt")
    print("FAILED: Write succeeded unexpectedly!")
    sys.exit(1)
except PermissionError as e:
    print(f"PASSED: Write blocked by OS filesystem permissions: {e}")

# Test 2: Windows NTFS DACL Absence of Unprivileged Groups
print("\n[Test 2] Auditing NTFS Discretionary Access Control Lists (DACL)...")
if os.name == "nt":
    res = subprocess.run(["icacls", str(key_path)], capture_output=True, text=True, check=True)
    out = res.stdout
    disallowed = ["BUILTIN\\Users", "Everyone", "NT AUTHORITY\\Authenticated Users"]
    for group in disallowed:
        if group in out:
            print(f"FAILED: Found unauthorized group '{group}' in DACL:\n{out}")
            sys.exit(1)
    print("PASSED: Disallowed groups (BUILTIN\\Users, Everyone, Authenticated Users) are strictly absent.")
else:
    print("Non-Windows OS: checking POSIX octal mode...")
    mode = oct(key_path.stat().st_mode)
    if key_path.stat().st_mode & 0o077 != 0:
        print(f"FAILED: Permissions too permissive: {mode}")
        sys.exit(1)
    print(f"PASSED: POSIX mode is {mode}")

# Test 3: TLS Client Without Root CA Fails Validation
print("\n[Test 3] Verifying TLS Handshake Rejection Without CA Trust...")
server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
server_ctx.load_cert_chain(str(crt_path), str(key_path))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("127.0.0.1", 0))
port = s.getsockname()[1]
s.listen(1)

def srv():
    try:
        c, _ = s.accept()
        with server_ctx.wrap_socket(c, server_side=True) as ss:
            ss.sendall(b"SECRET_DATA")
    except Exception:
        pass

t = threading.Thread(target=srv)
t.start()

# Untrusted client (default system trust, which does not yet have our internal CA)
untrusted_ctx = ssl.create_default_context()
rejected = False
try:
    with socket.create_connection(("127.0.0.1", port), timeout=3) as sock:
        with untrusted_ctx.wrap_socket(sock, server_hostname="localhost") as tls_sock:
            tls_sock.recv(1024)
except ssl.SSLCertVerificationError as ex:
    rejected = True
    print(f"PASSED: Untrusted connection rejected as expected: {ex.verify_message}")
except Exception as ex:
    # Any TLS verification failure is expected
    rejected = True
    print(f"PASSED: Untrusted connection rejected: {ex}")

t.join()
s.close()

if not rejected:
    print("FAILED: Untrusted client was accepted unexpectedly!")
    sys.exit(1)

# Test 4: TLS Client With Root CA Succeeds Validation
print("\n[Test 4] Verifying TLS Handshake Acceptance With Pilot Root CA Trust...")
s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s2.bind(("127.0.0.1", 0))
port2 = s2.getsockname()[1]
s2.listen(1)

def srv2():
    try:
        c, _ = s2.accept()
        with server_ctx.wrap_socket(c, server_side=True) as ss:
            ss.sendall(b"AUTHORIZED_FORENSIC_SESSION")
    except Exception:
        pass

t2 = threading.Thread(target=srv2)
t2.start()

trusted_ctx = ssl.create_default_context(cafile=str(ca_crt_path))
with socket.create_connection(("127.0.0.1", port2), timeout=3) as sock2:
    with trusted_ctx.wrap_socket(sock2, server_hostname="localhost") as tls_sock2:
        msg = tls_sock2.recv(1024)
        if msg == b"AUTHORIZED_FORENSIC_SESSION":
            print(f"PASSED: Trusted client received: {msg.decode()}")
        else:
            print(f"FAILED: Unexpected message: {msg}")
            sys.exit(1)

t2.join()
s2.close()

print("\n" + "=" * 70)
print("ALL UNAUTHORIZED ACCESS & CA TRUST TESTS PASSED (4/4)")
print("=" * 70)
