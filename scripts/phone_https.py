"""Prepare and serve local HTTPS for phone tests without changing system trust.

Run with the project's Python:
    python scripts/phone_https.py setup --ip YOUR_LAPTOP_WIFI_IP
    python scripts/phone_https.py serve
"""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
from pathlib import Path
import secrets
import shutil
import ssl
import subprocess
import sys
import threading


PROJECT_DIR = Path(__file__).resolve().parents[1]
CERT_DIR = PROJECT_DIR / ".local-https"
PUBLIC_CERT_NAME = "pothole-test-ca.cer"
HTTPS_PORT = 8443
CERTIFICATE_PORT = 8002


def private_ipv4(value: str) -> str:
    """Only bind this development helper to a private LAN address."""
    address = ipaddress.IPv4Address(value)
    allowed = ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
    if not any(address in ipaddress.IPv4Network(network) for network in allowed):
        raise ValueError("Use the laptop's private Wi-Fi IPv4 address.")
    return str(address)


def setup(ip: str) -> None:
    ip = private_ipv4(ip)
    openssl = shutil.which("openssl") or str(Path("C:/Program Files/Git/usr/bin/openssl.exe"))
    if not Path(openssl).is_file():
        raise RuntimeError("OpenSSL was not found. Git for Windows includes it.")
    CERT_DIR.mkdir(exist_ok=True)

    def run(*arguments: str) -> None:
        # Argument lists avoid interpreting file paths or input as shell commands.
        result = subprocess.run(
            [openssl, *arguments], cwd=CERT_DIR, capture_output=True, text=True,
            check=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode:
            raise RuntimeError(f"OpenSSL {arguments[0]} failed: {result.stderr.strip()}")

    root_key = CERT_DIR / "root-ca.key"
    root_cert = CERT_DIR / "root-ca.pem"
    if root_key.exists() != root_cert.exists():
        raise RuntimeError("The local CA is incomplete. Keep its existing files for diagnosis; do not overwrite them.")

    if not root_cert.exists():
        (CERT_DIR / "root.cnf").write_text(
            "[req]\nprompt=no\ndistinguished_name=dn\nx509_extensions=ca\n"
            "[dn]\nCN=Pothole Phone Test CA\n"
            "[ca]\nbasicConstraints=critical,CA:TRUE,pathlen:0\n"
            "keyUsage=critical,keyCertSign,cRLSign\n"
            "subjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid:always\n",
            encoding="ascii",
        )
        run("req", "-x509", "-newkey", "rsa:2048", "-noenc", "-sha256", "-days", "365",
            "-config", "root.cnf", "-keyout", "root-ca.key", "-out", "root-ca.pem")
    # Reuse the same CA so changing the laptop IP does not require reinstalling it.
    run("x509", "-in", "root-ca.pem", "-noout", "-checkend", str(31 * 86400))
    (CERT_DIR / "server.cnf").write_text(
        "[req]\nprompt=no\ndistinguished_name=dn\n"
        "[dn]\nCN=Pothole local recording test\n"
        "[server]\nbasicConstraints=critical,CA:FALSE\n"
        "keyUsage=critical,digitalSignature,keyEncipherment\n"
        "extendedKeyUsage=serverAuth\nsubjectKeyIdentifier=hash\n"
        "authorityKeyIdentifier=keyid,issuer\n"
        f"subjectAltName=IP:{ip},IP:127.0.0.1,DNS:localhost\n",
        encoding="ascii",
    )
    run("req", "-new", "-newkey", "rsa:2048", "-noenc", "-sha256",
        "-config", "server.cnf", "-keyout", "server.key", "-out", "server.csr")
    run("x509", "-req", "-in", "server.csr", "-CA", "root-ca.pem", "-CAkey", "root-ca.key",
        "-set_serial", "0x" + secrets.token_hex(16), "-sha256", "-days", "30",
        "-extfile", "server.cnf", "-extensions", "server", "-out", "server.pem")
    run("verify", "-CAfile", "root-ca.pem", "-purpose", "sslserver", "-verify_ip", ip, "server.pem")
    # Export ONLY the public CA certificate in the format used for phone import.
    run("x509", "-in", "root-ca.pem", "-outform", "DER", "-out", PUBLIC_CERT_NAME)
    ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER).load_cert_chain(CERT_DIR / "server.pem", CERT_DIR / "server.key")
    (CERT_DIR / "settings.json").write_text(json.dumps({"ip": ip}, indent=2), encoding="utf-8")
    print(f"Prepared and verified local certificates for {ip} (server certificate: 30 days).")
    print("Private keys remain in the ignored .local-https folder. System trust was not changed.")
    print("Next: run this script with 'serve'.")


class CertificateDownload(BaseHTTPRequestHandler):
    """Serve exactly one public certificate, never a filesystem directory."""

    def do_GET(self) -> None:
        if self.path != f"/{PUBLIC_CERT_NAME}":
            self.send_error(404)
            return
        content = (CERT_DIR / PUBLIC_CERT_NAME).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "application/x-x509-ca-cert")
        self.send_header("Content-Disposition", f'attachment; filename="{PUBLIC_CERT_NAME}"')
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)


def serve() -> None:
    settings_path = CERT_DIR / "settings.json"
    if not settings_path.exists():
        raise RuntimeError("Run 'setup --ip YOUR_LAPTOP_WIFI_IP' first.")
    ip = private_ipv4(json.loads(settings_path.read_text(encoding="utf-8"))["ip"])
    for name in (PUBLIC_CERT_NAME, "server.pem", "server.key"):
        if not (CERT_DIR / name).is_file():
            raise RuntimeError(f"Missing {name}; run setup again.")

    # The HTTP endpoint exists only to install the public certificate on phones.
    # The recording page and its assets are served by Uvicorn over HTTPS.
    downloader = ThreadingHTTPServer((ip, CERTIFICATE_PORT), CertificateDownload)
    thread = threading.Thread(target=downloader.serve_forever, daemon=True)
    thread.start()
    print(f"Install certificate: http://{ip}:{CERTIFICATE_PORT}/{PUBLIC_CERT_NAME}", flush=True)
    print(f"Then open recorder:  https://{ip}:{HTTPS_PORT}/capture", flush=True)
    print("Keep this terminal open. Ctrl+C stops both local servers.", flush=True)
    try:
        # Running a file from scripts/ otherwise puts that folder first on sys.path.
        sys.path.insert(0, str(PROJECT_DIR))
        import uvicorn

        uvicorn.run(
            "app.main:app", host=ip, port=HTTPS_PORT,
            ssl_certfile=str(CERT_DIR / "server.pem"),
            ssl_keyfile=str(CERT_DIR / "server.key"),
        )
    finally:
        downloader.shutdown()
        downloader.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    setup_command = commands.add_parser("setup", help="Generate project-local certificates without installing trust")
    setup_command.add_argument("--ip", required=True, help="Laptop's private Wi-Fi IPv4 address")
    commands.add_parser("serve", help="Start HTTPS recording page and public certificate download")
    args = parser.parse_args()
    try:
        if args.command == "setup":
            setup(args.ip)
        else:
            serve()
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Phone HTTPS setup failed: {error}\n")
