# Политика размещения и завершения pod

| Workload | Реплики HA | PDB | Rolling и остановка |
| --- | ---: | --- | --- |
| Web | 2 | minAvailable 1 | maxUnavailable 0, maxSurge 1, grace 150 s |
| Worker | 3 | minAvailable 2 | maxUnavailable 0, maxSurge 1, warm shutdown, grace 960 s |
| Beat | 1 | — | Recreate, session advisory lock, grace 60 s |

Стандартный и throughput профили задают component-scoped hostname spread DoNotSchedule и zone preference ScheduleAnyway. В OrbStack hostname preference ScheduleAnyway. PDB применяется к voluntary eviction. Прямое удаление пода проверяет восстановление и обходит PDB.

[Живые PDB](raw/live-topology-final.txt) · [Kubernetes termination](https://kubernetes.io/docs/concepts/workloads/pods/pod-termination/)
