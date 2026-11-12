# ASPM 1.0.1 RC2 — candidate build

Frozen source: `25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb` (upstream3.5.100; ASPM1.0.1, channelrc2). Build from this exact SHA with `scripts/build_images.py`, digest-pinned `build-lock.json`, empty context and GNU msgfmt. See [reproduction](rc2/REPRODUCE.md) and [provenance](RC2_GIT_PROVENANCE.md). Repeated app/nginx content IDs match the retained images.

Candidate tags: `aspm-build:25fb63ae7b48`, `aspm-nginx-build:25fb63ae7b48`. No registry digest is available. Full suite has two inherited import errors, so **do not promote** `aspm:1.0.1-rc2` or Stable1.0.1 yet. Later docs/QA commits do not change embedded source; check the runtime diff against the frozen SHA.

The RC1 procedure below is historical.

# Сборка ASPM 1.0.1 RC1

Версия продукта хранится в `dojo/aspm/release.json`: ASPM **1.0.1**, канал **rc1**, upstream **DefectDojo OSS 3.5.100**. Не заменяет upstream `dojo.__version__`. Точный SHA и image IDs находятся в `measurements/build-rc.json`.

Сборка экспортирует `dojo/`, LICENSE.md и NOTICE из Git, а не из изменяемой рабочей директории. Зависимости приложения и vendor static берутся из двух образов с проверенными digest в `build-lock.json`, тех же, что использовались для Round 5. Не используется `origin/dev` или `latest`. Шрифты, CSS, Alpine, Chart.js и остальные runtime-ресурсы обслуживаются локально; новых runtime-пакетов нет.

```sh
python3 release/1.0.1/scripts/build_images.py \
  --sha 5cdbc77fc9d4b8d0899069f5d44cd5241b2acae6 \
  --context /tmp/aspm-build-clean \
  --manifest /tmp/aspm-build-manifest.json
```

Нужны Docker/BuildKit, Git, Python 3, GNU gettext `msgfmt`; каталог context должен быть пустым. Все существующие django.po компилируются, их SHA256 записываются в manifest. SOURCE_DATE_EPOCH берётся из коммита, времена экспортированных файлов нормализуются. Сверка двух сборок сохранена в measurements; повторяемость не означает независимую проверку цепочки поставки.

Browser dev dependencies отдельно: `cd release/1.0.1/browser && npm ci`, затем установка Chromium через Playwright. Это зависимости проверки, в продуктовые образы они не входят. Пакеты закреплены в package-lock.json.

Локальные имена RC: `aspm:1.0.1-rc1` и `aspm-nginx:1.0.1-rc1`. Проверенные image IDs записаны в `measurements/release-images.json`. Не опубликован stable tag `1.0.1`; registry push не выполняется без настроенного registry. Сохранить переносимый пакет можно через `docker save` обоих RC-образов с последующим gzip и SHA256 вне Git.

Текущая проверенная платформа — локальный ARM64 Docker. Перед использованием на AMD64 необходима отдельная сборка/проверка соответствующих dependency images и повторение release gates.
