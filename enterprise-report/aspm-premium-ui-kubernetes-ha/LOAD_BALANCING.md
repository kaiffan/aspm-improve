# HTTP, TLS и балансировка

Kubernetes ClusterIP aspm-aspm выбирает готовые nginx/Django pod. Вход, Projects/Reports, API и статика проверяются с новой TCP связью на каждый запрос. Сессии общие через PostgreSQL. Для lab Traefik работает в отдельном namespace и видит только свой TLS Secret. ExternalName ведёт к стабильному DNS приложения. Ingress не требует Service с публичным адресом.

CSS и JS ASPM имеют версию source SHA и кеш с revalidation через 60 секунд. Нужные байты проверяются на каждой готовой реплике. При одновременной работе разных версий endpoint может вернуть активы соседней версии. Для дальнейших несовместимых изменений требуется совместимая двухфазная публикация статики или общий versioned origin.

[Распределение](raw/load-balancing.txt) · [TLS](raw/ingress-http.txt) · [Rollout](FAILOVER_TEST_RESULTS.md)
