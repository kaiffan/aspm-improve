# Публикация master

Ветка `master` создана из ветки по умолчанию `codex/performance-round4` репозитория `kaiffan/aspm-improve`. Её исходный SHA `716efb463387f82a0d13d5eae2541ac6b7dfee96`. Согласован fast-forward для тестового развёртывания. Ревизия исходников образов `e2f3f244f478033f5137ccb1248ab9c3b5d577df` входит в публикуемое дерево.

Для подтверждения публикации сравните SHA из `git ls-remote origin refs/heads/master` с SHA согласованного дерева. Получите исходники отдельным `git clone --single-branch --branch master` и сравните SHA и дерево. Привязку сборки к исходникам проверьте по `application_sha` в `deploy/handover/DELIVERY_MANIFEST.json`. Порядок сборки и развёртывания указан в [START_HERE](../../deploy/handover/START_HERE.md).
