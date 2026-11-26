# Private evidence и media

Evidence и media claims остаются раздельными. Evidence хранит original scanner report и generated HTML/JSON. Runtime UID 1001/GID 1337 используют общие пути. Production CSI должен поддержать RWX, права, atomic rename и fsync. В OrbStack одна нода делит RWO local-path между pod.

Проверка сравнивает SHA-256 одного исходного артефакта и JSON-отчёта через два разных адреса web pod перед заменой и через готовые адреса после замены. Download требует авторизации и возвращает private/no-store.

[До замены](raw/storage-before.json) · [После замены](raw/storage-after.json)
