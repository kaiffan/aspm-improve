"""Exercise ASPM webhook management over HTTP with its real broker and worker."""
# ruff: noqa: INP001 -- standalone CLI used by the cluster smoke
import argparse
import html
import json
import re
import sys
import time
from urllib.parse import urlsplit

import requests

ROOT = "/settings/integrations/webhooks/"


def extract(pattern, content, field):
    match = re.search(pattern, content)
    if not match:
        message = f"{field} was missing from the page"
        raise RuntimeError(message)
    return html.unescape(match.group(1))


class Browser:
    def __init__(self, origin, credentials):
        self.origin = origin
        self.session = requests.Session()
        login = self.get("/login")
        response = self.post("/login", login, credentials, expected=302)
        if "/login" in response.headers.get("Location", ""):
            message = "Lab account could not sign in"
            raise RuntimeError(message)

    def get(self, path, expected=200):
        response = self.session.get(self.origin + path, timeout=10, allow_redirects=False)
        check_status(response, expected)
        return response

    def post(self, path, source, data=None, *, expected):
        csrf = extract(r'name="csrfmiddlewaretoken" value="([^"]+)"', source.text, "CSRF token")
        response = self.session.post(self.origin + path, data={**(data or {}), "csrfmiddlewaretoken": csrf}, timeout=10, allow_redirects=False)
        check_status(response, expected)
        return response


def check_status(response, expected):
    if response.status_code != expected:
        message = f"{response.request.method} {urlsplit(response.url).path}: HTTP {response.status_code}, expected {expected}"
        raise RuntimeError(message)


def verify(condition, message):
    if not condition:
        raise RuntimeError(message)


def wait_for(get, message, seconds=120):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        result = get()
        if result:
            return result
        time.sleep(1.5)
    raise TimeoutError(message)


def webhook_form(fixture):
    return {
        "name": f"OrbStack qualification {fixture['suffix']}",
        "product_id": str(fixture["product_id"]),
        "repository_id": str(fixture["repository_id"]),
        "endpoint": "https://webhook-qualification.invalid/events",
        "enabled": "on",
        "events": "scan.completed",
        "scanner": "Generic Findings Import",
        "severity": "High",
        "timeout_seconds": 2,
        "max_attempts": 2,
        "rate_per_minute": 60,
    }


def create(browser, fields):
    new_webhook = browser.get(ROOT + "new/")
    response = browser.post(ROOT + "new/", new_webhook, fields, expected=200)
    verify("no-store" in response.headers.get("Cache-Control", ""), "Secret response must not be cached")
    secret = extract(r'id="webhook-secret" readonly value="([^"]+)"', response.text, "Signing secret")
    path = extract(r'href="(/settings/integrations/webhooks/\d+/)">Continue to delivery history', response.text, "History URL")
    return path, secret


def submit_scan(origin, fixture):
    api = origin + "/api/aspm/v1/scans/"
    headers = {"Authorization": "ASPM " + fixture["token"]}
    data = {
        "project_id": fixture["product_id"], "repository_id": fixture["repository_id"],
        "commit_sha": fixture["suffix"].ljust(40, "a"), "scanner_type": "Generic Findings Import",
        "idempotency_key": fixture["suffix"],
    }
    content = json.dumps({"findings": [{"title": "Synthetic webhook qualification", "description": "Lab fixture", "severity": "High"}]})
    response = requests.post(api, headers=headers, data=data, files={"file": ("scan.json", content, "application/json")}, timeout=20)
    check_status(response, 202)
    scan_id = response.json()["id"]

    def completed():
        status = requests.get(api + scan_id + "/", headers=headers, timeout=10)
        check_status(status, 200)
        body = status.json()
        verify(body["status"] != "FAILED", "Synthetic scan processing failed")
        return body["status"] == "COMPLETED" and body["finding_count"] == 1

    wait_for(completed, "Worker did not complete synthetic ingestion")


def get_attempts(browser, history, event, error):
    response = browser.get(history, 200)
    for row in re.findall(r"<tr>.*?</tr>", response.text, flags=re.DOTALL):
        if f"<td>{event}<br>" in row and "<td>DEAD<br>" in row and error in row:
            return extract(r'href="([^"]+/deliveries/[0-9a-f-]+/)">Attempts', row, "Attempt URL")
    return None


def qualify(origin, fixture):
    admin = Browser(origin, fixture["admin"])
    viewer = Browser(origin, fixture["viewer"])
    admin.get(ROOT)
    viewer.get(ROOT, 403)
    fields = webhook_form(fixture)
    form = admin.get(ROOT + "new/")
    invalid = admin.post(ROOT + "new/", form, {**fields, "endpoint": "https://127.0.0.1/events"}, expected=200)
    verify("Use a public HTTPS endpoint" in invalid.text and 'id="webhook-secret"' not in invalid.text, "Private endpoint was accepted")
    history, secret = create(admin, fields)
    unrelated, _ = create(admin, {**fields, "severity": "Critical", "name": fields["name"] + " unmatched"})
    viewer.get(history, 403)
    verify(secret not in admin.get(history).text and secret not in admin.get(history + "edit/").text, "Signing secret reappeared after creation")

    start = time.monotonic()
    submit_scan(origin, fixture)
    attempts = wait_for(lambda: get_attempts(admin, history, "scan.completed", "dns_failed"), "Expected DNS failure and retry exhaustion")
    attempts_page = admin.get(attempts)
    first_count = attempts_page.text.count("dns_failed")
    verify(first_count == 2, "Expected exactly two failed delivery attempts")
    verify("No deliveries yet" in admin.get(unrelated).text, "Severity filter accepted a non-matching scan")
    admin.post(attempts + "replay/", admin.get(history), expected=302)
    replay = wait_for(lambda: get_attempts(admin, history, "scan.completed", "dns_failed"), "Replay did not reach terminal state")
    verify(replay == attempts and admin.get(replay).text.count("dns_failed") == 4, "Replay did not retain delivery identity and attempts")

    rotation = admin.post(history + "actions/rotate/", admin.get(history), expected=200)
    new_secret = extract(r'id="webhook-secret" readonly value="([^"]+)"', rotation.text, "Rotated signing secret")
    verify(new_secret != secret and "no-store" in rotation.headers.get("Cache-Control", ""), "Secret did not rotate safely")
    admin.post(history + "actions/test/", admin.get(history), expected=302)
    wait_for(lambda: get_attempts(admin, history, "webhook.test", "dns_failed"), "Manual test event did not use the durable queue")
    admin.post(history + "actions/disable/", admin.get(history), expected=302)
    admin.post(history + "actions/test/", admin.get(history), expected=400)
    admin.post(unrelated + "actions/archive/", admin.get(unrelated), expected=302)
    verify("Archived" in admin.get(unrelated).text, "Archive did not preserve history")
    return {
        "status": "PASS", "origin": origin, "seconds": round(time.monotonic() - start, 2),
        "admin": 200, "project_viewer": 403, "private_ip_rejected_on_create": True,
        "one_time_secret_and_rotation": True, "real_scan_completed": True,
        "matching_severity_delivery_attempted": True, "nonmatching_severity_filtered": True,
        "dns_failure_attempts": first_count, "attempts_after_replay": 4,
        "same_delivery_on_replay": True, "manual_test_event": True,
        "disabled_test_rejected": True, "archived_history_preserved": True,
        "delivery_outcome": "dns_failed on a reserved .invalid hostname; no external receiver contacted",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("origin")
    args = parser.parse_args()
    origin = urlsplit(args.origin)
    if origin.scheme != "http" or origin.hostname not in {"localhost", "127.0.0.1"} or origin.username or origin.path not in {"", "/"}:
        parser.error("Expected an explicitly owned loopback ASPM origin")
    json.dump(qualify(args.origin.rstrip("/"), json.load(sys.stdin)), sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
