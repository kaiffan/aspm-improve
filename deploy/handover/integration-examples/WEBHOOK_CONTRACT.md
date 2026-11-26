# Подпись Webhook

Заголовки запроса: X-ASPM-Event-ID, X-ASPM-Delivery-ID, X-ASPM-Timestamp, X-ASPM-Signature. ASPM отправляет исходные UTF-8 JSON bytes и timestamp. Подпись формируется как v1= + hex(HMAC-SHA-256(secret, ASCII(timestamp) + b'.' + body)). В получателе проверьте точное представление подписываемых байтов по `dojo/webhooks/transport.py` из архива исходников, валидируйте timestamp, сравнивайте HMAC через constant-time compare и дедуплицируйте по Delivery ID. Примите результат только после проверки подписи. Для replay ожидайте ту же идентичность delivery и примените свою политику повторов.

Удерживайте прежний и новый secret на согласованный период ротации. В отчёт проверки помещайте идентификатор delivery, timestamp, результат TLS и status, без payload и secret. [Администрирование](../docs/12_WEBHOOKS_GUIDE.md)
