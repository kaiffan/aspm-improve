# 08 | Сеть и TLS

| Направление | Минимальный доступ |
|---|---|
| Пользователь / CI → ingress | TCP 443, доверенный сертификат `ingress.tlsSecretName` и SNI `ingress.host` |
| Ingress → ASPM | ClusterIP → nginx 8080, точные `networkPolicy.ingressNamespace` и `ingressPodSelector` |
| ASPM → DNS | TCP/UDP 53, проверить namespace и NodeLocal DNS топологию CNI |
| ASPM → PostgreSQL | Частный FQDN, порт 5432 либо согласованный, TLS verify-full |
| ASPM → broker и cache | Утверждённые endpoints и порт, TLS |
| ASPM → Keycloak | TCP 443, issuer discovery/token/JWKS и userinfo, доверенный CA |
| Worker → webhook | Разрешённые HTTPS destinations. Ограничьте egress на сетевой границе |
| Prometheus → метрики | TCP 8081, согласованные selectors |

Объедините dependency CIDR/selectors в `networkPolicy.egress`. Проверьте поддержку NetworkPolicy CNI. Pre-install migration Job должен подключаться к DB до создания policy чарта. Ingress перезаписывает forwarded-proto и применяет согласованные лимиты upload, таймауты и drain. Установите secure cookies, `DD_SITE_URL` HTTPS, допустимые `DD_ALLOWED_HOSTS` и `DD_SECURE_PROXY_SSL_HEADER`. Проверяйте сертификат с хоста пользователя и из pod. Применяйте `curl --cacert` / `openssl s_client -verify_hostname` с доверенной CA.

Для TLS broker задайте в URI rediss параметр ssl_cert_reqs=required. Если используется частный CA, предоставьте доверенный bundle по согласованному пути в образе или через платформенный mount. Для TLS cache проверьте hostname, CA и PING в диагностическом Pod. Сверьте доверие рабочего Celery worker после запуска. [Параметры Celery 5.6](https://docs.celeryq.dev/en/v5.6.0/userguide/configuration.html#broker-use-ssl)
