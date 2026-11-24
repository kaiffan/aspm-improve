# Воспроизведение

```sh
git worktree add -b feature/aspm-zero-finalize-flow /private/tmp/aspm-zero-finalize-flow 19cd7b4129de52e75eabaf0e07739e4c2b682f8e
# Configure an isolated development Docker Compose stack with PostgreSQL and private artifact volume.
COMPOSE_PROJECT_NAME=aspm-zero-finalize COMPOSE_FILE=.cache/zero-finalize/compose.json ./run-unittest.sh --test-case 'unittests.test_aspm_zero_finalize unittests.test_aspm_ingestion unittests.test_aspm_integration unittests.test_finding_write_concurrency unittests.test_finding_patch_concurrent_delete'
COMPOSE_PROJECT_NAME=aspm-zero-finalize COMPOSE_FILE=.cache/zero-finalize/compose.json ./run-unittest.sh --test-case unittests
node --test release/1.0.1/scripts/*.test.cjs
```

Секретный compose/runtime env не коммитится. Укажите собственные DB credentials и scopes service token. Исходные release branches и baseline containers не изменяются.

Через examples/aspm-ci/upload.sh отправьте Semgrep, откройте Commit evidence и дождитесь COMPLETED; затем независимо загрузите Trivy/Gitleaks. Проверьте findings, UNKNOWN coverage без declaration, FAILED history, выбор context при втором pipeline. POST reports с `{}` создаст новую версию без finalize; сохраните checksums, загрузите поздний scan и повторно проверьте прежнюю версию. Полный frozen performance campaign запускается только при достаточном свободном месте.


Для данного validation использовались свежие `test_aspm_zero_releasegate` и независимые runtime/малые A/B DB. После неудачного тестового preflight не переиспользуйте keepdb для финального gate без проверки fixture state. Полный suite выполнен в dev image с requirements-dev; production image не содержит vcr_unittest.

Image строится из `git archive 12dfcbe6bb0beb1cbe0bd411b2c26b820cb9d23a dojo` с [Dockerfile.candidate](Dockerfile.candidate). `scripts/verify_image_sources.py` проверяет каждый tracked Git blob в A/B images. Script paths для local qualification рассчитаны на приватный Docker runtime и volumes `/zero-qualification` и `/zero-runtime`; env/credentials должны принадлежать вашему изолированному стенду и не публиковаться.

`scripts/qualify_concurrency.py` ограничен runtime DB `aspm_zero`; worker fault controller проверяет ownership labels и работает только с `aspm-zero-runtime-*`. `scripts/benchmark_small.py` ограничен `aspm_zero_ab_a/b`; одинаковые CPU2 / RAM1536MiB, PostgreSQL CPU1 / RAM768MiB, native ARM64. Он выполняется последовательно, отдельно от full suites и HTTP worker traffic.

Standalone qualification scripts запрещают запуск Python с `-O`: ownership checks и behavioral oracles используют assertions. Последующая правка форматирования/guards этих scripts не изменяет application/test source или source SHA собранного image.
