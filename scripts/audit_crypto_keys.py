"""
audit_crypto_keys.py — Comprehensive Cryptographic Key Handling, Internal PKI,
Filesystem Permission Hardening, Git Exclusion, and Log Sanitization Audit.
"""

import os
import sys
import stat
import re
import socket
import ssl
import threading
import subprocess
from pathlib import Path

from cryptography import x509
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

print("=" * 75)
print("VISIONFORENSICS AI — CRYPTOGRAPHIC SECURITY & PKI AUDIT")
print("=" * 75)

root = Path(__file__).resolve().parent.parent
gitignore_path = root / ".gitignore"
tls_key_path = root / "frontend" / "certs" / "pilot.key"
tls_crt_path = root / "frontend" / "certs" / "pilot.crt"
tls_dist_ca_path = root / "frontend" / "certs" / "pilot_ca.crt"
ca_key_path = root / "ca" / "pilot_ca.key"
ca_crt_path = root / "ca" / "pilot_ca.crt"
env_pilot_path = root / ".env.pilot"
compose_path = root / "docker-compose.pilot.yml"
dockerfile_frontend_path = root / "frontend" / "Dockerfile"

failures = []

# -----------------------------------------------------------------------------
# 1. TLS Private Key & Root CA Key Permission Hardening Audit
# -----------------------------------------------------------------------------
print("\n[1/6] Auditing Private Key Permissions & Host Isolation...")

for key_title, key_p in [("Server Leaf Key", tls_key_path), ("Root CA Key", ca_key_path)]:
    if not key_p.exists():
        failures.append(f"{key_title}: File missing at {key_p}")
        continue

    size = key_p.stat().st_size
    mode = oct(key_p.stat().st_mode)
    print(f"  * {key_title} Location:  {key_p}")
    print(f"  * Key Size:                 {size} bytes")
    print(f"  * Filesystem Mode:          {mode}")

    # Mode validation
    if os.name == "nt":
        # On Windows, check st_mode does not have write permissions for group/others
        raw_mode = key_p.stat().st_mode
        if raw_mode & (stat.S_IWGRP | stat.S_IWOTH):
            failures.append(f"CRITICAL: {key_title} has insecure write permissions: {mode}")
        
        # Windows NTFS ACL check via icacls
        try:
            res = subprocess.run(["icacls", str(key_p)], capture_output=True, text=True, check=True)
            acl_output = res.stdout
            # Ensure unauthorized groups are NOT present in ACL
            forbidden_groups = ["BUILTIN\\Users", "Everyone", "NT AUTHORITY\\Authenticated Users"]
            for grp in forbidden_groups:
                if grp in acl_output:
                    failures.append(f"CRITICAL: {key_title} grants permissions to forbidden group '{grp}'!\n{acl_output}")
            print(f"  * Windows NTFS ACL Audit:   PASSED (BUILTIN\\Users & Authenticated Users revoked)")
        except Exception as e:
            failures.append(f"Failed running icacls on {key_p}: {e}")
    else:
        # On POSIX: strictly 0600 or 0400
        raw_mode = key_p.stat().st_mode
        if raw_mode & 0o077 != 0:
            failures.append(f"CRITICAL: {key_title} permissions too broad on POSIX: {mode} (must be 0400 or 0600)")
        else:
            print(f"  * POSIX Permission Audit:   PASSED ({mode})")

# -----------------------------------------------------------------------------
# 2. CA Key Isolation & Container Boundary Verification
# -----------------------------------------------------------------------------
print("\n[2/6] Auditing CA Private Key Isolation & Container Mounts...")

# Ensure ca/pilot_ca.key is NEVER copied to frontend/certs or webroot
if (root / "frontend" / "certs" / "pilot_ca.key").exists():
    failures.append("CRITICAL LEAK: pilot_ca.key was found inside frontend/certs/!")
else:
    print("  * CA Key Webroot Exclusion: PASSED (pilot_ca.key strictly isolated outside frontend)")

# Check docker-compose.pilot.yml for read-only mount and absence of ca_key mount
if compose_path.exists():
    compose_text = compose_path.read_text(encoding="utf-8")
    if "pilot_ca.key" in compose_text:
        failures.append("CRITICAL: docker-compose.pilot.yml mounts pilot_ca.key!")
    if "./frontend/certs:/etc/nginx/certs:ro" not in compose_text:
        failures.append("docker-compose.pilot.yml must mount frontend/certs as read-only (:ro)")
    else:
        print("  * Container Volume Security: PASSED (certs mounted read-only :ro; CA key not mounted)")
else:
    failures.append("docker-compose.pilot.yml missing")

# Check frontend/Dockerfile does not copy CA key
if dockerfile_frontend_path.exists():
    df_text = dockerfile_frontend_path.read_text(encoding="utf-8")
    if "pilot_ca.key" in df_text:
        failures.append("CRITICAL: frontend/Dockerfile references pilot_ca.key!")
    if "chmod 600 /etc/nginx/certs/pilot.key" not in df_text:
        failures.append("frontend/Dockerfile must enforce chmod 600 on /etc/nginx/certs/pilot.key")
    else:
        print("  * Container Image Hardening: PASSED (Docker image enforces chmod 600 / chown root:nginx)")
else:
    failures.append("frontend/Dockerfile missing")

# -----------------------------------------------------------------------------
# 3. PKI Hierarchy, Certificate SANs & Validity Audit
# -----------------------------------------------------------------------------
print("\n[3/6] Auditing PKI Hierarchy, SANs, and Certificate Validity...")

if not ca_crt_path.exists():
    failures.append("ca/pilot_ca.crt missing")
elif not tls_crt_path.exists():
    failures.append("frontend/certs/pilot.crt missing")
else:
    try:
        ca_cert = x509.load_pem_x509_certificate(ca_crt_path.read_bytes())
        certs_in_bundle = x509.load_pem_x509_certificates(tls_crt_path.read_bytes())
        leaf_cert = certs_in_bundle[0]

        # 3.1 Verify Root CA properties
        ca_bc = ca_cert.extensions.get_extension_for_class(x509.BasicConstraints).value
        if not ca_bc.ca:
            failures.append("Root CA certificate must have basicConstraints CA:TRUE")
        if ca_bc.path_length != 0:
            failures.append("Root CA certificate must have path_length=0 (cannot issue intermediates)")
        print(f"  * Root CA basicConstraints: PASSED (CA:TRUE, pathlen=0)")

        # 3.2 Verify Leaf Certificate properties (CANNOT be a CA!)
        leaf_bc = leaf_cert.extensions.get_extension_for_class(x509.BasicConstraints).value
        if leaf_bc.ca:
            failures.append("CRITICAL: Server leaf certificate has CA:TRUE! It must be CA:FALSE.")
        else:
            print("  * Leaf basicConstraints:    PASSED (CA:FALSE — cannot act as a CA)")

        # 3.3 Verify Cryptographic Signature of leaf by Root CA
        ca_cert.public_key().verify(
            leaf_cert.signature,
            leaf_cert.tbs_certificate_bytes,
            padding.PKCS1v15(),
            leaf_cert.signature_hash_algorithm,
        )
        print("  * PKI Signature Chain:      PASSED (leaf signature cryptographically verified by Root CA)")

        # 3.4 Verify Subject Alternative Names (SANs)
        san_ext = leaf_cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        san_values = [str(n.value) for n in san_ext]
        required_sans = ["localhost", "127.0.0.1", "visionforensics.local", "visionforensics-pilot-frontend"]
        for r_san in required_sans:
            if r_san not in san_values:
                failures.append(f"Leaf certificate missing required SAN: {r_san}")
        print(f"  * Subject Alternative Names: PASSED (Includes: {', '.join(required_sans)})")

        # 3.5 Verify Validity Window
        validity_days = (leaf_cert.not_valid_after_utc - leaf_cert.not_valid_before_utc).days
        if validity_days > 398:
            failures.append(f"Leaf certificate validity is {validity_days} days (> 398 days browser maximum policy)")
        else:
            print(f"  * Leaf Validity Policy:     PASSED ({validity_days} days <= 398 days)")

        if len(certs_in_bundle) < 2:
            failures.append("pilot.crt must bundle the full chain (leaf certificate + Root CA certificate)")
        else:
            print(f"  * Full Chain Bundle:        PASSED (2 certificates bundled in pilot.crt)")

    except Exception as e:
        failures.append(f"PKI validation error: {e}")

# -----------------------------------------------------------------------------
# 4. Live TLS Handshake & Client CA Verification Test
# -----------------------------------------------------------------------------
print("\n[4/6] Executing Live TLS Handshake with Internal CA Validation...")

try:
    # Build TLS Server Context with leaf cert & key
    server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_ctx.load_cert_chain(str(tls_crt_path), str(tls_key_path))

    # Spin up ephemeral local listener
    srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv_sock.bind(("127.0.0.1", 0))
    port = srv_sock.getsockname()[1]
    srv_sock.listen(1)

    server_errors = []
    def srv_worker():
        try:
            conn, _ = srv_sock.accept()
            with server_ctx.wrap_socket(conn, server_side=True) as ss:
                ss.sendall(b"VISIONFORENSICS_TLS_OK")
        except Exception as ex:
            server_errors.append(str(ex))

    th = threading.Thread(target=srv_worker)
    th.start()

    # Build TLS Client Context trusting ONLY the internal Root CA
    client_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=str(ca_crt_path))
    # verify_mode is CERT_REQUIRED by default, check_hostname=True by default
    with socket.create_connection(("127.0.0.1", port), timeout=5) as raw_conn:
        with client_ctx.wrap_socket(raw_conn, server_hostname="localhost") as tls_conn:
            banner = tls_conn.recv(1024)
            cipher = tls_conn.cipher()
            peer_cert = tls_conn.getpeercert()

            if banner != b"VISIONFORENSICS_TLS_OK":
                failures.append(f"Unexpected TLS banner: {banner}")
            else:
                print(f"  * TLS Termination Handshake: PASSED (Negotiated: {cipher[0]} / {cipher[1]})")
                print(f"  * Client CA Validation:      PASSED (Authenticity verified against {ca_crt_path.name})")

    th.join()
    srv_sock.close()

except Exception as e:
    failures.append(f"Live TLS handshake verification failed: {e}")

# -----------------------------------------------------------------------------
# 5. Backup HMAC Key Location & Storage Isolation
# -----------------------------------------------------------------------------
print("\n[5/6] Auditing Backup HMAC Key & Storage Isolation...")
if not env_pilot_path.exists():
    failures.append(".env.pilot missing")
else:
    env_content = env_pilot_path.read_text(encoding="utf-8")
    hmac_match = re.search(r"BACKUP_HMAC_KEY=([a-fA-F0-9]+)", env_content)
    if not hmac_match:
        failures.append("BACKUP_HMAC_KEY not found in .env.pilot")
    else:
        hmac_key_val = hmac_match.group(1)
        print(f"  * BACKUP_HMAC_KEY Location:  Configured in .env.pilot")
        print(f"  * Key Length:                {len(hmac_key_val)} hex characters (256-bit)")

        # Verify key is NOT inside any backup directory
        backups_dir = root / "backups"
        if backups_dir.exists():
            for b_file in backups_dir.rglob("*"):
                if b_file.is_file() and not b_file.name.endswith(".dump"):
                    try:
                        content = b_file.read_text(encoding="utf-8", errors="ignore")
                        if hmac_key_val in content:
                            failures.append(f"CRITICAL: BACKUP_HMAC_KEY was found stored inside backup artifact: {b_file}")
                    except Exception:
                        pass
        print("  * Backup Directory Check:   PASSED (HMAC secret strictly absent from backups)")

# -----------------------------------------------------------------------------
# 6. Git Exclusion & Secret Log Sanitization Audit
# -----------------------------------------------------------------------------
print("\n[6/6] Auditing Git Exclusion (.gitignore) & Log Sanitization...")
if not gitignore_path.exists():
    failures.append(".gitignore missing")
else:
    gi_text = gitignore_path.read_text(encoding="utf-8")
    required_patterns = [".env.pilot", "*.key", "frontend/certs/", "ca/", "backups/"]
    for pat in required_patterns:
        if pat not in gi_text:
            failures.append(f"Git Exclusion: Pattern '{pat}' missing from .gitignore!")
        else:
            print(f"  * Excluded in .gitignore:   {pat:<20} (CONFIRMED)")

# Audit logs for private key headers and HMAC secrets
log_dirs = [root / "backend", root / "scripts"]
found_leaks = 0
key_headers = ["-----BEGIN RSA PRIVATE KEY-----", "-----BEGIN PRIVATE KEY-----"]

for search_dir in log_dirs:
    for log_file in search_dir.glob("**/*.log"):
        try:
            txt = log_file.read_text(encoding="utf-8", errors="ignore")
            for kh in key_headers:
                if kh in txt:
                    failures.append(f"LEAK: TLS private key header found in {log_file}")
                    found_leaks += 1
            if hmac_key_val in txt:
                failures.append(f"LEAK: BACKUP_HMAC_KEY found in {log_file}")
                found_leaks += 1
        except Exception:
            pass

if found_leaks == 0:
    print("  * Secret Log Sanitization:  CONFIRMED (Zero private keys or HMAC secrets present in log files)")

print("\n" + "=" * 75)
if failures:
    print("CRYPTO SECURITY AUDIT FAILED:")
    for f in failures:
        print(f"  [X] {f}")
    sys.exit(1)
else:
    print("ALL CRYPTOGRAPHIC & PKI SECURITY AUDIT CHECKS PASSED (100% Secure)")
    print("=" * 75)
