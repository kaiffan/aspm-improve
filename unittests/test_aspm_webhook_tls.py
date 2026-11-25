import hashlib
import hmac
import ssl
import tempfile
import threading
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

import urllib3
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from django.test import SimpleTestCase

from dojo.webhooks.transport import send


class WebhookRealTLSTests(SimpleTestCase):
    def test_real_verified_tls_http_and_receiver_hmac(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "consumer.example.com")])
        cert = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key())
                .serial_number(x509.random_serial_number()).not_valid_before(datetime.now(UTC) - timedelta(minutes=1))
                .not_valid_after(datetime.now(UTC) + timedelta(days=1))
                .add_extension(x509.SubjectAlternativeName([x509.DNSName("consumer.example.com")]), critical=False)
                .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True).sign(key, hashes.SHA256()))
        received = []

        class Consumer(BaseHTTPRequestHandler):
            def do_POST(self):
                received.append((self.headers, self.rfile.read(int(self.headers["Content-Length"]))))
                self.send_response(204)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *args):
                pass

        with tempfile.TemporaryDirectory() as directory:
            cert_path, key_path = Path(directory) / "cert.pem", Path(directory) / "key.pem"
            cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
            key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
            server = HTTPServer(("127.0.0.1", 0), Consumer)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(cert_path, key_path)
            server.socket = context.wrap_socket(server.socket, server_side=True)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            real_pool = urllib3.HTTPSConnectionPool

            def test_pool(address, *, port, **kwargs):
                self.assertEqual(address, "127.0.0.1")
                self.assertEqual(port, 443)
                return real_pool(address, port=server.server_port, ca_certs=str(cert_path), **kwargs)

            try:
                # Only this test's resolver/port seam maps the public policy onto its owned loopback TLS consumer.
                with patch("dojo.webhooks.transport.resolve_public", return_value="127.0.0.1"), patch("dojo.webhooks.transport.urllib3.HTTPSConnectionPool", side_effect=test_pool):
                    status = send("https://consumer.example.com/events", "qualification-secret", b'{"event":1}', "event-id", 2, delivery_id="delivery-id")
                self.assertEqual(status, 204)
                self.assertEqual(len(received), 1)
                headers, body = received[0]
                expected = "v1=" + hmac.new(b"qualification-secret", headers["X-ASPM-Timestamp"].encode() + b"." + body, hashlib.sha256).hexdigest()
                self.assertEqual(headers["X-ASPM-Signature"], expected)
                self.assertEqual(headers["Host"], "consumer.example.com")
                self.assertEqual(headers["X-ASPM-Event-ID"], "event-id")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
