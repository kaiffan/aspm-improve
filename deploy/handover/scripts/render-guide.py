"""Render the Russian deployment overview with ReportLab and the delivered SVGs."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
INK = colors.HexColor("#173A33")
ACCENT = colors.HexColor("#286A58")
MUTED = colors.HexColor("#465A52")
PAPER = colors.HexColor("#EFF4F0")
LINE = colors.HexColor("#D9E5DD")


def p(text, style="body"):
    return Paragraph(escape(text), styles[style])


def section(items, number, title, intro):
    items.extend([p(number, "eyebrow"), p(title, "title"), p(intro), Spacer(1, 11)])


def blocks(items, entries):
    for title, body in entries:
        items.extend([p(title, "header"), p(body)])


def table(items, rows, widths):
    header, *data = rows
    matrix = [[p(x, "label") for x in header], *[[p(x, "cell") for x in row] for row in data]]
    obj = Table(matrix, colWidths=widths, hAlign="LEFT", repeatRows=1)
    obj.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PAPER, colors.white]),
        ("LINEBELOW", (0, 1), (-1, -1), 0.35, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    items.extend([obj, Spacer(1, 10)])


def frame(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(50, 53, 545, 53)
    canvas.setFont("Regular", 9)
    canvas.setFillColor(MUTED)
    canvas.drawString(50, 34, "ASPM 1.0.1   /   Enterprise Delivery")
    canvas.drawRightString(545, 34, f"{doc.page:02d}")
    canvas.restoreState()


def figure(items, work, stem):
    target = work / (stem + ".png")
    subprocess.run(["rsvg-convert", "-w", "1450", str(ROOT / "architecture" / (stem + ".svg")), "-o", str(target)], check=True)
    graphic = Image(str(target), width=495, height=247.5)
    graphic.hAlign = "LEFT"
    items.extend([graphic, Spacer(1, 12)])


def build_pdf(output, work):
    manifest = json.loads((ROOT / "DELIVERY_MANIFEST.json").read_text())
    notes = [
        ("02", "Архитектура и потоки"),
        ("03", "Подготовка инфраструктуры"),
        ("04", "Установка и smoke"),
        ("05", "Эксплуатация и диагностика"),
        ("06", "Backup, restore и изменения"),
        ("07", "Статус и передача"),
    ]
    items = [
        Spacer(1, 34), p("КОРПОРАТИВНАЯ ПОСТАВКА  /  26 НОЯБРЯ 2026", "eyebrow"),
        p("ASPM 1.0.1", "cover"),
        p("Развёртывание и эксплуатация", "subtitle"),
        Spacer(1, 14), p("Рабочий экземпляр для SRE, DBA, IAM и владельца ASPM."),
    ]
    table(items, [
        ("Идентификация", "Значение"),
        ("Приложение", "1.0.1 · DefectDojo OSS 3.5.100"),
        ("Helm", manifest["chart_version"] + " · appVersion 1.0.1-enterprise-rc"),
        ("Кандидат", manifest["application_sha"][:12] + " · Linux/ARM64"),
        ("Статус", "PRODUCTION HOLD"),
    ], [147, 348])
    items.append(p("Содержание", "header"))
    table(items, [("Стр.", "Раздел"), *notes], [61, 434])
    items.append(PageBreak())

    section(items, "02   /   СИСТЕМА", "Архитектура и потоки",
            "Два web pod с nginx и Django, три worker и один активный Beat. Внешние сервисы планируются отдельно.")
    figure(items, work, "deployment")
    figure(items, work, "scan-flow")
    items.append(p("Модель данных и путь OIDC даны в docs/02_ARCHITECTURE.md."))
    items.append(PageBreak())

    section(items, "03   /   ДО НАЧАЛА", "Подготовка инфраструктуры",
            "Заполните checklists/INFRASTRUCTURE_INPUT.md и согласуйте окно staging с владельцами.")
    table(items, [
        ("Компонент", "Что подготовить"),
        ("Kubernetes", "Context, namespace, Linux arch, registry, два закреплённых image digest, квоты и запас на rollout."),
        ("PostgreSQL", "Выделенная DB и роль с правом миграций, FQDN, слоты и CA. SSL verify-full. Direct/session pooling."),
        ("Хранилище", "Два RWX PVC, UID 1001/GID 1337, fsync/atomic rename, snapshots и журнал целостности."),
        ("Broker и cache", "Независимые endpoints и URI в Secret. Ограниченный egress."),
        ("Ingress", "Class, hostname, доверенный сертификат и корректный proxy header. Egress к DNS/DB/IdP/broker."),
        ("Keycloak / AD", "Confidential client, PKCE S256, callback, ID token claims, доверенный CA, группы и TTL."),
    ], [126, 369])
    blocks(items, [
        ("Секреты", "Укажите references в site.yaml. Runtime Secret, CA PostgreSQL, Keycloak credential и TLS импортируются из утверждённого secret store."),
        ("Расчёт приложения", "Бюджет 16 vCPU / 32 GiB. Для Standard HA планируйте 100 соединений на выделенном PostgreSQL, учитывая резерв DBA и rollout."),
    ])
    items.append(PageBreak())

    section(items, "04   /   ПЕРВЫЙ ЗАПУСК", "Установка и smoke",
            "Команды запускаются из распакованного комплекта. Имена и параметры берутся из анкеты.")
    blocks(items, [
        ("1. Целостность", "shasum -a 256 -c SHA256SUMS. Все записи должны вернуть OK."),
        ("2. Конфигурация", "Скопируйте config/values-production.example.yaml в site.yaml. Заполните внешние references, digest, hostname и egress."),
        ("3. Preflight", "scripts/preflight.sh --context CONTEXT --namespace NAMESPACE --release aspm --profile ha --arch ARCH -f site.yaml"),
        ("4. Развёртывание", "scripts/deploy.sh --context CONTEXT --namespace NAMESPACE --release aspm --profile ha --arch ARCH -f site.yaml --apply"),
        ("5. Проверка", "Migration Job: Succeeded, Ready web/worker/Beat, health HTTP 200, Helm test Succeeded, опубликованный Login HTTP 200."),
        ("6. Проверка прав и данных", "Войдите через Keycloak тестовыми SecOps, Expert и User. В тестовом проекте выполните Legacy import, CI upload и скачайте HTML/JSON отчёт."),
    ])
    items.append(p("Local rehearsal с независимыми зависимостями описана в START_HERE.md."))
    items.append(PageBreak())

    section(items, "05   /   ДЕЖУРСТВО", "Эксплуатация и диагностика",
            "Сверяйте явный context и namespace. Сохраняйте redacted events, correlation ID и состояние Helm.")
    table(items, [
        ("Симптом", "Диагностика и проверка"),
        ("CrashLoop или migration", "Посмотрите init schema-and-storage, Job logs и database plan. DBA проверяет lock и резервную копию."),
        ("Ingress 502/503", "EndpointSlice, Ready реплик, TLS hostname, NetworkPolicy. Повторите запрос без client retries."),
        ("ScanRun завис или FAILED", "GET статуса, attempt, error_code, worker/Beat и oldest pending. Проверьте broker и storage."),
        ("Права пользователя", "Проверьте Keycloak claims, project ID, TTL. Протестируйте отдельную учётную запись."),
        ("Высокая нагрузка DB", "Активные сессии, waits, WAL и CPU. Сопоставьте всплеск с rollout, worker concurrency и отчётами."),
        ("Хранилище и целостность", "PVC Bound, free bytes и inodes. Сравните checksum, восстановите согласованную копию."),
    ], [156, 339])
    items.append(p("Полный runbook и эскалации находятся в docs/16_TROUBLESHOOTING.md."))
    items.append(PageBreak())

    section(items, "06   /   ДАННЫЕ", "Backup, restore и изменения",
            "Операции восстановления выполняет DBA с явно выбранной пустой целью. Согласуйте RPO, RTO и порядок switching.")
    blocks(items, [
        ("Backup", "Зафиксируйте согласованную точку записи. Снимите PostgreSQL dump, snapshot private evidence и media. Защитите ключи и файлы в штатном vault."),
        ("Restore", "Проверьте SHA-256. Запустите scripts/restore.sh с отдельным DB service и точным подтверждением цели. Сверьте миграции, счётчики, SHA-256 оригиналов и версии отчётов."),
        ("Upgrade", "Проверьте schema compatibility и lock impact на копии данных. Сохраните текущую Helm revision и image digests. Примените новый пакет через deploy."),
        ("Rollback", "Укажите успешную revision, письменный schema review и точное имя цели. Helm переключает манифесты. Решение по схеме, данным и трафику принимает DBA/SRE."),
    ])
    figure(items, work, "data-model")
    items.append(PageBreak())

    section(items, "07   /   ПЕРЕДАЧА", "Решение и открытые проверки",
            "Состояние конкретных gates и фактические журналы фиксируются в qualification/RELEASE_GATE.md.")
    table(items, [
        ("Граница", "Действие владельца"),
        ("Corporate staging и IAM", "Предоставить registry, namespace, TLS, PostgreSQL/CSI и тестовые AD группы. Пройти post-deployment."),
        ("AMD64", "Собрать и просканировать оба образа на согласованном Linux/AMD64 runner, проверить smoke."),
        ("Ёмкость и HA", "Выделить стенд Core9/Acceptance 1M, проверить отказ узла и внешних сервисов."),
        ("Security", "Разобрать оставшиеся findings, включая CVE-2026-6653. Утвердить окно и gates перед production."),
    ], [152, 343])
    blocks(items, [
        ("Контакты", "ASPM owner __________________________    SRE __________________________"),
        ("", "DBA __________________________________    IAM __________________________"),
        ("Дополнения", "Выверенные команды и подробные инструкции в редактируемых docs/ и checklists/; журнал чистой установки в qualification/."),
    ])
    SimpleDocTemplate(str(output), pagesize=A4, leftMargin=50, rightMargin=50, topMargin=55,
                      bottomMargin=72, title="ASPM 1.0.1 | Развёртывание и эксплуатация",
                      author="ASPM Release Engineering").build(items, onFirstPage=frame, onLaterPages=frame)


def font(pattern):
    return subprocess.check_output(["fc-match", "-f", "%{file}", pattern], text=True).strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--regular")
    parser.add_argument("--bold")
    args = parser.parse_args()
    pdfmetrics.registerFont(TTFont("Regular", args.regular or font("Arial:style=Regular")))
    pdfmetrics.registerFont(TTFont("Bold", args.bold or font("Arial:style=Bold")))
    styles = {}
    for name, size, leading, weight, color, after in [
        ("body", 11, 16, "Regular", MUTED, 10), ("cell", 10, 14, "Regular", INK, 0),
        ("label", 10, 14, "Bold", colors.white, 0), ("eyebrow", 10, 14, "Bold", ACCENT, 8),
        ("header", 13, 17, "Bold", INK, 4), ("title", 28, 34, "Bold", INK, 10),
        ("cover", 55, 65, "Bold", INK, 8), ("subtitle", 25, 32, "Regular", MUTED, 12),
    ]:
        styles[name] = ParagraphStyle(name, fontName=weight, fontSize=size, leading=leading, textColor=color,
                                      spaceAfter=after, alignment=TA_LEFT)
    with tempfile.TemporaryDirectory() as tmp:
        build_pdf(args.output, Path(tmp))
