{{- define "aspm.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- define "aspm.fullname" -}}
{{- default (printf "%s-%s" .Release.Name (include "aspm.name" .)) .Values.fullnameOverride | trunc 54 | trimSuffix "-" -}}
{{- end -}}
{{- define "aspm.labels" -}}
app.kubernetes.io/name: {{ include "aspm.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | quote }}
{{- end -}}
{{- define "aspm.selector" -}}
app.kubernetes.io/name: {{ include "aspm.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
{{- define "aspm.image" -}}
{{- if .digest -}}{{ printf "%s@%s" .repository .digest }}{{- else -}}{{ printf "%s:%s" .repository .tag }}{{- end -}}
{{- end -}}
{{- define "aspm.env" -}}
{{- if hasKey .Values.config "DD_ASPM_OIDC_CLIENT_SECRET" -}}
{{- fail "Set oidc.existingSecret and oidc.clientSecretKey for the OIDC credential" -}}
{{- end -}}
{{- range $key, $value := .Values.config }}
- name: {{ $key }}
  value: {{ $value | quote }}
{{- end }}
- name: DD_ASPM_STORAGE_MIN_FREE_BYTES
  value: {{ .Values.storage.minimumFreeBytes | int64 | quote }}
{{- $secret := .Values.existingSecret }}
{{- range $env, $key := dict "DD_SECRET_KEY" .Values.secretKeys.secretKey "DD_CREDENTIAL_AES_256_KEY" .Values.secretKeys.credentialKey "DD_DATABASE_URL" .Values.secretKeys.databaseUrl "DD_CELERY_BROKER_URL" .Values.secretKeys.brokerUrl "DD_CACHE_URL" .Values.secretKeys.cacheUrl }}
- name: {{ $env }}
  valueFrom:
    secretKeyRef:
      name: {{ $secret }}
      key: {{ $key }}
{{- end }}
{{- with .Values.extraEnv }}
{{ toYaml . }}
{{- end }}
{{- end -}}

{{- define "aspm.serviceAccount" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "aspm.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{- define "aspm.oidc.env" -}}
{{- with .Values.oidc }}
{{- if .enabled }}
- {name: DD_ASPM_OIDC_ENABLED, value: "True"}
- name: DD_ASPM_OIDC_ISSUER
  value: {{ required "oidc.issuer is required" .issuer | quote }}
- name: DD_ASPM_OIDC_CALLBACK_URL
  value: {{ required "oidc.callbackUrl is required" .callbackUrl | quote }}
- name: DD_ASPM_OIDC_CLIENT_ID
  value: {{ required "oidc.clientId is required" .clientId | quote }}
- name: DD_ASPM_OIDC_CLIENT_SECRET
  valueFrom:
    secretKeyRef:
      name: {{ required "oidc.existingSecret is required" .existingSecret | quote }}
      key: {{ required "oidc.clientSecretKey is required" .clientSecretKey | quote }}
- {name: DD_ASPM_OIDC_CLIENT_AUTH, value: {{ .clientAuth | quote }}}
- {name: DD_ASPM_OIDC_SCOPES, value: {{ .scopes | quote }}}
- {name: DD_ASPM_OIDC_ROLE_CLAIM, value: {{ .roleClaim | quote }}}
- {name: DD_ASPM_OIDC_GROUP_CLAIM, value: {{ .groupClaim | quote }}}
- {name: DD_ASPM_OIDC_SECOPS_ROLE, value: {{ .secopsRole | quote }}}
- {name: DD_ASPM_OIDC_EXPERT_ROLE, value: {{ .expertRole | quote }}}
- {name: DD_ASPM_OIDC_USER_ROLE, value: {{ .userRole | quote }}}
- {name: DD_ASPM_OIDC_SESSION_AGE, value: {{ .sessionAge | quote }}}
- {name: DD_ASPM_OIDC_GROUP_TTL, value: {{ .groupTtl | quote }}}
- {name: DD_ASPM_OIDC_PROVIDER_LOGOUT, value: {{ .providerLogout | quote }}}
{{- if .existingCaSecret }}
- {name: DD_ASPM_OIDC_CA_BUNDLE, value: "/app/idp-tls/ca.crt"}
{{- end }}
{{- end }}
{{- end }}
{{- end -}}

{{- define "aspm.monitoring.relabel" -}}
- targetLabel: application
  replacement: aspm
- targetLabel: release
  replacement: {{ .Release.Name | quote }}
- targetLabel: namespace
  replacement: {{ .Release.Namespace | quote }}
- sourceLabels: [__meta_kubernetes_pod_name]
  targetLabel: pod
- sourceLabels: [__meta_kubernetes_pod_label_app_kubernetes_io_component]
  targetLabel: component
{{- range $key, $value := .Values.monitoring.dedicated.externalLabels }}
- targetLabel: {{ $key }}
  replacement: {{ $value | quote }}
{{- end }}
{{- with .Values.monitoring.relabelings }}
{{ toYaml . }}
{{- end }}
{{- end -}}

{{- define "aspm.monitoring.endpoint" -}}
port: aspm-metrics
path: {{ .Values.monitoring.path | quote }}
interval: {{ .Values.monitoring.interval | quote }}
scrapeTimeout: {{ .Values.monitoring.timeout | quote }}
{{- with .Values.monitoring }}
{{- if .scrapeAuthSecret }}
authorization:
  credentials: {name: {{ .scrapeAuthSecret | quote }}, key: token}
{{- end }}
{{- if .scrapeTLSSecret }}
scheme: https
tlsConfig:
  ca:
    secret: {name: {{ required "monitoring.scrapeCASecret is required for TLS" .scrapeCASecret | quote }}, key: ca.crt}
  {{- if .scrapeServerName }}
  serverName: {{ .scrapeServerName | quote }}
  {{- end }}
{{- end }}
{{- end }}
relabelings: {{ include "aspm.monitoring.relabel" . | nindent 2 }}
{{- end -}}

{{- define "aspm.monitoring.allowlist" -}}
(up|scrape_(duration_seconds|samples_scraped|samples_post_metric_relabeling|series_added)|aspm:(http|scan|report|webhook|pvc|postgres|celery|delivery)_[a-z0-9_:]+|aspm_{{ if not .Values.monitoring.remoteWrite.securityPosture }}(http|ingestion|scan|artifact|report|storage|outbox|webhook|identity|celery|durable|dependency|broker|evidence|postgres)_[a-z0-9_]+{{ else }}[a-z0-9_]+{{ end }}|pg_[a-z0-9_]+|redis_(up|connected_clients|memory_used_bytes|memory_max_bytes|rejected_connections_total|evicted_keys_total|commands_processed_total)|kube_(deployment|pod|node|horizontalpodautoscaler|poddisruptionbudget|job)_[a-z0-9_]+|kubelet_volume_stats_[a-z0-9_]+|container_(cpu|memory|network)_[a-z0-9_]+|node_(cpu_seconds_total|memory_MemAvailable_bytes|memory_MemTotal_bytes|disk_io_time_seconds_total)|traefik_(service|entrypoint)_[a-z0-9_]+|prometheus_(remote_storage|tsdb)_[a-z0-9_]+|process_(cpu_seconds_total|resident_memory_bytes)|ALERTS)
{{- end -}}
