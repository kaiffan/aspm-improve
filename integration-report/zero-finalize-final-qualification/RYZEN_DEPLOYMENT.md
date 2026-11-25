# Изолированная лаборатория Ryzen

В доступной конфигурации нет Ryzen 7 5700X. Комплект рассчитан на Linux x86_64 и локальный Docker daemon. Preflight проверяет vCPU, RAM, CPU model, cgroup, типы файловых систем, размещение Docker и I/O. Заданы минимум 8 vCPU и 24 GiB доступной VM памяти, при том же наборе Compose caps для обоих вариантов.

Для каждого повтора PostgreSQL восстанавливается из одного sealed dump. Проверяются SHA-256 файла и fingerprint исходных Findings. PG volume, state, broker и runtime получают уникальный Compose project и ownership label. Успешная рабочая БД удаляется только после проверки project, database marker и integrity. Неудачная остаётся для диагностики. Stop сохраняет volumes и snapshot.

Нужны Git, Docker с Compose, Python 3.12+, Node, нативный Chromium Playwright и свободный loopback порт 48115. Codex на VM не требуется.

[Команды](REPRODUCE.md) · [Compose](native/compose.yml)
