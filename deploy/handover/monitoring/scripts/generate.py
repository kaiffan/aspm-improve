"""Build Grafana and Prometheus assets from reviewable source."""
# ruff: noqa: INP001
import json
import shutil
from pathlib import Path

import yaml

BUNDLE = Path(__file__).resolve().parents[1]
CHART = BUNDLE.parents[1] / "helm/aspm/observability"
SCOPE = "cluster,environment,namespace,release"
SEL = 'cluster=~"${cluster:regex}",environment=~"${environment:regex}",namespace=~"${namespace:regex}",release=~"${release:regex}"'
APP = 'application="aspm"'
BASE = APP + "," + SEL
DS = {"type": "prometheus", "uid": "${datasource}"}

DASHBOARDS = [
    ("aspm-control-center", "ASPM Operations Control Center", "01-aspm-control-center"),
    ("aspm-http-api", "ASPM HTTP & API Performance", "02-http-api-performance"),
    ("aspm-ingestion", "ASPM Scanner Ingestion & Celery", "03-ingestion-celery"),
    ("aspm-postgresql", "ASPM PostgreSQL & Database Performance", "04-postgresql"),
    ("aspm-kubernetes", "ASPM Kubernetes & High Availability", "05-kubernetes-ha"),
    ("aspm-integrations", "ASPM Reports, Webhooks & Integrations", "06-reports-webhooks-integrations"),
    ("aspm-pipeline", "ASPM Monitoring Pipeline", "07-monitoring-pipeline"),
    ("aspm-security", "ASPM Security Posture Overview", "08-security-posture"),
    ("aspm-slo", "ASPM SLIs & Error Budget", "09-sli-error-budget"),
]


def selector(name, filters="", base=BASE):
    return f"{name}{{{base}{',' + filters if filters else ''}}}"


def scoped(expr):
    return expr.replace("@", BASE)


def rate(name, labels="", unit="", filters=""):
    series = f"rate({selector(name, filters)}[$__rate_interval])"
    return f"sum by ({labels}) ({series}){unit}" if labels else f"sum({series}){unit}"


def quantile(name, percentile=0.95, labels="", filters=""):
    groups = "le" + (f",{labels}" if labels else "")
    return f"histogram_quantile({percentile}, {rate(name + '_bucket', groups, filters=filters)})"


def variable(name, metric, extra=""):
    query = f"label_values({metric}{extra}, {name})"
    return {
        "name": name, "label": name, "type": "query", "query": query, "definition": query,
        "datasource": DS, "refresh": 1, "includeAll": True, "multi": True, "allValue": ".*",
        "current": {"selected": True, "text": "All", "value": "$__all"},
        "sort": 1, "options": [],
    }


def section(title, panels):
    return title, panels


def panel(title, expr, unit, description, *, kind="timeseries", legend="", thresholds=None, link=None):
    return {
        "title": title, "description": description, "type": kind, "datasource": DS,
        "targets": [
            {"refId": chr(65 + index), "expr": item, "legendFormat": label,
             "instant": kind in {"stat", "bargauge", "table"}, "range": kind not in {"stat", "bargauge", "table"}}
            for index, (item, label) in enumerate(zip([expr] if isinstance(expr, str) else expr, [legend] if isinstance(legend, str) else legend, strict=True))
        ],
        "fieldConfig": {"overrides": [], "defaults": {
            "unit": unit, "noValue": "Нет данных",
            "mappings": [{"type": "special", "options": {
                "match": "null+nan", "result": {"text": "Нет данных", "color": "gray"},
            }}] if kind == "stat" else [],
            **({"thresholds": {"mode": "absolute", "steps": [{"color": color, "value": value} for value, color in thresholds]},
                "color": {"mode": "thresholds"}} if thresholds else {}),
        }},
        "options": {"legend": {"displayMode": "table", "placement": "bottom", "calcs": []},
                    "tooltip": {"mode": "multi", "sort": "desc"},
                    **({"colorMode": "value" if thresholds else "none", "graphMode": "none", "reduceOptions": {"calcs": ["lastNotNull"]}} if kind == "stat" else {})},
        **({"links": [{"title": "Открыть дашборд", "url": f"/d/{link}?${{__all_variables}}"}]} if link else {}),
    }


def stat(title, expr, unit, description, thresholds=None, link=None):
    return panel(title, expr, unit, description, kind="stat", thresholds=thresholds, link=link)


def record(name, expr):
    return {"record": "aspm:" + name, "expr": expr}


def build_rules():
    group = SCOPE
    app = '{application="aspm"'
    http = app + ',group!~"internal"}'
    duration_buckets = app + ',group!~"internal"}'
    rules = [
        record("http_rps:rate5m", f"sum by ({group}) (rate(aspm_http_requests_total{http}[5m]))"),
        record("http_5xx_ratio:rate5m", f"(sum by ({group}) (rate(aspm_http_requests_total{app},status=~\"5..\",group!=\"internal\"}}[5m])) or 0 * aspm:http_rps:rate5m) / on ({group}) (aspm:http_rps:rate5m > 0)"),
        record("http_p95_seconds:rate5m", f"histogram_quantile(0.95, sum by ({group},le) (rate(aspm_http_request_duration_seconds_bucket{duration_buckets}[5m])))"),
        record("scan_completion_p95_seconds:rate5m", f"histogram_quantile(0.95, sum by ({group},le) (rate(aspm_scan_phase_seconds_bucket{app},stage=\"acceptance_to_completion\"}}[5m])))"),
        record("scan_completed:rate5m", f"sum by ({group}) (rate(aspm_scan_events_total{app},result=\"completed\",component=\"worker\"}}[5m]))"),
        record("celery_workers:count", f'count by ({group}) ((time() - aspm_celery_heartbeat_timestamp_seconds{{application="aspm",component="worker"}}) < 20) or 0 * count by ({group}) (up{{application="aspm",component="worker"}})'),
        record("delivery_lag_seconds", 'max by (cluster,environment,namespace,release) (clamp_min(prometheus_remote_storage_highest_timestamp_in_seconds{application="aspm"} - ignoring(remote_name,url) group_right prometheus_remote_storage_queue_highest_sent_timestamp_seconds{application="aspm",remote_name="aspm-victoriametrics"}, 0))'),
    ]
    # Recording output needs application identity for the remote-write filter.
    for item in rules:
        item["labels"] = {"application": "aspm"}
    alerts = []

    def alert(name, expr, minutes, severity, summary, cause, dashboard, threshold):
        alerts.append({
            "alert": name, "expr": expr, "for": minutes, "labels": {"severity": severity, "team": "aspm-operations", "application": "aspm"},
            "annotations": {"summary": summary, "description": cause, "dashboard_uid": dashboard,
                            "threshold": threshold, "runbook": f"runbooks/OPERATIONS.md#{name.lower()}"},
        })

    for component, name, readable in (
        ("web", "ASPMWebScrapeUnavailable", "web"),
        ("worker", "ASPMWorkerScrapeUnavailable", "Celery"),
        ("beat", "ASPMSingletonScrapeUnavailable", "singleton"),
    ):
        alert(name, f'max by ({group}) (up{{application="aspm",component="{component}"}}) == 0', "2m", "critical",
              f"Все scrape targets {readable} недоступны", "Проверьте Pod, NetworkPolicy, TLS и авторизацию scrape.", "aspm-pipeline", "max(up) = 0")
    for source, label, uid in (("database", "PostgreSQL", "aspm-postgresql"),
                               ("broker", "Valkey", "aspm-ingestion"), ("storage", "EvidenceStorage", "aspm-kubernetes")):
        alert(f"ASPM{label}Unavailable", f'max by ({group}) (aspm_dependency_up{{application="aspm",source="{source}"}}) == 0', "2m", "critical",
              f"{label} недоступен", "Проверка singleton не вернула свежих данных. Проверьте журнал sidecar и зависимость.", uid, "probe = 0")
    alert("ASPMNoWorkerHeartbeat", "aspm:celery_workers:count == 0", "2m", "critical", "Нет heartbeat от Celery",
          "Возможны проблемы брокера, остановка процесса или перегрузка worker.", "aspm-ingestion", "0 worker")
    alert("ASPMHighHTTP5xx", f"aspm:http_5xx_ratio:rate5m > 0.05 and on ({group}) aspm:http_rps:rate5m > 1", "5m", "critical",
          "Доля HTTP 5xx выше 5%", "Проверьте ошибки приложения и его зависимости.", "aspm-http-api", ">5% при >1 запроса/с")
    alert("ASPMHighAPIP95",
          f'histogram_quantile(0.95, sum by ({group},le) (rate(aspm_http_request_duration_seconds_bucket{{application="aspm",group=~"api_v2|api_v3|ingestion"}}[5m]))) > 2 and on ({group}) aspm:http_rps:rate5m > 1',
          "10m", "warning", "p95 API выше 2 с", "Проверьте медленные маршруты, БД и конкуренцию за CPU.", "aspm-http-api", ">2 с")
    alert("ASPMScanNotProgressing", f'max by ({group}) (aspm_durable_oldest_seconds{{application="aspm",kind="scan"}}) > 900 and on ({group}) aspm:scan_completed:rate5m == 0',
          "5m", "critical", "ScanRun не продвигаются", "Проверьте состояние outbox, broker и worker heartbeat.", "aspm-ingestion", "старше 15 мин, завершений нет")
    alert("ASPMScanFailures", f'sum by ({group}) (increase(aspm_scan_events_total{{application="aspm",component="worker",result="failed"}}[15m])) >= 3',
          "2m", "warning", "Повторяющиеся ошибки ScanRun", "Проверьте тип сканера и журнал обработки.", "aspm-ingestion", "≥3 за 15 мин")
    alert("ASPMBrokerBacklogGrowing", f'sum by ({group},queue) (deriv(aspm_broker_queue_ready{{application="aspm"}}[10m])) > 0.1 and sum by ({group},queue) (aspm_broker_queue_ready{{application="aspm"}}) > 20',
          "5m", "warning", "Очередь Valkey растёт", "Сравните очередь, reserved и active прежде, чем масштабировать workers.", "aspm-ingestion", ">20 и прирост >0,1/с")
    alert("ASPMRemoteWriteStalled", "aspm:delivery_lag_seconds > 120", "3m", "critical", "Задержка remote write выше двух минут",
          "Возможны ошибки доступа, TLS, перегрузка VictoriaMetrics либо проблемы с WAL.", "aspm-pipeline", ">120 с")
    alert("ASPMRemoteWriteRetries", f'sum by ({group}) (rate(prometheus_remote_storage_samples_retried_total{{application="aspm",remote_name="aspm-victoriametrics"}}[5m])) > 1',
          "5m", "warning", "Prometheus повторяет отправку", "Проверьте ответы remote endpoint и рост очереди.", "aspm-pipeline", ">1 sample/с")
    alert("ASPMWebhookFailures", f'sum by ({group}) (increase(aspm_webhook_delivery_attempts_total{{application="aspm",outcome=~"retry|failed"}}[15m])) > 5',
          "3m", "warning", "Повторяющиеся ошибки вебхуков", "Проверьте доступность получателя и очередь повторных попыток.", "aspm-integrations", ">5 за 15 мин")
    alert("ASPMOIDCConnectivity", f'sum by ({group}) (increase(aspm_identity_events_total{{application="aspm",event="provider",result="unavailable"}}[10m])) >= 3',
          "2m", "warning", "Ошибки подключения к OIDC", "Проверьте DNS, CA и сетевой доступ Keycloak.", "aspm-integrations", "≥3 за 10 мин")
    for component in ("web", "worker", "beat"):
        workload = f'deployment=~".*-{component}",application="aspm"'
        diff = f'kube_deployment_spec_replicas{{{workload}}} - kube_deployment_status_replicas_available{{{workload}}}'
        alert(f"ASPMReduced{component.title()}Replicas", f'{diff} > 0', "5m", "warning", f"Реплик {component} меньше заданного числа",
              "Проверьте rollout, scheduling, probes и лимиты.", "aspm-kubernetes", "available < desired")
        if component != "beat":
            alert(f"ASPMNoReady{component.title()}Replicas", f'kube_deployment_status_replicas_available{{{workload}}} == 0',
                  "2m", "critical", f"Нет доступных реплик {component}", "Проверьте deployment и восстановите доступность.", "aspm-kubernetes", "available = 0")
    alert("ASPMMigrationJobFailed", 'kube_job_status_failed{application="aspm",job_name=~".*-migrate.*"} > 0',
          "2m", "critical", "Job миграции завершился ошибкой", "Проверьте журнал migration Job и совместимость схемы.", "aspm-kubernetes", ">0 ошибок Job")
    for threshold, severity, name in ((0.85, "warning", "ASPMEvidenceSpaceLow"), (0.95, "critical", "ASPMEvidenceSpaceCritical")):
        alert(name, f'1 - (aspm_evidence_filesystem_bytes{{application="aspm",state="available"}} / ignoring(state) aspm_evidence_filesystem_bytes{{application="aspm",state="total"}}) > {threshold}',
              "5m", severity, "На файловой системе evidence заканчивается место", "Сверьте PVC capacity и квоты CSI.", "aspm-kubernetes", f">{threshold:.0%}")
    for threshold, severity, name in ((0.85, "warning", "ASPMPVCSpaceLow"), (0.95, "critical", "ASPMPVCSpaceCritical")):
        alert(name, f'kubelet_volume_stats_used_bytes{{application="aspm"}} / (kubelet_volume_stats_capacity_bytes{{application="aspm"}} > 0) > {threshold}',
              "5m", severity, "Заполнение PVC", "Сверьте квоту, свободные inodes и доступность расширения.", "aspm-kubernetes", f">{threshold:.0%}")
    alert("ASPMCPUThrottling",
          'rate(container_cpu_cfs_throttled_periods_total{application="aspm",container!=""}[5m]) / (rate(container_cpu_cfs_periods_total{application="aspm",container!=""}[5m]) > 0) > 0.25',
          "10m", "warning", "Стойкий CPU throttling", "Сверьте CPU limits и нагрузку pod.", "aspm-kubernetes", ">25% CFS periods")
    alert("ASPMContainerMemoryHigh",
          'max by (cluster,environment,namespace,release,pod,container) (container_memory_working_set_bytes{application="aspm",container!=""}) / (max by (cluster,environment,namespace,release,pod,container) (kube_pod_container_resource_limits{application="aspm",resource="memory"}) > 0) > 0.9',
          "10m", "warning", "Рабочая память контейнера близка к лимиту", "Проверьте рост RSS, историю OOMKilled и нагрузку.", "aspm-kubernetes", ">90%")
    alert("ASPMPostgresExporterUnavailable", 'pg_up{application="aspm"} == 0', "2m", "critical",
          "PostgreSQL недоступен экспортёру", "Проверьте TLS, сеть и мониторинговую роль.", "aspm-postgresql", "pg_up = 0")
    alert("ASPMPostgresDeadlocks", 'sum by (cluster,environment,namespace,release) (increase(pg_stat_database_deadlocks{application="aspm"}[15m])) >= 2',
          "3m", "warning", "Повторные deadlocks PostgreSQL", "Изучите журнал PostgreSQL и конфликтующие операции.", "aspm-postgresql", "≥2 за 15 мин")
    alert("ASPMPostgresConnectionsHigh", 'sum without(state,datname) (pg_stat_activity_count{application="aspm"}) / pg_settings_max_connections{application="aspm"} > 0.8',
          "5m", "warning", "База ASPM занимает больше 80% лимита соединений", "Проверьте budget пулов и long-running transactions.", "aspm-postgresql", ">80%")
    alert("ASPMPostgresLockWaits", 'sum by (cluster,environment,namespace,release) (aspm_postgres_lock_waits{application="aspm"}) > 0',
          "5m", "warning", "Устойчивые lock waits", "Проверьте pg_stat_activity и блокирующие транзакции.", "aspm-postgresql", "ожидание >5 мин")
    return {"groups": [
        {"name": "aspm-recording", "interval": "30s", "rules": rules},
        {"name": "aspm-alerting", "interval": "30s", "rules": alerts},
    ]}


def build_panels():
    http = 'group!="internal",component="web"'
    scan = 'scanner=~"${scanner:regex}",component="worker"'
    pod = 'pod=~"${pod:regex}"'
    remote = 'remote_name="aspm-victoriametrics"'
    pvc = '1 - (aspm_evidence_filesystem_bytes{@,state="available"} / ignoring(state) aspm_evidence_filesystem_bytes{@,state="total"})'
    pg_capacity = 'sum without(state,datname) (pg_stat_activity_count{@}) / pg_settings_max_connections{@}'
    good = [(None, "red"), (1, "green")]
    data = {
        "aspm-control-center": [
            section("Состояние сервиса", [
                stat("Web scrape доступен", scoped('max(up{@,component="web"})'), "short", "Доступность scrape как сигнал от веб-подов. Проверку пользовательского пути выполняет ingress.", good, "aspm-pipeline"),
                stat("HTTP · запросов/с", rate("aspm_http_requests_total", filters=http), "reqps", "Запросы, обработанные Django.", link="aspm-http-api"),
                stat("HTTP p95", quantile("aspm_http_request_duration_seconds", filters=http), "s", "Квантили по сумме buckets всех нужных pod.", link="aspm-http-api"),
                stat("HTTP 5xx", scoped("aspm:http_5xx_ratio:rate5m{@}"), "percentunit", "Доля ошибок в окне 5 минут, при наличии запросов.", [(None, "green"), (0.01, "yellow"), (0.05, "red")]),
                stat("Web · готовые реплики", scoped('sum(kube_deployment_status_replicas_ready{@,deployment=~".*-web"})'), "short", "Kubernetes Deployment ready replicas.", link="aspm-kubernetes"),
                stat("Celery · живые workers", scoped("sum(aspm:celery_workers:count{@})"), "short", "Heartbeat моложе 20 секунд.", [(None, "red"), (1, "green")], "aspm-ingestion"),
                stat("ScanRun завершено/мин", rate("aspm_scan_events_total", unit=" * 60", filters=scan+',result="completed"'), "short", "Готовые результаты ScanRun с опубликованными наблюдениями.", link="aspm-ingestion"),
                stat("ScanRun · p95 до завершения", quantile("aspm_scan_phase_seconds", filters=scan+',stage="acceptance_to_completion"'), "s", "От создания ScanRun до терминального COMPLETED."),
                stat("Durable jobs", scoped("sum(aspm_ingestion_outbox_pending{@})"), "short", "Незавершённые scan/report jobs. Выборка ограничена 10 001 строкой."),
                stat("PostgreSQL · соединения", scoped(pg_capacity), "percentunit", "Сеансы из pg_stat_activity / max_connections.", link="aspm-postgresql"),
                stat("Evidence · занято", scoped(pvc), "percentunit", "Использование файловой системы, видимой из evidence volume.", [(None, "green"), (0.85, "yellow"), (0.95, "red")], "aspm-kubernetes"),
                stat("Remote write · lag", scoped("aspm:delivery_lag_seconds{@}"), "s", "Разница времён последней WAL sample и последней отправленной sample.", [(None, "green"), (30, "yellow"), (120, "red")], "aspm-pipeline"),
            ]),
            section("Сигналы за выбранный период", [
                panel("HTTP по группам", rate("aspm_http_requests_total", "group", filters=http), "reqps", "Поток Django по типу маршрута.", legend="{{group}}"),
                panel("Ошибки вебхуков", rate("aspm_webhook_delivery_attempts_total", "outcome", filters='outcome=~"retry|failed"'), "ops", "Сбой HTTP попытки с последующим retry либо терминальной обработкой.", legend="{{outcome}}"),
                panel("Состояние зависимостей", scoped("aspm_dependency_up{@}"), "short", "Результат последнего свежего singleton probe.", legend="{{source}}"),
                panel("Активные алерты", scoped('ALERTS{@,alertstate="firing"}'), "short", "Строка означает, что правило сработало.", kind="table"),
            ]),
        ],
        "aspm-http-api": [
            section("HTTP и API", [
                panel("RPS по группе", rate("aspm_http_requests_total", "group", filters=http+','+pod), "reqps", "Запросы на уровне Django.", legend="{{group}}"),
                panel("Ответы по классам", [rate("aspm_http_requests_total", filters=http+','+pod+f',status=~"{family}.."') for family in (2, 3, 4, 5)], "reqps", "Серии появляются после первого ответа соответствующего класса.", legend=["2xx", "3xx", "4xx", "5xx"]),
                panel("Задержка p50 / p90 / p95 / p99", [quantile("aspm_http_request_duration_seconds", q, filters=http+','+pod) for q in (.5, .9, .95, .99)], "s", "Buckets суммируются до вычисления квантилей.", legend=["p50", "p90", "p95", "p99"]),
                panel("Распределение latency", rate("aspm_http_request_duration_seconds_bucket", "le", filters=http+','+pod), "s", "Гистограмма времени обработки Django. Бакеты в секундах.", kind="heatmap", legend="{{le}}"),
                panel("Запросы в обработке", scoped(f'aspm_http_in_flight{{@,{pod}}}'), "short", "Мгновенный счётчик обработчиков Django.", legend="{{pod}}"),
                panel("Принятие upload · 202 p95", quantile("aspm_ingestion_acceptance_seconds", filters=pod), "s", "Время от входа в Django до ответа 202. Completion на панели ScanRun."),
                panel("Размер ответа p95", quantile("aspm_http_response_bytes", labels="group", filters=pod), "bytes", "Content-Length либо размер созданного тела ответа.", legend="{{group}}"),
                panel("Traffic на web pods", rate("aspm_http_requests_total", "pod", filters=http+','+pod), "reqps", "Распределение запросов по pod.", legend="{{pod}}"),
                panel("Медленные маршруты · p95", f'topk(10, {quantile("aspm_http_request_duration_seconds", labels="route", filters=http+","+pod)})', "s", "Первые 10 нормализованных route names, среди маршрутов с наблюдениями.", kind="bargauge", legend="{{route}}"),
                panel("Traefik 504 · timeouts", rate("traefik_service_requests_total", "service", filters='code="504"'), "reqps", "Timeouts, видимые Traefik на границе.", legend="{{service}}"),
            ]),
        ],
        "aspm-ingestion": [
            section("ScanRun и стадии", [
                panel("Принятые, дубликаты, завершённые, ошибки", rate("aspm_scan_events_total", "result", " * 60", 'scanner=~"${scanner:regex}",result=~"accepted|duplicate|completed|failed|retry|recovered"'), "short", "События за минуту. Повторная попытка учитывается отдельно.", legend="{{result}}"),
                panel("Findings и наблюдения/с", [rate("aspm_scan_findings_imported_total", "scanner", filters=scan), rate("aspm_scan_observations_total", "scanner", filters=scan)], "ops", "Новые Findings от импортера и отдельно опубликованные observations.", legend=["{{scanner}} findings", "{{scanner}} observations"]),
                panel("Стадии ScanRun · p95", quantile("aspm_scan_phase_seconds", labels="stage", filters=scan), "s", "Parser, reimport с dedup, snapshot, и время от принятия до запуска и завершения.", legend="{{stage}}"),
                panel("Доля успешных терминальных попыток", rate("aspm_scan_events_total", "scanner", filters=scan+',result="completed"') + " / (" + rate("aspm_scan_events_total", "scanner", filters=scan+',result=~"completed|failed"') + " > 0)", "percentunit", "Повторные исполнения учитываются отдельно.", legend="{{scanner}}"),
            ]),
            section("Доставка, очередь и workers", [
                panel("Durable jobs по состоянию", scoped("aspm_durable_jobs{@}"), "short", "Лимит выборки 10 001 строка на snapshot.", legend="{{kind}} · {{state}}"),
                panel("Возраст durable job", scoped("aspm_durable_oldest_seconds{@}"), "s", "Старейшая запись из ограниченной выборки.", legend="{{kind}} · {{state}}"),
                panel("Valkey ready / unacked", [scoped('aspm_broker_queue_ready{@,queue=~"${queue:regex}"}'), scoped("aspm_broker_unacked{@}")], "short", "Ready для заданных очередей, unacked по отдельному broker keyspace.", legend=["ready {{queue}}", "unacked"]),
                panel("Celery active / reserved", scoped('sum by(state) (aspm_celery_worker_tasks{@,component="worker"} and ignoring(state) (time() - aspm_celery_heartbeat_timestamp_seconds{@,component="worker"} < 20))'), "short", "Reserved исключает active, только свежие heartbeat.", legend="{{state}}"),
                panel("Возраст heartbeat", scoped('time() - aspm_celery_heartbeat_timestamp_seconds{@,component="worker"}'), "s", "Последний heartbeat от каждого worker.", legend="{{pod}}"),
                panel("Celery · опубликовано и исполнено", [rate("aspm_celery_published_total", "task"), rate("aspm_celery_tasks_total", "task,result")], "ops", "Успешно опубликованные задачи и результаты выполнения.", legend=["pub {{task}}", "{{task}} · {{result}}"]),
                panel("Celery · время выполнения p95", quantile("aspm_celery_task_seconds", labels="task"), "s", "Время выполнения по ограниченному типу задачи.", legend="{{task}}"),
                panel("Outbox · попытки отправки", rate("aspm_outbox_dispatch_total", "kind,result"), "ops", "Публикации durable jobs в broker.", legend="{{kind}} · {{result}}"),
            ]),
        ],
        "aspm-postgresql": [
            section("Подключение, сессии и throughput", [
                stat("Доступность PostgreSQL", scoped("min(pg_up{@})"), "short", "Соединение postgres_exporter с сервером.", good),
                stat("Connection utilization", scoped(pg_capacity), "percentunit", "Все видимые pg_stat_activity сессии / max_connections."),
                panel("Сессии по состоянию", scoped('sum by(datname,state) (pg_stat_activity_count{@,datname!=""})'), "short", "Доступность state зависит от прав monitoring role.", legend="{{datname}} · {{state}}"),
                panel("Commit / rollback", [rate("pg_stat_database_xact_commit", "datname"), rate("pg_stat_database_xact_rollback", "datname")], "ops", "Операции по базе.", legend=["{{datname}} commit", "{{datname}} rollback"]),
                panel("Deadlocks", rate("pg_stat_database_deadlocks", "datname"), "ops", "Счётчик PostgreSQL deadlocks с учётом reset.", legend="{{datname}}"),
                panel("Размер базы", scoped('pg_database_size_bytes{@,datname!=""}'), "bytes", "Размер базы, доступной экспортёру.", legend="{{datname}}"),
                panel("Cache hit ratio", scoped('rate(pg_stat_database_blks_hit{@}[5m]) / ((rate(pg_stat_database_blks_hit{@}[5m]) + rate(pg_stat_database_blks_read{@}[5m])) > 0)'), "percentunit", "Доля heap/index blocks, найденных в shared buffers.", legend="{{datname}}"),
                panel("Temp bytes и файлы", rate("pg_stat_database_temp_bytes", "datname"), "Bps", "Запись во временные файлы PostgreSQL.", legend="{{datname}}"),
                panel("WAL bytes/sec", rate("aspm_postgres_wal_bytes_total"), "Bps", "Singleton читает PostgreSQL pg_stat_wal.", legend="WAL"),
                panel("Longest transaction", scoped('pg_stat_activity_max_tx_duration{@,state=~"active|idle in transaction"}'), "s", "Самая долгая транзакция в наблюдаемой группе.", legend="{{datname}} · {{state}}"),
                panel("Checkpoint rate", [rate("pg_stat_checkpointer_num_timed_total"), rate("pg_stat_checkpointer_num_requested_total")], "ops", "KPI PostgreSQL 17+ с включённым stat_checkpointer.", legend=["timed", "requested"]),
                panel("Backend lock waits", scoped("aspm_postgres_lock_waits{@}"), "short", "Ungranted locks из pg_locks, включая shared objects."),
                panel("Lock counts по режиму", scoped("pg_locks_count{@}"), "short", "Lock modes, которые предоставляет postgres_exporter.", legend="{{datname}} · {{mode}}"),
                panel("Autovacuum runs", rate("pg_stat_user_tables_autovacuum_count", "datname"), "ops", "Агрегировано по БД, если stat_user_tables включён.", legend="{{datname}}"),
                panel("Replication lag", scoped("pg_replication_lag{@}"), "s", "Доступно с включённым replication collector при репликации.", legend="{{instance}}"),
                panel("Внешний сервер · CPU", scoped('1 - avg by(instance) (rate(node_cpu_seconds_total{@,mode="idle"}[5m]))'), "percentunit", "Подключайте только разрешённые targets отдельных хостов PostgreSQL.", legend="{{instance}}"),
            ]),
        ],
        "aspm-kubernetes": [
            section("Deployment и Pods", [
                panel("Desired / ready", [scoped('kube_deployment_spec_replicas{@}'), scoped('kube_deployment_status_replicas_ready{@}')], "short", "Deployment replicas из kube-state-metrics.", legend=["{{deployment}} desired", "{{deployment}} ready"]),
                panel("Pod phase", scoped('kube_pod_status_phase{@} == 1'), "short", "Текущее состояние pod по kube-state-metrics.", kind="table", legend="{{pod}}"),
                panel("Restarts", scoped('increase(kube_pod_container_status_restarts_total{@}[15m])'), "short", "Перезапуски контейнеров за 15 минут.", legend="{{pod}} · {{container}}"),
                panel("Последний OOMKilled", scoped('kube_pod_container_status_last_terminated_reason{@,reason="OOMKilled"} == 1'), "short", "Причина последнего завершения. Требуется kube-state-metrics.", kind="table"),
                panel("CPU", rate("container_cpu_usage_seconds_total", "pod,container", filters='container!="",'+pod), "cores", "Реальное использование CPU, в cores.", legend="{{pod}} · {{container}}"),
                panel("CPU throttling", scoped('rate(container_cpu_cfs_throttled_periods_total{@}[5m]) / (rate(container_cpu_cfs_periods_total{@}[5m]) > 0)'), "percentunit", "Доля CFS периодов с throttling.", legend="{{pod}} · {{container}}"),
                panel("Memory working set", scoped('container_memory_working_set_bytes{@,container!="",'+pod+'}'), "bytes", "Working set из kubelet/cAdvisor.", legend="{{pod}} · {{container}}"),
                panel("CPU requests / limits", [scoped('kube_pod_container_resource_requests{@,resource="cpu"}'), scoped('kube_pod_container_resource_limits{@,resource="cpu"}')], "cores", "Данные resource spec из kube-state-metrics.", legend=["{{pod}} {{container}} request", "{{pod}} {{container}} limit"]),
                panel("Memory requests / limits", [scoped('kube_pod_container_resource_requests{@,resource="memory"}'), scoped('kube_pod_container_resource_limits{@,resource="memory"}')], "bytes", "Данные resource spec из kube-state-metrics.", legend=["{{pod}} {{container}} request", "{{pod}} {{container}} limit"]),
                panel("PDB · disruptions allowed", scoped("kube_poddisruptionbudget_status_pod_disruptions_allowed{@}"), "short", "Допустимое число добровольных disruptions.", legend="{{poddisruptionbudget}}"),
                panel("HPA · current / desired", [scoped("kube_horizontalpodautoscaler_status_current_replicas{@}"), scoped("kube_horizontalpodautoscaler_status_desired_replicas{@}")], "short", "Появляется при включённом HPA и exporter.", legend=["{{horizontalpodautoscaler}} current", "{{horizontalpodautoscaler}} desired"]),
                panel("Scheduling blocked", scoped('kube_pod_status_scheduled{@,condition="false"} == 1'), "short", "Pod ещё не назначен на node.", kind="table"),
            ]),
            section("Сеть и storage", [
                panel("Traefik · ответы", rate("traefik_service_requests_total", "code,service"), "reqps", "Только разрешённые Traefik service labels.", legend="{{service}} · {{code}}"),
                panel("Traefik · p95", quantile("traefik_service_request_duration_seconds", labels="service"), "s", "Latency на уровне Traefik service.", legend="{{service}}"),
                panel("PVC · объём и расход", [scoped("kubelet_volume_stats_capacity_bytes{@}"), scoped("kubelet_volume_stats_used_bytes{@}")], "bytes", "Объём и расход от CSI/kubelet. Empty series означает отсутствие источника.", legend=["{{persistentvolumeclaim}} total", "{{persistentvolumeclaim}} used"]),
                panel("Evidence filesystem", scoped("aspm_evidence_filesystem_bytes{@}"), "bytes", "Файловая система изнутри pod. На shared volume может быть шире PVC quota.", legend="{{state}}"),
                panel("Evidence · ошибки", rate("aspm_storage_failures_total", "operation"), "ops", "Ошибки хранения и чтения артефактов.", legend="{{operation}}"),
                panel("Миграция · неудачные Jobs", scoped('kube_job_status_failed{@,job_name=~".*-migrate.*"}'), "short", "Данные видны, пока Job существует.", legend="{{job_name}}"),
            ]),
        ],
        "aspm-integrations": [
            section("Отчёты и артефакты", [
                panel("Отчёты по состоянию", rate("aspm_report_events_total", "kind,result", " * 60", 'result=~"requested|generated|failed"'), "short", "Lifecycle событий в минуту. Classic HTML измеряется на сервере.", legend="{{kind}} · {{result}}"),
                panel("Stage latency · p95", quantile("aspm_report_phase_seconds", labels="kind,stage"), "s", "Генерация и ожидание запуска generated отчёта.", legend="{{kind}} · {{stage}}"),
                panel("Размер файлов · p95", quantile("aspm_artifact_bytes", labels="format"), "bytes", "Размер загруженных отчётов scan и generated HTML/JSON.", legend="{{format}}"),
                panel("Сбои отчётов и ограничения", rate("aspm_report_events_total", "kind,result", filters='result=~"download_failed|integrity_failed|size_limit"'), "ops", "Ошибки скачивания, проверки артефактов и лимита размера.", legend="{{kind}} · {{result}}"),
            ]),
            section("Webhooks и идентификация", [
                panel("Доставки вебхуков", rate("aspm_webhook_delivery_attempts_total", "outcome"), "ops", "Результат каждой HTTP попытки.", legend="{{outcome}}"),
                panel("Webhook HTTP · классы", rate("aspm_webhook_http_total", "status_class"), "reqps", "Ответы HTTP по классам и no_response.", legend="{{status_class}}"),
                panel("Webhook latency · p95", [quantile("aspm_webhook_delivery_duration_seconds"), quantile("aspm_webhook_queue_wait_seconds")], "s", "HTTP попытка и ожидание до первой попытки.", legend=["HTTP", "queue"]),
                panel("Backlog / dead-letter", [scoped("aspm_webhook_outbox_pending{@}"), scoped("aspm_webhook_outbox_dead{@}")], "short", "Глобальные gauges только из singleton.", legend=["pending", "dead"]),
                panel("Возраст ожидающей доставки", scoped("aspm_webhook_outbox_oldest_seconds{@}"), "s", "Возраст старейшей записи в выборке."),
                panel("OIDC и доступ", rate("aspm_identity_events_total", "event,result"), "ops", "Исходы callback, provider connectivity, 403 и истечение управляемых сессий.", legend="{{event}} · {{result}}"),
            ]),
        ],
        "aspm-pipeline": [
            section("Scrape и TSDB", [
                panel("Targets up", scoped('up{@,component=~"${component:regex}"}'), "short", "Доступность по target.", legend="{{component}} · {{instance}}"),
                panel("Scrape duration", scoped("scrape_duration_seconds{@}"), "s", "Длительность последнего scrape.", legend="{{component}} · {{instance}}"),
                panel("Scraped samples", scoped("scrape_samples_scraped{@}"), "short", "Размер последнего scrape.", legend="{{component}} · {{instance}}"),
                panel("Активные серии TSDB", scoped("prometheus_tsdb_head_series{@}"), "short", "Число активных TSDB head series.", legend="{{instance}}"),
                panel("WAL bytes", scoped("prometheus_tsdb_wal_storage_size_bytes{@}"), "bytes", "Размер локального WAL.", legend="{{instance}}"),
                panel("Prometheus RSS", scoped('process_resident_memory_bytes{@,component="prometheus"}'), "bytes", "RSS процесса Prometheus.", legend="{{instance}}"),
            ]),
            section("Доставка в VictoriaMetrics", [
                panel("Отправлено / retry / dropped", [rate("prometheus_remote_storage_samples_total", filters=remote), rate("prometheus_remote_storage_samples_retried_total", filters=remote), rate("prometheus_remote_storage_samples_dropped_total", filters=remote), rate("prometheus_remote_storage_samples_failed_total", filters=remote)], "ops", "Отправленные samples и ошибки write queue.", legend=["sent", "retried", "dropped", "failed"]),
                panel("Samples в очереди отправки", scoped(f'prometheus_remote_storage_samples_pending{{@,{remote}}}'), "short", "Очередь в RAM. Дополнительные samples могут оставаться в WAL.", legend="{{instance}}"),
                panel("Число shards", scoped(f'prometheus_remote_storage_shards{{@,{remote}}}'), "short", "Текущее число параллельных потоков remote write.", legend="{{instance}}"),
                panel("Отставание доставки", scoped("aspm:delivery_lag_seconds{@}"), "s", "Watch alert локальным evaluator при длительном outage.", legend="{{release}}"),
                panel("Возраст последнего sample в источнике", scoped('time() - max(timestamp(up{@,component="web"}))'), "s", "В VictoriaMetrics показывает свежесть поступления samples."),
            ]),
        ],
        "aspm-security": [
            section("Агрегаты для SecOps", [
                stat("Проекты", scoped("aspm_security_projects{@}"), "short", "Все проекты. Требует opt-in securityPosture и доступа SecOps."),
                stat("Репозитории", scoped("aspm_security_repositories{@}"), "short", "Все зарегистрированные репозитории."),
                stat("Активные Findings", scoped("sum(aspm_security_active_findings{@})"), "short", "Активные записи live Findings с исключением false positives, duplicates, out of scope и mitigated."),
                panel("Активные Findings по severity", scoped("aspm_security_active_findings{@}"), "short", "Количество live Findings по каноническому severity.", legend="{{severity}}"),
                panel("Активность сканеров", rate("aspm_scan_events_total", "scanner,result", " * 60", 'result=~"completed|failed"'), "short", "Завершения и ошибки по разрешённому каталогу сканеров за минуту.", legend="{{scanner}} · {{result}}"),
                panel("Отчёты, сгенерированные за час", scoped('sum by(kind) (increase(aspm_report_events_total{@,result="generated"}[1h]))'), "short", "Число сформированных отчётов в скользящий час.", legend="{{kind}}"),
            ]),
        ],
        "aspm-slo": [
            section("Доступность и бизнес-SLI", [
                panel("HTTP · доля не-5xx", scoped("1 - aspm:http_5xx_ratio:rate5m{@}"), "percentunit", "HTTP SLI по Django, требует наблюдаемых запросов."),
                panel("ScanRun · доля успеха", rate("aspm_scan_events_total", filters=scan+',result="completed"') + " / (" + rate("aspm_scan_events_total", filters=scan+',result=~"completed|failed"') + " > 0)", "percentunit", "Успешные терминальные попытки / все терминальные попытки."),
                panel("ScanRun · completion p90", quantile("aspm_scan_phase_seconds", .9, filters=scan+',stage="acceptance_to_completion"'), "s", "Все наблюдаемые ScanRun. Acceptance workload 400 Findings проверяется отдельным тестом."),
                panel("Generated reports · доля успеха", rate("aspm_report_events_total", filters='kind="generated",result="generated"') + " / (" + rate("aspm_report_events_total", filters='kind="generated",result=~"generated|failed"') + " > 0)", "percentunit", "Успешные терминальные исходы / все терминальные исходы."),
                panel("Webhook · доля успешных попыток", rate("aspm_webhook_delivery_attempts_total", filters='outcome="success"') + " / (" + rate("aspm_webhook_delivery_attempts_total") + " > 0)", "percentunit", "Доля HTTP попыток с успешным сохранённым результатом."),
                panel("Burn rate · HTTP", scoped('aspm:http_5xx_ratio:rate5m{@} / 0.001'), "short", "Иллюстративный бюджет 0,1%, требуется утверждение владельцем."),
            ]),
        ],
    }
    return data


def make_dashboard(uid, title, sections):
    panels = []
    position = 0
    for title_row, children in sections:
        panels.append({"id": len(panels) + 1, "type": "row", "title": title_row, "collapsed": False,
                       "gridPos": {"x": 0, "y": position, "w": 24, "h": 1}, "panels": []})
        position += 1
        x, row_height = 0, 0
        for child in children:
            w, h = (6, 4) if child["type"] == "stat" else (12, 8)
            if x + w > 24:
                position += row_height
                x, row_height = 0, 0
            child["id"] = len(panels) + 1
            child["gridPos"] = {"x": x, "y": position, "w": w, "h": h}
            if child["type"] == "heatmap":
                child["options"] = {"calculate": False, "cellGap": 1, "color": {"mode": "scheme", "scheme": "Spectral"},
                                    "yAxis": {"unit": "s"}, "tooltip": {"show": True}}
                child["targets"][0]["format"] = "heatmap"
            panels.append(child)
            x += w
            row_height = max(row_height, h)
        if children:
            position += row_height
    variables = [
        {"name": "datasource", "label": "Источник", "type": "datasource", "query": "prometheus",
         "current": {"text": "${DS_PROMETHEUS}", "value": "${DS_PROMETHEUS}"}, "refresh": 1, "options": []},
    ]
    filters = [APP]
    for label in ("cluster", "environment", "namespace", "release"):
        variables.append(variable(label, "up", "{" + ",".join(filters) + "}"))
        filters.append(label + '=~"${' + label + ':regex}"')
    for label, metric in (("component", "up"), ("pod", "up"), ("scanner", "aspm_scan_events_total"), ("queue", "aspm_broker_queue_ready")):
        if any("${" + label + ":" in target["expr"] for item in panels for target in item.get("targets", [])):
            variables.append(variable(label, metric, "{" + ",".join(filters) + "}"))
    return {
        "__inputs": [{"name": "DS_PROMETHEUS", "label": "VictoriaMetrics", "type": "datasource",
                      "pluginId": "prometheus", "pluginName": "Prometheus"}],
        "uid": uid, "title": title, "description": "ASPM 1.0.1 · эксплуатационная телеметрия",
        "schemaVersion": 40, "version": 1, "refresh": "30s", "time": {"from": "now-1h", "to": "now"},
        "tags": ["aspm", "operations"], "templating": {"list": variables}, "panels": panels,
        "links": [{"title": "ASPM dashboards", "type": "dashboards", "asDropdown": True,
                   "includeVars": True, "keepTime": True, "tags": ["aspm"]}],
    }


def main():
    data = build_panels()
    for uid, title, filename in DASHBOARDS:
        path = CHART / "dashboards" / (filename + ".json")
        path.write_text(json.dumps(make_dashboard(uid, title, data[uid]), ensure_ascii=False, indent=2) + "\n")
        shutil.copyfile(path, BUNDLE / "dashboards" / path.name)
    rules = yaml.safe_dump(build_rules(), sort_keys=False, allow_unicode=True, width=1200)
    (CHART / "rules.yaml").write_text(rules)
    (BUNDLE / "prometheus" / "rules.yaml").write_text(rules)


if __name__ == "__main__":
    main()
