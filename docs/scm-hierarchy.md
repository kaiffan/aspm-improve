# Репозитории и коммиты в DefectDojo

Примените миграции и задайте `DD_ASPM_SCM_HIERARCHY=True` на web и worker. В карточке проекта появится вкладка Repositories. В ней доступны репозитории, коммиты, связанные Engagement и сравнение Finding между двумя коммитами одного репозитория. Доступ определяется правами существующего Product. [Архитектура и миграции](design/scm-hierarchy.md)

`/api/v2/repositories/` и `/api/v2/commits/` поддерживают CRUD. Для списков доступны фильтры по `product`, `provider`, `url` у репозиториев и по `repository`, `product`, `sha`, `branch` у коммитов. `Engagement.commit` представлен опциональным ID только при включённом флаге. Перенос Engagement в другой Product отсоединяет commit и сохраняет старые SCM-поля.

## Загрузка из CI

Пайплайн передаёт `repository_url`, полный `commit_hash`, `product_name`, необязательный `branch_tag` и стандартные поля импорта. Product уже должен существовать. Для явной привязки в import передайте `engagement`, в reimport — `test`. Объект должен принадлежать указанному проекту и совпадать с SCM-контекстом. При передаче `engagement_name` автоматический поиск ограничивается этим именем внутри коммита. Укажите `test_title`, если в одном коммите выполняется несколько сканов одного типа.

Обычный import создаёт новый Test, а автоматический reimport обновляет последний подходящий Test внутри выбранного коммита. `auto_create_context=true` разрешает создать Test при первом reimport. Повторный запуск того же CI-коммита переиспользует Repository, Commit и Engagement. Параллельные первые загрузки сериализуются при выборе Engagement.

Сохраните общий пример в `ci/defectdojo-upload.sh` в репозитории сканируемого приложения и передавайте токен из хранилища секретов CI.

```bash
#!/usr/bin/env bash
set -euo pipefail

curl --fail-with-body --silent --show-error --max-time 180 \
  --header "Authorization: Token ${DD_TOKEN:?}" \
  --form-string "product_name=${DD_PRODUCT_NAME:?}" \
  --form-string "repository_url=${SCM_REPOSITORY_URL:?}" \
  --form-string "commit_hash=$(git rev-parse HEAD)" \
  --form-string "branch_tag=${SCM_BRANCH:-}" \
  --form-string "scan_type=${DD_SCAN_TYPE:-Generic Findings Import}" \
  --form-string "test_title=${DD_TEST_TITLE:-CI security scan}" \
  --form-string 'auto_create_context=true' \
  --form "file=@${SCAN_FILE:?}" \
  "${DD_BASE_URL%/}/api/v2/reimport-scan/"
```

GitHub Actions. Добавьте шаг после checkout и генерации отчёта.

```yaml
- name: Import security scan
  env:
    DD_BASE_URL: ${{ vars.DD_BASE_URL }}
    DD_PRODUCT_NAME: ${{ vars.DD_PRODUCT_NAME }}
    DD_TOKEN: ${{ secrets.DD_TOKEN }}
    SCM_REPOSITORY_URL: ${{ github.server_url }}/${{ github.repository }}
    SCM_BRANCH: ${{ github.head_ref || github.ref_name }}
    SCAN_FILE: reports/dojo.json
  run: bash ci/defectdojo-upload.sh
```

GitLab CI. Настройте `DD_TOKEN` как masked variable и предоставьте job отчёт сканера как artifact.

```yaml
upload_security_scan:
  script:
    - export SCM_REPOSITORY_URL="$CI_PROJECT_URL" SCM_BRANCH="$CI_COMMIT_REF_NAME"
    - export SCAN_FILE=reports/dojo.json
    - bash ci/defectdojo-upload.sh
```

Jenkins. Задайте HTTP(S) `SCM_REPOSITORY_URL` в окружении job и храните токен как Secret text.

```groovy
withCredentials([string(credentialsId: 'defectdojo-api-token', variable: 'DD_TOKEN')]) {
    sh '''
        export SCM_BRANCH="${BRANCH_NAME:-}"
        export SCAN_FILE=reports/dojo.json
        bash ci/defectdojo-upload.sh
    '''
}
```

## Сравнение результатов

В деталях коммита выберите базовый коммит из того же репозитория. Интерфейс показывает `new`, `fixed` и `unchanged` для известных отпечатков. `fixed` здесь означает, что отпечаток присутствовал в базовом снимке и отсутствует в целевом. Для вывода об исправлении сопоставляйте отчёты одинаковых сканеров и одинакового охвата. Finding без hash и идентификатора сканера в сравнение не входит.
