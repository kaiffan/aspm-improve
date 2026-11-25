"""Add a private Keycloak HTTPS lab to a disposable ASPM Compose test stack."""
# ruff: noqa: INP001 -- standalone lab command
import argparse
import json
import re
from pathlib import Path

NGINX = """pid /tmp/nginx.pid;
events {}
http {
  include /etc/nginx/mime.types;
  default_type application/octet-stream;
  access_log off;
  client_body_temp_path /tmp/client-body;
  proxy_temp_path /tmp/proxy;
  fastcgi_temp_path /tmp/fastcgi;
  uwsgi_temp_path /tmp/uwsgi;
  scgi_temp_path /tmp/scgi;
  server {
    listen 48141 ssl;
    ssl_certificate /etc/nginx/tls.crt;
    ssl_certificate_key /etc/nginx/tls.key;
    client_max_body_size 52m;
    location /static/ { alias /usr/share/nginx/html/static/; }
    location ~ ^/static/dojo/(css/aspm.css|js/aspm(-evidence)?.js)$ {
      proxy_set_header Host $http_host;
      proxy_pass http://web:8000;
    }
    location / {
      proxy_set_header Host $http_host;
      proxy_set_header X-Forwarded-Proto https;
      proxy_pass http://web:8000;
    }
  }
}
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", help="Private Compose JSON for a dedicated development stack", type=Path)
    parser.add_argument("state", help="Directory created by prepare.py", type=Path)
    parser.add_argument("--nginx-image", required=True, help="Local application nginx image with compiled static assets")
    parser.add_argument("--sha", required=True, help="Full application source SHA")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-f0-9]{40}", args.sha):
        parser.error("--sha must be a full lowercase SHA")
    state = args.state.resolve()
    secrets = json.loads((state / "accounts.json").read_text())
    config = json.loads(args.base.read_text())
    services = config["services"]
    test = services["uwsgi"]
    if test["environment"]["DD_DATABASE_NAME"] != "aspm_final_integration" or services["postgres"]["environment"]["POSTGRES_DB"] != "aspm_final_integration":
        parser.error("The lab requires the dedicated aspm_final_integration database")
    config["networks"]["edge"] = {}
    services["keycloak"] = {
        "image": "quay.io/keycloak/keycloak:26.6.4",
        "command": ["start-dev", "--import-realm"],
        "environment": {
            "KC_HOSTNAME": "https://aspm-keycloak.test:48140", "KC_HTTPS_PORT": "48140",
            "KC_HTTPS_CERTIFICATE_FILE": "/opt/keycloak/conf/tls.crt", "KC_HTTPS_CERTIFICATE_KEY_FILE": "/opt/keycloak/conf/tls.key",
            "KC_BOOTSTRAP_ADMIN_USERNAME": "lab-admin", "KC_BOOTSTRAP_ADMIN_PASSWORD": secrets["admin"],
        },
        "ports": ["127.0.0.1:48140:48140"],
        "volumes": [
            f"{state}/realm.json:/opt/keycloak/data/import/realm.json:ro",
            f"{state}/aspm-keycloak.test.crt:/opt/keycloak/conf/tls.crt:ro",
            f"{state}/aspm-keycloak.test.key:/opt/keycloak/conf/tls.key:ro",
        ],
        "networks": {"isolated": {"aliases": ["aspm-keycloak.test"]}, "edge": {}},
    }
    runtime = test["environment"].copy()
    runtime.pop("DD_TESTING", None)
    runtime.update(DD_CACHE_URL="redis://cache:6379/0", DD_CELERY_BROKER_URL="redis://broker:6379/0",
                   DD_ASPM_API_ONLY="True", DD_ASPM_GIT_SHA=args.sha, DD_ASPM_WEBHOOKS_ENABLED="True")
    web = runtime | {
        "DD_ALLOWED_HOSTS": "localhost,127.0.0.1", "DD_SITE_URL": "https://localhost:48141", "DD_DEBUG": "True",
        "DD_SESSION_COOKIE_SECURE": "True", "DD_CSRF_COOKIE_SECURE": "True", "DD_SECURE_PROXY_SSL_HEADER": "True",
        "DD_ASPM_OIDC_ENABLED": "True", "DD_ASPM_OIDC_ISSUER": "https://aspm-keycloak.test:48140/realms/aspm-qualification",
        "DD_ASPM_OIDC_CALLBACK_URL": "https://localhost:48141/sso/callback", "DD_ASPM_OIDC_CLIENT_ID": "aspm",
        "DD_ASPM_OIDC_CLIENT_SECRET": secrets["secret"], "DD_ASPM_OIDC_CA_BUNDLE": "/app/keycloak-ca.crt",
        "DD_ASPM_OIDC_GROUP_TTL": "120",
    }
    services["web"] = {
        **test, "entrypoint": ["python", "manage.py", "runserver", "0.0.0.0:8000", "--noreload", "--insecure"],
        "environment": web, "volumes": [*test["volumes"], f"{state}/aspm-keycloak.test.crt:/app/keycloak-ca.crt:ro"],
    }
    services["worker"] = {
        **test, "environment": runtime,
        "entrypoint": ["celery", "--app=dojo", "worker", "--loglevel=WARNING", "--concurrency=2", "--prefetch-multiplier=1"],
    }
    services["beat"] = {**test, "environment": runtime, "entrypoint": ["python", "manage.py", "aspm_beat"]}
    (state / "nginx.conf").write_text(NGINX)
    services["tls"] = {
        "image": args.nginx_image, "entrypoint": ["nginx", "-g", "daemon off;"], "ports": ["127.0.0.1:48141:48141"],
        "depends_on": ["web"], "networks": ["isolated", "edge"],
        "volumes": [
            f"{state}/nginx.conf:/etc/nginx/nginx.conf:ro", f"{state}/localhost.crt:/etc/nginx/tls.crt:ro",
            f"{state}/localhost.key:/etc/nginx/tls.key:ro",
        ],
    }
    output = state / "compose.json"
    output.touch(mode=0o600)
    output.write_text(json.dumps(config, indent=2) + "\n")


if __name__ == "__main__":
    main()
