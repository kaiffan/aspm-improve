# Старый и новый жизненный цикл

```mermaid
flowchart LR
  A[CI upload] --> B[ACCEPTED + original + outbox]
  B --> C[Celery PROCESSING]
  C --> D[COMPLETED + immutable observations]
  C --> E[FAILED remains in history]
  D --> F[Live Overview / Findings / ASPM Report]
  F --> G[Optional POST reports]
  G --> H[Short immutable membership transaction]
  H --> I[Async versioned HTML / JSON]
```

Раньше: upload → process → обязательный finalize для reports и сравнения; Findings суммировал успешные reruns. Теперь: upload → видимый ScanRun → process → видимые актуальные historical results. Другие scanners не задерживают публикацию уже готовых результатов.

Finalize сохраняется как необязательная legacy-фиксация. Историческая корректность требует immutable original, observations generation и точного membership для фиксированного экспорта; отдельная публичная команда для видимости не нужна.
