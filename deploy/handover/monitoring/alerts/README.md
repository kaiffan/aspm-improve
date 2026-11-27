# Правила ASPM

Используйте [Prometheus rules](../prometheus/rules.yaml) с одним evaluator. Для Dedicated Prometheus включите `monitoring.rules.enabled`. При наличии Operator chart создаёт PrometheusRule. Для vmalert можно использовать rules file и query endpoint VictoriaMetrics. Правила локальной доставки и dead-man monitor оценивайте там, где даже во время сбоя доступны свежие данные. Для Grafana-managed alerting перенесите выражения в единственный выбранный evaluator.

Выражения, severity, команда, окно, порог и UID панели есть в YAML. В chart переопределяйте `monitoring.rules.thresholds.<AlertName>.expr` и `duration`. Для ссылок на страницы дежурных укажите `monitoring.rules.runbookBase` и `grafanaBase`. Пороги поставки предназначены для первого прогона staging.

Acceptance для Import 400 Findings (110 с), Finding Browser Open (60 с), Finding POST (5 с) и Native HTML Report E2E (70 с) измеряет p90 отдельных приёмочных сценариев. HTTP latency и скользящий p90 всех ScanRun описывают другие рабочие SLIs.
