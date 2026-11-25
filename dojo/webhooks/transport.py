"""Pinned public DNS, verified TLS, no proxies or redirects, no response-body retention."""
import hashlib
import hmac
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as ResolverTimeout
from urllib.parse import urlsplit

import urllib3

from dojo.webhooks.validation import public_address, validate_endpoint

_resolvers = ThreadPoolExecutor(max_workers=4, thread_name_prefix="aspm-hook-dns")
_resolver_slots = threading.BoundedSemaphore(4)


class DeliveryError(Exception):
    pass


def resolve_public(host):
    if not _resolver_slots.acquire(blocking=False):
        msg = "dns_capacity"
        raise DeliveryError(msg)
    try:
        future = _resolvers.submit(socket.getaddrinfo, host, 443, type=socket.SOCK_STREAM)
    except BaseException:
        _resolver_slots.release()
        raise
    future.add_done_callback(lambda _: _resolver_slots.release())
    try:
        answers = future.result(timeout=1)
    except (OSError, ResolverTimeout) as error:
        msg = "dns_failed"
        raise DeliveryError(msg) from error
    addresses = sorted({entry[4][0] for entry in answers})
    if not addresses or any(not public_address(ip) for ip in addresses):
        msg = "ssrf_blocked"
        raise DeliveryError(msg)
    return addresses[0]


def signature(secret, timestamp, body):
    return "v1=" + hmac.new(secret.encode(), str(timestamp).encode() + b"." + body, hashlib.sha256).hexdigest()


def send(endpoint, secret, body, event_id, timeout, *, delivery_id):
    validate_endpoint(endpoint)
    url = urlsplit(endpoint)
    host = url.hostname.encode("idna").decode("ascii")
    address = resolve_public(host)
    timestamp = int(time.time())
    headers = {"Host": host, "Content-Type": "application/json", "User-Agent": "ASPM-Webhooks/1", "X-ASPM-Event-ID": str(event_id),
               "X-ASPM-Delivery-ID": str(delivery_id), "X-ASPM-Timestamp": str(timestamp), "X-ASPM-Signature": signature(secret, timestamp, body)}
    try:
        # Connect to the checked IP, while TLS SNI/certificate verification use the original host.
        with urllib3.HTTPSConnectionPool(address, port=443, server_hostname=host, assert_hostname=host, cert_reqs="CERT_REQUIRED", maxsize=1) as pool:
            response = pool.urlopen("POST", url.path or "/", body=body, headers=headers, redirect=False, retries=False,
                                    timeout=urllib3.Timeout(connect=timeout, read=timeout, total=timeout), preload_content=False)
            try:
                return response.status
            finally:
                response.close()
    except urllib3.exceptions.SSLError as error:
        msg = "tls_failed"
        raise DeliveryError(msg) from error
    except (urllib3.exceptions.HTTPError, OSError) as error:
        msg = "network_failed"
        raise DeliveryError(msg) from error
