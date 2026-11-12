# Git / Docker provenance — ASPM 1.0.1 RC2

Рабочая ветка `release/1.0.1-rc2`, создана от проверенного RC1; исходный пользовательский checkout `feature/ha-orm-scm-engagements-ui-webhooks` на207c7740bcd9ac56bd8a496ad30aca3778b41b7b и его untracked файлы сохранены. Новый origin/dev или custom Engagements код не подмешивался.

## Почему RC1 имел два SHA

RC1 release HEAD `d153d109706749d4e7910e0c585a9ac760b98eba`; embedded source `5cdbc77fc9d4b8d0899069f5d44cd5241b2acae6`. Между ними release docs, QA evidence/helpers и packaging recipes; **нет изменений embedded dojo, static и dependency runtime**. Называть всю разницу только документацией было бы неточно. [Полный список путей и runtime comparison](rc2/raw/rc1-provenance.json).

Recipes могут влиять на запуск, поэтому сравнение использовало одинаковые фактические4×4 uWSGI, limits/env и pinned dependencies; labels отдельно не считались достаточной проверкой. [Actual runtime](rc2/raw/actual-runtime.json). В environment унаследован DD_INITIALIZE=true, но Compose запускает только явно указанные app/nginx/cache/worker, initializer service отсутствует и migrations не выполнялись.

## Источники сопоставимой серии

| Variant | Runtime source | App image ID | Nginx ID |
|---|---|---|---|
| Round 5 | `c6a6144ed93b83adb1fd4ea9daa2c5e417ecea37` | `sha256:b06ecb25fd6fa04308e585b54334a057963e366d066222441c622229a75b7499` | `sha256:ff576ccae3595858347f21bce8cb17588d50a29c26645e9056780fb4590b72e8` |
| RC1 | `5cdbc77fc9d4b8d0899069f5d44cd5241b2acae6` | `sha256:81eac7baeeb48d5f0fe725f586c9cbcf1e461286c00f39e2f9c8d3cf39f745c7` | `sha256:912110ae1ba8e1cb21cdb0b4599b5010cfa5e030975f378530dbd551d76dfb27` |
| RC2 | `25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb` | `sha256:40ccfda81142aa8482d0b05fb501684c3bc23df231169a069a02e1da51052f0c` | `sha256:82851226dc47f5756dc7d56fea0f43c851bc9e86df63682a549802875f06c411` |

## RC2

ASPM version **1.0.1**, channel **rc2**; upstream DefectDojo **3.5.100**. Frozen source **`25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb`**. `get_branding`, image ENV и OCI revision соответствуют ему. OCI created/DD_ASPM_BUILD_TIMESTAMP нормализованы к SOURCE_DATE_EPOCH (`2026-11-11T21:27:27Z`) для воспроизводимости; фактическое capture время — environment.json. Upstream internal version не переименована.

Проверены2233 app source/compiled files и40 tracked static files, mismatches0. Повторная сборка после восстановления дала **те же app/nginx content IDs**: [reproduced build](rc2/build-reproduced.json), [identity check](rc2/raw/build-reproducibility.json). Base dependencies закреплены digest в build-lock.json; GNU msgfmt и все28 translations записаны в manifest. Python dependencies идентичны трём вариантам.

Позднейшие RC2 commits содержат QA scripts, raw evidence и release docs. Их HEAD может отличаться от runtime source; проверять `git diff 25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb..HEAD -- dojo components requirements.txt requirements-dev.txt Dockerfile.django Dockerfile.nginx`: runtime diff должен быть пуст. Для Docker build всегда указывать точный sourceSHA, не изменяющийся HEAD.

RepoDigest отсутствует: images локальные, registry push не выполнялся. Приведён content image ID, не вымышленный registry manifest digest. Alias `aspm:1.0.1-rc2` и Stable1.0.1 **не promoted** из-за двух full-suite import errors. Кандидат доступен как `aspm-build:25fb63ae7b48` / `aspm-nginx-build:25fb63ae7b48`; его byte identity фиксирована IDs выше.
