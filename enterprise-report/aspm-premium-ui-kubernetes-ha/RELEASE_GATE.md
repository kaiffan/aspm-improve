# Release gate

**Laboratory deployment активен. Production HOLD.**

| Контроль | Состояние |
| --- | --- |
| Ревизия Helm | 10, chart 0.1.0-rc.7 |
| Кандидат приложения | 6e88953f3cd8ce8119baafd73db23da6191ee4a7 |
| Точка отката | Revision 7, исходное приложение 2a44031af0631df3f18ff7b037874df31a8ee9eb |
| Топология | 2 nginx+Django, 3 Celery worker, 1 Beat, отдельный локальный TLS ingress |
| Корпоративная квалификация | external PostgreSQL/broker/cache, RWX/CSI с нескольких узлов, node failover, HPA, полный аудит WCAG и capacity остаются открытыми |

Перед выпуском нужны реальные инфраструктурные параметры, проверка корпоративных certificate / SSO mappings и наблюдаемость под рабочей нагрузкой. Результаты лаборатории относятся к одному узлу. В роли User поиск в шапке ведёт по разрешённым проектам. Документы включают измеренный первый отказ подключения и различия среды.

[Вход ASPM](http://127.0.0.1:18735/login) · [TLS lab](https://localhost:18736/login) · [Топология](raw/live-topology-final.txt) · [Проверка URL](raw/final-url-check.txt) · [Helm test после масштабирования](raw/helm-test-after-scaling.txt) · [Production input](EXTERNAL_INFRASTRUCTURE_INPUT.md)
