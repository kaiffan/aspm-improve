# 15 | Upgrade и rollback

1. Зафиксируйте версии приложения/чарта, digest каждого образа, текущую Helm revision и значения. Проверьте `showmigrations --plan` на копии БД. Сравните database schema и rollback compatibility, оцените data migrations и lock time. Зафиксируйте backup и допустимое окно работ.
2. Выполните upgrade через `scripts/deploy.sh` с новым package и оверлеями. Контролируйте migration Job, endpoint readiness, ошибки клиентов и очередь. Перед следующим rollout дождитесь штатного завершения старых pod.
3. Если принято решение об откате, укажите успешную revision и документ schema-review с результатами, ссылкой на backup и решением DBA. Helm rollback переключает манифесты. Схема базы остаётся текущей.

```bash
helm history aspm --kube-context "$ASPM_CONTEXT" -n "$ASPM_NAMESPACE"
scripts/rollback.sh --context "$ASPM_CONTEXT" --namespace "$ASPM_NAMESPACE" --release aspm \
  --profile ha --arch "$ASPM_ARCH" --revision 4 --schema-review reviewed-schema.md \
  --confirm-target "$ASPM_CONTEXT/$ASPM_NAMESPACE/aspm/4" --url "https://$ASPM_HOST"
```

Проверьте smoke, backlog, старые и новые записи, hash артефактов. Если старое приложение несовместимо с уже применённой схемой, используйте forward fix либо утверждённое восстановление согласованных DB и PVC в отдельное окружение.
