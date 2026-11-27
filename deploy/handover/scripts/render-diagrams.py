"""Rebuild the editable SVG architecture views."""
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS = {
    "deployment": (
        "Развёртывание Standard HA",
        [
            ("Клиенты", "Браузер · CI"), ("Ingress", "HTTPS · TLS"), ("ClusterIP", "Kubernetes Service"),
            ("Web × 2", "nginx + Django"), ("PostgreSQL", "Сессии · outbox · locks"),
            ("Workers × 3", "Celery · parser · reports"), ("Beat × 1", "Dispatcher · fencing"),
            ("Private storage", "Evidence и media · S3 / RWX"), ("Keycloak", "OIDC · AD federation"),
            ("Broker / cache", "Отдельные endpoints"),
        ],
        [(0, 1), (1, 2), (2, 3), (3, 4), (3, 7), (3, 8), (6, 4), (6, 9), (9, 5), (5, 4), (5, 7)],
        [(20, 100), (260, 100), (500, 100), (740, 100), (260, 245), (500, 245), (20, 245),
         (740, 245), (740, 390), (20, 390)],
    ),
    "data-model": (
        "Объекты и границы доступа",
        [
            ("Product Type", "Группировка"), ("Product / Project", "Область RBAC"), ("Engagement", "Политика назначения"),
            ("Test", "Classic import / reimport"), ("Finding", "Статус · triage"), ("Repository", "В пределах Project"),
            ("Commit", "Полный Git SHA"), ("ScanRun", "Idempotency · статус"), ("Observation", "Исторический снимок"),
            ("Evidence / Report", "Исходные bytes · версии"),
        ],
        [(0, 1), (1, 2), (2, 3), (3, 4), (1, 5), (5, 6), (6, 7), (7, 8), (7, 9)],
        [(20, 100), (260, 100), (500, 100), (740, 100), (740, 245), (260, 245),
         (260, 390), (500, 390), (740, 390), (500, 245)],
    ),
    "scan-flow": (
        "Приём и публикация результата",
        [
            ("CI upload", "Multipart · ASPM token"), ("API acceptance", "Scope · SHA · idempotency"),
            ("Atomic record", "ScanRun + durable outbox"), ("HTTP 202 / 200", "Клиент получает ScanRun ID"),
            ("Celery", "Beat → broker → worker"), ("Parser & matching", "Engagement · Test · Findings"),
            ("COMPLETED", "Immutable observations"), ("Reports", "Версии HTML / JSON"),
        ],
        [(0, 1), (1, 2), (2, 3), (2, 4), (4, 5), (5, 6), (6, 7)],
        [(20, 100), (260, 100), (500, 100), (740, 100), (500, 245), (260, 245), (260, 390), (500, 390)],
    ),
    "authentication-flow": (
        "Вход, связывание и обновление прав",
        [
            ("Браузер", "Переход на /sso/login"), ("Django start", "PKCE S256 · state · nonce"),
            ("Keycloak", "Authorization Code · AD"), ("Callback", "Проверка кода и ID token"),
            ("Связь аккаунта", "issuer + subject"), ("Role / grants", "Назначение по claims"),
            ("ASPM session", "Protected cookie · server state"), ("Refresh", "TTL · revoke · downgrade"),
        ],
        [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)],
        [(20, 100), (260, 100), (500, 100), (740, 100), (740, 245), (500, 245), (260, 245), (260, 390)],
    ),
}
WIDTH, HEIGHT = 200, 68


def connector(a, b):
    x, y = a
    tx, ty = b
    if y == ty:
        start, end = (x + WIDTH, tx) if x < tx else (x, tx + WIDTH)
        return f"M{start} {y + HEIGHT / 2} H{end}"
    start_y, end_y = (y + HEIGHT, ty) if y < ty else (y, ty + HEIGHT)
    middle = (start_y + end_y) / 2
    return f"M{x + WIDTH / 2} {start_y} V{middle} H{tx + WIDTH / 2} V{end_y}"


for stem, (title, nodes, links, positions) in DIAGRAMS.items():
    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="480" viewBox="0 0 960 480" role="img">',
        f"<title>{escape(title)}</title>",
        '<defs><marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">'
        '<polygon points="0 0, 6 3, 0 6" fill="#3D766D"/></marker></defs>',
        '<rect width="960" height="480" fill="#F4F7F4" rx="18"/>',
        '<rect x="20" y="27" width="10" height="38" fill="#226A59" rx="4"/>',
        f'<text x="45" y="55" font-size="30" font-weight="700" font-family="Arial,sans-serif" fill="#183731">{escape(title)}</text>',
    ]
    for src, dst in links:
        path = connector(positions[src], positions[dst])
        elements.append(f'<path d="{path}" fill="none" stroke="#3D766D" stroke-width="2" marker-end="url(#arrow)"/>')
    for (name, detail), (x, y) in zip(nodes, positions, strict=True):
        elements.extend([
            f'<rect x="{x}" y="{y}" width="{WIDTH}" height="{HEIGHT}" rx="10" fill="#FFFFFF" stroke="#B6CAC3"/>',
            f'<text x="{x+13}" y="{y+27}" font-size="17" font-weight="700" font-family="Arial,sans-serif" fill="#183731">{escape(name)}</text>',
            f'<text x="{x+13}" y="{y+49}" font-size="12" font-family="Arial,sans-serif" fill="#3D514C">{escape(detail)}</text>',
        ])
    elements.append("</svg>")
    (ROOT / "architecture" / f"{stem}.svg").write_text("\n".join(elements) + "\n")
