# Release gate

**HOLD для интеграции в релиз: полный frozen Core9 / mandatory acceptance A/B на 1M не выполнен из-за disk gate.** Функциональный zero-finalize candidate проверен. Stable, registry push, release branches и PR не изменялись.

## Пройдено

- Full Django: 8294 passed / 553 skipped / 0 failures/errors; baseline fresh repeat 8277 / 553 / 0.
- JavaScript 17/17; strict API-only 52/52.
- Real concurrent ingestion/export integrity, idempotency/conflict, FAILED history.
- Настоящие broker outage и SIGKILL/restart worker; тот же Test и 3000 observations после recovery.
- Browser smoke пяти вкладок; HTTP/Celery acceptance и exports без finalize, включая immutable image.
- Migration drift, Django checks, основная/ASPM OpenAPI validation.
- Immutable membership 0316, old report bytes, protected source и fingerprint защищённого 1M seed.
- Git/image source identity: B 2264/2264 tracked dojo blobs, A 2262/2262.
- Свежий малый диагностический A/B на идентичных копиях fixture DB.

## Осталось до релизной интеграции

Освободить достаточное место либо перенести frozen 1M stand на подходящий host и выполнить полный Core9 + mandatory acceptance A/B, включая PostgreSQL CPU, concurrent throughput, peak worker RSS и storage/WAL в целевом масштабе. Текущий guard требует 13,096,679,103 bytes перед clone; доступно 7,860,330,496. Порог 6 GiB и buffer 2 GiB не снижались. Новые результаты нельзя смешивать со старыми Mac/RC4 measurements.

После этих gates нужен review кандидата и явное решение об интеграции/релизе. Локальный image ARM64; подготовка не является публикацией Stable или доказательством другой архитектуры.

Application SHA: `12dfcbe6bb0beb1cbe0bd411b2c26b820cb9d23a`.
Image: `aspm-zero-finalize:12dfcbe6bb0b`, ID `sha256:edf74628cbd9f448d87713a1c2d56440bdae3e29d80d1264bcf6409b9d3b4fe8`.
[Provenance](checks/image-provenance.json), [disk gate](checks/performance-disk-gate.json).
