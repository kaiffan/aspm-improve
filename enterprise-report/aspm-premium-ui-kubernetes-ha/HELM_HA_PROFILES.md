# Helm профили и ресурсы

| Профиль | Web / worker / Beat | Параметры |
| --- | --- | --- |
| Local | 1 / 1 / 1 | 200m / 384Mi requests Django, один узел |
| HA Standard | 2 / 3 / 1 | web pod requests 700m / 1088Mi, worker 600m / 1Gi, TLS, RWX, PDB |
| High-throughput | 2–3 / 3–4 / 1 | web aggregate limit 1750m / 2304Mi, worker 1500m / 2Gi, CPU HPA web и опциональный HPA worker |

Для стандартного профиля по limits steady state составляет 10.5 vCPU / 11 GiB. Один surge каждого компонента плюс migration Job дают 15.5 vCPU. Верхний HPA с surge и Job даёт 16 vCPU / 21.5 GiB. Terminating pod могут временно выйти за арифметику surge, это проверяется на целевом ресурсе. HPA исключает replicas из своего Deployment, требует Metrics API и в OrbStack проверен рендером.

[Линт](raw/helm-lint-profiles.txt) · [Standard](raw/profile-ha.yaml) · [High-throughput](raw/profile-high-throughput.yaml)
