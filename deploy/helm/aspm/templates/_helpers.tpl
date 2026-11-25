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
