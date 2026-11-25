# Provenance образов

| Вариант | Application SHA | Архитектура проверенного образа | Сверено Git blobs dojo |
|---|---|---|---:|
| A | 19cd7b4129de52e75eabaf0e07739e4c2b682f8e | Linux ARM64 | 2 262 |
| B | 25da29aaff229d3a815e223d8af8bdc4ecca7c5e | Linux ARM64 | 2 264 |

Image B ID sha256:6f276aa582690eecfab68c93e4679489d57525b836494dc29bbd6ed40504552b фактически использовался HTTP и worker. Локальный B наследует проверенный image с заменой двух изменённых файлов. Проверка содержимого повторена для A и B.

Native Linux AMD64 build **HOLD**. Build plan и Compose config проверены. Сценарий сборки проверяет архитектуру хоста и демона, точные Git revisions, OCI label, Python dependency inventory и blobs app image.

[Image IDs и changed files](raw/provenance.json) · [Build plan](raw/native-build-plan.json)
