# 09 | Администрирование SecOps и Expert

Для первого запуска без Keycloak создайте bootstrap-учётную запись приватно интерактивной командой `python manage.py createsuperuser` из контейнера web. Передавайте доступ по политике организации и проверьте запись аудита.

## SecOps

1. В Classic создайте Product Type и Product. В DevSecOps этот Product доступен как Project. Назначьте владельца и проектную группу Keycloak.
2. Настройте Engagement в карточке Project. Доступны Default, Repository, Branch, Environment и Explicit. Для Explicit CI передаёт разрешённый `engagement_id` этого продукта. Repository policy имеет приоритет над Product policy.
3. Настройте Repository, выпустите токен с требуемыми scopes, сохраните его в CI vault. Назначьте владельца ротации.
4. В Access Management сверяйте OIDC mapping. В System Health проверяйте миграции, очереди, evidence. Для Webhooks назначайте владельца получателя и проверяйте подпись и историю delivery.

```bash
kubectl --context "$ASPM_CONTEXT" -n "$ASPM_NAMESPACE" exec -it \
  deployment/aspm-aspm-web -c web -- python manage.py aspm_ingestion_token \
  --product 123 --repository 456 --user ci-project-a --days 30 \
  --scopes submit,status,read,reports
```

Raw token отображается один раз. Запускайте без журналирования терминала. Для отзыва используйте `aspm_ingestion_token --revoke TOKEN_ID`, сверив ID и проверив новый токен.

## Expert

Откройте Findings и выберите Project/Severity/Status. Проверьте историю, контекст скана и evidence. При triage оставьте причину в комментарии. Для False Positive измените статус в карточке и проверьте её и следующую версию отчёта. Для Classic выберите Engagement/Test и Native HTML Report. Для DevSecOps выберите Commit и Reports. Опубликованная версия DevSecOps сохраняет исходное состояние.
