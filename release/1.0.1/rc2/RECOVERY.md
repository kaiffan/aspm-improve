# Восстановление после прерывания 12 ноября 2026

Временные worktree, private configuration и незакоммиченные raw-результаты в `/private/tmp` исчезли после остановки среды. Ветка RC2 сохранилась на `25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb`; Docker images и database volumes сохранились. Ветка RC2 на GitHub до восстановления отсутствовала.

Ранее сообщённые промежуточные результаты без raw-файлов не включаются в итоговую сопоставимую серию. Измерения и проверки повторяются, evidence сохраняется в этом каталоге и коммитится. Постоянный worktree расположен в игнорируемом `.cache/aspm-1.0.1-rc2` исходного workspace; private credentials — в соседнем `.cache/aspm-rc2-private` (0700/0600), вне Git.

Существующие images не помечаются новым release alias без прохождения gates. Исходная БД и protected seed не пересоздаются; проверяются полные row fingerprints. Запись допускается только в существующей `aspm_rc2_validation`, Django suite — только в отдельном `dd-final-tests` PostgreSQL.
