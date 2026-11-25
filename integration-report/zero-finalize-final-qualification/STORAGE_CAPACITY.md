# Диск, CPU, память и I/O

На Mac свободно около 7,9 GiB. В Docker измерено около 7,49 GiB. Исходный guard требует 12,2 GiB для одной копии существующего 1M seed с запасом.

Для native lab заложен 51 GiB перед инициализацией. Состав оценки в GiB: seed 6, dump 4, restore 6, WAL 5, images/build 10, observations/indexes 3, выгрузки и raw 5, маржа 6 и постоянный guard 6. После замера реального seed бюджет проверяется перед восстановлением и во время нагрузки. Docker root и state filesystem проверяются отдельно. Probe записывает и синхронизирует 128 MiB на state и на PG volume лаборатории.

| Локальный профиль за 17,79 с | Наблюдение |
|---|---:|
| PostgreSQL CPU | 10,35 CPU-с |
| HTTP / worker CPU | 4,06 / 8,48 CPU-с |
| WAL по разнице LSN | 17 904 176 B |
| PostgreSQL cgroup I/O, read / write | 5 001 216 / 83 042 304 B |
| Прирост БД / observations с индексами | 7 929 856 / 1 679 360 B |
| Прирост файлов evidence | 207 708 B |
| PostgreSQL / HTTP / worker cgroup memory peak | 422 / 374 / 434 MiB |

CPU PostgreSQL, cgroup I/O и WAL относятся к общему лабораторному PG instance. Дельты базы zf_load составили 326 считанных блоков, 3 323 299 cache hits и 0 temp bytes. PostgreSQL I/O timing на локальном профиле выключен. Memory peak берётся со старта контейнера и включает cache. Отдельный RSS процесса запрошен в SQL-трассах. Native профиль включает track_io_timing, pg_stat_io и pg_stat_statements с planning.

[Машинная сводка](raw/load-summary.json) · [Restore rehearsal](raw/local-restore.json) · [Native budget](raw/native-campaign-plan.json)
