# Scanner compatibility

VERIFIED in this table denotes the named checked-in fixture through API acceptance, worker import, observations and report output. Corporate export variants require samples and independent qualification. Parser source versions are pinned by the application source tree. Scanner versions are recorded from CI metadata when supplied.

| Tool and format | Exact scan_type | Status | Mapping and identity exercised |
| --- | --- | --- | --- |
| Dependency-Track Finding Packaging Format JSON | `Dependency Track Finding Packaging Format (FPF) Export` | VERIFIED | `dependency_track/one_finding.json`. Parser tests cover version ranges, affected versions, alias/CVE selection, EPSS and 3.8.0 and 4.14.1 inputs. Dedup prefers the supplied identity, with a component, version and vulnerability-ID fallback. |
| Semgrep JSON | `Semgrep JSON Report` | VERIFIED | `semgrep/one_finding.json`. Rule, path, line, severity, CWE and repeated fingerprints are covered by parser tests. |
| Semgrep SARIF | `SARIF` | PARTIALLY VERIFIED | Parser test covers the checked-in Semgrep OWASP benchmark SARIF. The six-format worker scenario uses the separate JSON parser. |
| Trivy JSON schema 2 | `Trivy Scan` | VERIFIED | `trivy/scheme_2_many_vulns.json`. Tests cover target, package version, CVE, CVSS, severity, fixed versions, images, misconfigurations and Kubernetes shapes. |
| KICS JSON | `KICS Scan` | VERIFIED | `kics/many_findings.json`. Tests cover query/title, IaC path, line, severity and nullable fields. The existing hash includes file path, line, title, description and severity. |
| Fortify XML | `Fortify Scan` | VERIFIED | `fortify/fortify_few_findings.xml`. XML filename suffix is required for parser selection. |
| Fortify FPR | `Fortify Scan`, `Fortify Scan v2` | PARTIALLY VERIFIED | FPR parser tests cover audit state, snippets and v2 source line handling. Worker qualification used the XML fixture. |
| ffuf JSON | `ffuf Scan` | VERIFIED | `ffuf/ffuf_one_vuln.json`. Parser uses result URL and discovery details and maps discoveries to Info. Existing hash uses title and endpoints. |
| Corporate “FF” export | Pending business identification | BLOCKED BY MISSING SAMPLE | Both checked-in candidates have independent fixture results. The corporate integration owner must provide the tool and export/version. |

The Dependency-Track test set exercises component versions and scanner-provided identifiers. PURL is not exported as a dedicated Finding field by this parser. Trivy, KICS and Fortify dedup settings are inherited at this checkpoint.

Parser tests use sanitized in-repository reports. Generated artifacts preserve parser results and live triage is exercised through the ordinary Finding write path. Existing dedup keys are unchanged. No remapping operation or mass rehash is required.

Examples use the same multipart upload helper for each known format. Keep the original filename extension, set `ASPM_URL`, `ASPM_TOKEN`, `ASPM_PROJECT_ID`, `ASPM_REPOSITORY_URL` and the full `CI_COMMIT_SHA` in CI.

```sh
upload() {
  curl --fail-with-body "${ASPM_URL}/api/aspm/v1/scans/" \
    -H "Authorization: ASPM ${ASPM_TOKEN}" \
    -H "Idempotency-Key: ${CI_JOB_ID}/${CI_JOB_ATTEMPT:-1}/$3" \
    -F "project_id=${ASPM_PROJECT_ID}" \
    -F "repository_url=${ASPM_REPOSITORY_URL}" \
    -F "commit_sha=${CI_COMMIT_SHA}" \
    --form-string "scanner_type=$1" \
    -F "file=@$2"
}
upload 'Dependency Track Finding Packaging Format (FPF) Export' 'dependency-track.json' dtrack
upload 'Semgrep JSON Report' 'semgrep.json' semgrep
upload 'Trivy Scan' 'trivy.json' trivy
upload 'KICS Scan' 'kics.json' kics
upload 'Fortify Scan' 'fortify.xml' fortify
upload 'ffuf Scan' 'ffuf.json' ffuf
```
