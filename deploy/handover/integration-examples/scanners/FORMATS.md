# Названия и форматы

```bash
integration-examples/curl/upload.sh 'Dependency Track Finding Packaging Format (FPF) Export' dtrack.json
integration-examples/curl/upload.sh 'Semgrep JSON Report' semgrep.json
integration-examples/curl/upload.sh 'Trivy Scan' trivy.json
integration-examples/curl/upload.sh 'KICS Scan' kics.json
integration-examples/curl/upload.sh 'Fortify Scan' fortify.xml
integration-examples/curl/upload.sh 'ffuf Scan' ffuf.json
```

Эти команды применяются в отдельных заданиях. Для каждого сканера задайте отдельный ключ, стабильный при повторах той же отправки. Для Fortify используется XML файл с расширением .xml. [Уровни квалификации](../../qualification/SCANNER_COMPATIBILITY.md)
