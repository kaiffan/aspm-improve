# Helm integration

Chart 0.1.0-rc.3 extends the existing rc.1 chart and rc.2 packaging fix. Its OIDC block is disabled by default. Configure issuer, client ID, exact callback, existing Secret and client-secret key. An optional CA Secret supplies issuer trust. Only the web container receives the OIDC secret. Shared runtime settings carry the default Engagement policy and optional branding variables. Scanner support comes from the application parser registry and policy metadata.

## Повторная проверка OrbStack

После освобождения места состояние узла изменилось на `DiskPressure=False`. PostgreSQL и два процесса Valkey запустились в выделенном namespace `aspm-lab-orbstack`, все три PVC получили тома. Локальные ARM64-образы собраны из `c5ed33b99c9a33afa1dcc3c220956d9424679180`.

Helm 4.2.0 отобразил порог свободного места в экспоненциальной записи, и первый migration job остановился при загрузке настроек Django. В чарте `0.1.0-rc.4` порог передаётся как десятичное целое. Прошли 14 тестов чарта, включая регрессию для порогов 1 и 5 ГиБ. Обновлённый migration hook завершился, поднялись две web-реплики, два worker и beat.

В свежей лабораторной БД для Classic import добавлена штатная справочная запись `Development`. Проведены Classic import/reimport, нативный HTML-отчёт, Git-скан без отдельного finalize, двусторонние ссылки Test–ScanRun и webhook smoke. Из macOS проверен HTTP 200 на странице входа через port-forward. CSS из контейнера побайтно совпал с исходником.

В ревизии 3 проверен upgrade с тестовой аннотацией, в ревизии 4 — rollback к ревизии 2. Контрольные суммы связанных Tests, Findings и исходного Git-артефакта совпали до upgrade, после него и после rollback. Проверка покрывает откат Helm с тем же образом приложения и той же схемой БД.

HTTP-hook `helm test` получал `Connection refused` из test pod при обращении к ClusterIP. Лабораторная проверка приложения и проверка этого сетевого пути имеют отдельные результаты. TLS ingress и корпоративный Keycloak/AD на этом стенде не проверялись. [Свидетельство повторной проверки](dual-raw/orbstack-retry.json)

Enable HTTPS egress to Keycloak with the existing NetworkPolicy values and restrict ingress reachability to approved components. The ingress must overwrite forwarded protocol and remove auth callback query strings from access logs. The nginx sidecar logs the path without the query string.

The existing pre-upgrade migration Job, private evidence PVC, worker lifecycle and health probes remain the deployment path. Helm lint, render, schema and Kubernetes-manifest validation are recorded independently of Kubernetes install or rollback.
