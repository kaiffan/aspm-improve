# Конкурентность

Критический Django suite выполняется с отдельными PostgreSQL и Valkey. 111 тестов за 30.468 с · OK. Обнаружено по группам: 111.

Включены тесты Finding PATCH, reimport, stale model, отдельно запущенного Celery worker, сигналов и audit history. Для первого пробного прогона memory broker не доставлял сообщение в отдельный worker. Результат этого прогона сохранён. Финальный harness использует общий Valkey и отдельные подключения к PostgreSQL. Полный live тест одновременного replay webhooks и три rolling updates остаются открыты.
