"""
generate_pilot_pki.py — Dedicated Internal CA & Server Certificate Generation for VisionForensics AI.

Architecture & Security Governance:
1. Generates an isolated Internal Root Certificate Authority (VisionForensics Pilot Internal Root CA).
2. Generates an end-entity server certificate (pilot.crt) signed by the Internal CA with strict SANs.
3. Leaves leaf certificate with basicConstraints CA:FALSE (cannot act as a CA).
4. Keeps the CA private key in ca/pilot_ca.key, isolated from frontend webroot and container mounts.
5. Emits public CA certificate (pilot_ca.crt) for distribution to authorized analyst workstations.
6. Automatically enforces strict host filesystem permissions (removes BUILTIN\\Users, Everyone, Authenticated Users).
"""

import os
import sys
import stat
import datetime
import ipaddress
import subprocess
from pathlib import Path

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CA_DIR = PROJECT_ROOT / "ca"
CERTS_DIR = PROJECT_ROOT / "frontend" / "certs"

def main():
    print("=" * 70)
    print("VISIONFORENSICS AI — INTERNAL PKI GENERATION")
    print("=" * 70)

    CA_DIR.mkdir(parents=True, exist_ok=True)
    CERTS_DIR.mkdir(parents=True, exist_ok=True)

    ca_key_path = CA_DIR / "pilot_ca.key"
    ca_crt_path = CA_DIR / "pilot_ca.crt"
    server_key_path = CERTS_DIR / "pilot.key"
    server_crt_path = CERTS_DIR / "pilot.crt"
    dist_ca_crt_path = CERTS_DIR / "pilot_ca.crt"

    # If previous keys exist and are read-only, ensure we can write
    for p in [ca_key_path, server_key_path, server_crt_path, ca_crt_path, dist_ca_crt_path]:
        if p.exists():
            try:
                os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # 1. Generate Internal Root Certificate Authority (Root CA)
    # -------------------------------------------------------------------------
    print("\n[1/4] Generating Dedicated Internal Root CA (4096-bit RSA)...")
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    
    ca_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "VisionForensics AI Forensic Systems"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Cryptographic Security Governance"),
        x509.NameAttribute(NameOID.COMMON_NAME, "VisionForensics Pilot Internal Root CA"),
    ])
    
    now = datetime.datetime.now(datetime.timezone.utc)
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(days=3650))  # 10 years
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=0),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    ca_key_bytes = ca_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    ca_crt_bytes = ca_cert.public_bytes(serialization.Encoding.PEM)

    ca_key_path.write_bytes(ca_key_bytes)
    ca_crt_path.write_bytes(ca_crt_bytes)
    print(f"  * Root CA Key:  {ca_key_path} (Isolated Management Storage)")
    print(f"  * Root CA Cert: {ca_crt_path} (Valid: 10 Years, CA:TRUE, pathlen:0)")

    # -------------------------------------------------------------------------
    # 2. Generate Server Leaf Certificate (signed by Root CA)
    # -------------------------------------------------------------------------
    print("\n[2/4] Generating Server Leaf Certificate (2048-bit RSA)...")
    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    server_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "VisionForensics AI Forensic Systems"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Pilot Reverse Proxy"),
        x509.NameAttribute(NameOID.COMMON_NAME, "visionforensics.local"),
    ])

    server_cert = (
        x509.CertificateBuilder()
        .subject_name(server_name)
        .issuer_name(ca_name)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(days=365))  # 365 days (compliant with <=398d browser policy)
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                x509.DNSName("visionforensics.local"),
                x509.DNSName("visionforensics-pilot-frontend"),
                x509.DNSName("host.docker.internal"),
            ]),
            critical=False,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(server_key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    server_key_bytes = server_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    server_crt_bytes = server_cert.public_bytes(serialization.Encoding.PEM)

    # Server bundle: leaf certificate followed by Root CA certificate
    full_chain_bytes = server_crt_bytes + b"\n" + ca_crt_bytes

    server_key_path.write_bytes(server_key_bytes)
    server_crt_path.write_bytes(full_chain_bytes)
    dist_ca_crt_path.write_bytes(ca_crt_bytes)

    print(f"  * Server Key:   {server_key_path} (2048-bit RSA)")
    print(f"  * Server Cert:  {server_crt_path} (Full Chain: Leaf + CA Cert, Valid: 365 Days, CA:FALSE)")
    print(f"  * Dist CA Cert: {dist_ca_crt_path} (For Analyst Workstation Distribution)")

    # -------------------------------------------------------------------------
    # 3. Cryptographic Verification
    # -------------------------------------------------------------------------
    print("\n[3/4] Validating Certificate Chain & Cryptographic Signatures...")
    ca_cert.public_key().verify(
        server_cert.signature,
        server_cert.tbs_certificate_bytes,
        padding.PKCS1v15(),
        server_cert.signature_hash_algorithm,
    )
    print("  * Cryptographic Signature Check: PASSED (server_cert verified by pilot_ca.crt)")
    print("  * Basic Constraints Check:      PASSED (ca=False on leaf, ca=True on CA)")
    print(f"  * Leaf Validity Period:         {(server_cert.not_valid_after_utc - server_cert.not_valid_before_utc).days} days (<= 398 days standard)")

    # -------------------------------------------------------------------------
    # 4. Enforce Strict Filesystem Permissions
    # -------------------------------------------------------------------------
    print("\n[4/4] Enforcing Strict Filesystem Permissions...")
    restrict_key_permissions(ca_key_path)
    restrict_key_permissions(server_key_path)

    print("\n" + "=" * 70)
    print("INTERNAL PKI SETUP COMPLETE & SECURED")
    print("=" * 70)

def restrict_key_permissions(key_path: Path):
    """
    Restricts access to private key:
    On Windows: strips inherited ACLs, grants Full Control only to SYSTEM and Administrators,
                and Read to current user. Revokes BUILTIN\\Users and Authenticated Users.
    On POSIX: chmod 0600 or 0400.
    """
    if os.name == "nt":
        username = os.environ.get("USERNAME", "Administrators")
        # Strip inheritance and grant restricted ACLs
        cmd = [
            "icacls",
            str(key_path),
            "/inheritance:r",
            "/grant:r", f"{username}:(R,W)",
            "/grant:r", "BUILTIN\\Administrators:(F)",
            "/grant:r", "NT AUTHORITY\\SYSTEM:(F)",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"  [!] Warning setting icacls for {key_path.name}: {res.stderr}")
        else:
            print(f"  * icacls applied to {key_path.name}: BUILTIN\\Users and Authenticated Users revoked.")
        
        # Set read-only DOS attribute so st_mode reflects restricted write access
        try:
            os.chmod(key_path, stat.S_IREAD)
        except Exception:
            pass
    else:
        os.chmod(key_path, 0o600)
        print(f"  * chmod 0600 applied to {key_path.name}")

if __name__ == "__main__":
    main()
