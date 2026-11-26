# Воспроизведение

Lab context orbstack, release aspm и namespace aspm-lab-orbstack должны быть явно разрешены для тестового воздействия. Сначала проверьте метку aspm-lab=true, версию кластера, Pod readiness, свободное место, текущую рабочую ревизию и SHA. Для отката на рабочую исходную сборку используется revision 7. Не экспортируйте фактические values с credentials в Git.

Для локальной сборки используйте deploy/labs/orbstack/build-candidate.sh и готовые совместимые ARM64 bases. Зафиксируйте source SHA. Разверните два образа с одинаковым 12-символьным тегом и используйте values-ha.yaml и values-ha-ingress.yaml вместе с приватными values текущей ревизии. Порядок команд, подготовка TLS и pinned Traefik описаны в инструкции лаборатории. [Команды OrbStack](../../deploy/labs/orbstack/README.md)

Для dry run уже существующего релиза используйте server-side apply с field manager helm и dry-run=server. У HTTP hook Pod используйте отдельное имя для dry run, поскольку Kubernetes не переписывает Pod spec с тем же именем. Выполните helm test и зафиксируйте реальные image IDs запущенных pod.

Для Chromium запустите checks/browser.cjs с аргументами каталог отчёта, приватный login file, приватный Keycloak fixture. Login file содержит URL, имя пользователя и пароль на трёх отдельных строках. Задайте NODE_PATH на установленный Playwright. Gateway certificate проверяется отдельно curl с cacert.

Для измерений создайте временный observer из checks/observer.yaml. Подайте в stdin проверочного Python процесса приватный JSON как присваивание creds или fixture перед кодом, без отображения в журнале. Для ClusterIP используйте http_probe.py. Аутентифицируйтесь один раз, затем ведите журнал HTTP и времени через стабильный Service. Для shared storage вызовите ingestion_probe.py в режиме storage с готовыми Pod IP и JSON результата генерации. Синтетические fixture создаёт проверенный provision_webhook_smoke.py в правильной БД.

Для Celery воспроизведите работу одного заранее выбранного ScanRun с ограниченной блокировкой создания тестовых метаданных, наблюдайте активную задачу по Celery inspect и прервите только её дочерний процесс в lab. После завершения временной блокировки проверьте invocations, replay ID, Finding count и checksum. При измерении масштаба держите ту же БД и начальные workload budgets, затем верните сохранённые requests и limits и 2 web / 3 worker.

[Ingress manifest](raw/ingress-controller.yaml) · [Application manifest](raw/lab-rendered.yaml) · [Логи](FAILOVER_TEST_RESULTS.md)
