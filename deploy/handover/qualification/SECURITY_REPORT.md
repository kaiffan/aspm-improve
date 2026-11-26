# Security qualification

## Supply chain

Trivy 0.70.0 проверил оба ARM64 образа, Python, JavaScript, OS packages, licenses и secret patterns. SBOM CycloneDX относятся к конкретным финальным image config ID. Сводка с версиями и counts лежит в provenance. Результаты — идентификация известных advisories на дату проверки и материал для решения о риске.

| Finding | Решение |
|---|---|
| GHSA-6q48-6c7w-9gw2 | Старый pip содержал vendored certifi 2026.6.17, несмотря на pinned 2026.10.19 для приложения. После обновления pip 26.2.2 wheel с SHA-256 и проверки трёх trust stores advisory отсутствует в rescan |
| CVE-2026-6653 | Trivy помечает системный Debian 13 libxml2 Critical. Debian tracker указывает фикс для unstable и отмечает trixie как vulnerable. Не применяли неподдерживаемую замену системных библиотек. Владелец подтверждает дистрибутивный fix и перепроверяет точную сборку перед production |
| Остальные advisories | Провести triage по package/affected version и reachability, связанным APIs и ОС. Принятые на площадке исключения должны быть привязаны к digest и сроку |

Docker build analyzer указал ENV с именами DD_ADMIN_PASSWORD и METRICS_HTTP_AUTH_PASSWORD. Проверьте фактические значения при сборке: шаблоны имеют пустые defaults, initial credentials выдаются отдельно. Chart принимает runtime credential references, workloads запускаются non-root, с read-only root, drop ALL, RuntimeDefault seccomp и отключённым service account token automount. В Docker-источниках сохраняются LICENSE.md, NOTICE и файловые notices. Лабораторные provision контейнеры — отдельные компоненты репетиции.

Исходная snapshot-проверка нашла token/key patterns внутри тестовых отчётов legacy secret scanners. Эти fixtures исключены из source bundle. Не передавайте необработанные JSON результатов scanner secret detection.

[Advisory проекта certifi](https://github.com/certifi/python-certifi/security/advisories/GHSA-6q48-6c7w-9gw2) · [Примечания pip 26.2.2](https://pip.pypa.io/en/stable/news/#v26-2-2) · [Debian tracker](https://security-tracker.debian.org/tracker/CVE-2026-6653)

## Security приложения

Автоматические suites охватывают OIDC state/nonce/signature/expiration, safe redirects, issuer+subject, проектную авторизацию, привязку Engagement, private artifacts/reports, ограничение scope токена и webhook delivery. Live smoke проверяет запрет оригинала и отчёта при смене проектного scope. Покрытие идёт от серверных response и состояния БД.

На eee10e678c77 в ранее запущенном Kubernetes/TLS стенде local Keycloak прошли 6 профилей. SecOps видит admin pages, Expert получает 403, User видит ровно TEST/PAYMENTS/both/empty. Отзыв активной сессии был обнаружен через 119,31 с при TTL 120 с. Синтетический Keycloak и корпоративный AD имеют отдельные gates. Для конечной инфраструктуры требуется повторить access matrix и проверить привязку групп, ротацию, политический TTL и аудит.

Webhook TLS тест использует mock/test receiver. Реальный корпоративный consumer и управление egress остаются частью staging. Исходящая доставка использует HMAC, pin адреса DNS, проверяемый TLS, запрет redirects и отказ private addresses. Response body не удерживается. [Контракт](../integration-examples/WEBHOOK_CONTRACT.md)

Gitleaks v8.30.0 проверил диапазон origin/dev..release/aspm-1.0.1-handover. 199 generic-api-key hits в исторических отчётах и одном шаблоне. Из них 168 совпали с контекстом source/digest hash, одно с placeholder. 30 требуют ручного чтения владельцем исторических материалов. Все три каталога, содержащие совпадения, исключены из архивируемого исходного среза. Результат относится к проверенному диапазону истории.

Debian оценивает CVE-2026-6653 как Minor issue и отмечает отсутствие DSA для trixie. Trivy даёт Critical. Различие зафиксировано для владельца риска. Точная корпоративная достижимость и решение по системной библиотеке требуют проверки на согласованном staging.

Финальные ARM64 образы имеют отдельные SBOM. Приложение: 1 Critical, 125 High, 142 Medium, 109 Low, 26 Unknown по Trivy. Для nginx финальный image scan вернул 0 известных findings. В обоих образах secret detectors не нашли совпадений. Повторный secret scan отфильтрованного исходного среза дал 0 совпадений. Предупреждение scanner о Yarn Git URL означает неполное разрешение отдельного lockfile entry. [Отчёт Trivy](../provenance/TRIVY_SUMMARY.json) · [Ведомость исходного среза](../provenance/SOURCE_SCAN_SUMMARY.json)
