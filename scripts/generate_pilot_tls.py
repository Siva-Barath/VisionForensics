"""
generate_pilot_tls.py — Generates self-signed TLS certificates for VisionForensics AI pilot reverse proxy.
"""

from pathlib import Path
import datetime
import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def generate_certificates(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    key_path = output_dir / "pilot.key"
    crt_path = output_dir / "pilot.crt"

    print(f"Generating 2048-bit RSA private key...")
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "VisionForensics AI Pilot"),
        x509.NameAttribute(NameOID.COMMON_NAME, "pilot.visionforensics.local"),
    ])

    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("pilot.visionforensics.local"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )

    # Write private key
    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    # Write certificate
    crt_path.write_bytes(
        cert.public_bytes(serialization.Encoding.PEM)
    )

    print(f"Private Key saved to: {key_path}")
    print(f"Certificate saved to: {crt_path}")


if __name__ == "__main__":
    certs_dir = Path(__file__).resolve().parent.parent / "frontend" / "certs"
    generate_certificates(certs_dir)
