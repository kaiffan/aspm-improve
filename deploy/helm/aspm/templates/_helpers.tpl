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
{{- range $key, $value := .Values.config }}
- name: {{ $key }}
  value: {{ $value | quote }}
{{- end }}
- name: DD_ASPM_STORAGE_MIN_FREE_BYTES
  value: {{ .Values.storage.minimumFreeBytes | quote }}
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
