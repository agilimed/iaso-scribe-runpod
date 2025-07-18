{{/*
Expand the name of the chart.
*/}}
{{- define "nexuscare-ai.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "nexuscare-ai.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "nexuscare-ai.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "nexuscare-ai.labels" -}}
helm.sh/chart: {{ include "nexuscare-ai.chart" . }}
{{ include "nexuscare-ai.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "nexuscare-ai.selectorLabels" -}}
app.kubernetes.io/name: {{ include "nexuscare-ai.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "nexuscare-ai.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "nexuscare-ai.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Get the image repository
*/}}
{{- define "nexuscare-ai.image" -}}
{{- $registry := .Values.image.registry | default "" -}}
{{- $repository := .repository | default "" -}}
{{- $tag := .tag | default .Values.image.tag | default .Chart.AppVersion -}}
{{- if $registry -}}
{{- printf "%s/%s:%s" $registry $repository $tag -}}
{{- else -}}
{{- printf "%s:%s" $repository $tag -}}
{{- end -}}
{{- end }}

{{/*
Get PostgreSQL connection details
*/}}
{{- define "nexuscare-ai.postgresql.host" -}}
{{- if .Values.postgresql.enabled -}}
{{- printf "%s-postgresql" (include "nexuscare-ai.fullname" .) -}}
{{- else if .Values.cloudSQL.enabled -}}
{{- printf "127.0.0.1" -}}
{{- else if .Values.rds.enabled -}}
{{- .Values.rds.endpoint -}}
{{- else if .Values.azurePostgres.enabled -}}
{{- printf "%s.postgres.database.azure.com" .Values.azurePostgres.serverName -}}
{{- else -}}
{{- .Values.externalDatabase.host -}}
{{- end -}}
{{- end }}

{{/*
Get Redis connection details
*/}}
{{- define "nexuscare-ai.redis.host" -}}
{{- if .Values.redis.enabled -}}
{{- printf "%s-redis-master" (include "nexuscare-ai.fullname" .) -}}
{{- else if .Values.elasticache.enabled -}}
{{- .Values.elasticache.endpoint -}}
{{- else if .Values.memorystore.enabled -}}
{{- .Values.memorystore.endpoint -}}
{{- else if .Values.azureRedis.enabled -}}
{{- .Values.azureRedis.endpoint -}}
{{- else -}}
{{- .Values.externalRedis.host -}}
{{- end -}}
{{- end }}

{{/*
Get storage class
*/}}
{{- define "nexuscare-ai.storageClass" -}}
{{- if .Values.global.storageClass -}}
{{- if (eq "-" .Values.global.storageClass) -}}
{{- printf "" -}}
{{- else -}}
{{- printf "storageClassName: %s" .Values.global.storageClass -}}
{{- end -}}
{{- else -}}
{{- if .Values.persistence.storageClass -}}
{{- printf "storageClassName: %s" .Values.persistence.storageClass -}}
{{- end -}}
{{- end -}}
{{- end }}

{{/*
Return the appropriate apiVersion for ingress
*/}}
{{- define "nexuscare-ai.ingress.apiVersion" -}}
{{- if semverCompare ">=1.19-0" .Capabilities.KubeVersion.GitVersion -}}
{{- print "networking.k8s.io/v1" -}}
{{- else -}}
{{- print "networking.k8s.io/v1beta1" -}}
{{- end -}}
{{- end }}

{{/*
Cloud-specific annotations
*/}}
{{- define "nexuscare-ai.cloudAnnotations" -}}
{{- if eq .Values.global.cloudProvider "aws" -}}
{{- if .Values.aws.eksServiceAccount.create -}}
eks.amazonaws.com/role-arn: {{ .Values.aws.eksServiceAccount.annotations.roleArn | quote }}
{{- end -}}
{{- else if eq .Values.global.cloudProvider "gke" -}}
{{- if .Values.gke.workloadIdentity.enabled -}}
iam.gke.io/gcp-service-account: {{ .Values.gke.workloadIdentity.serviceAccount | quote }}
{{- end -}}
{{- else if eq .Values.global.cloudProvider "azure" -}}
{{- if .Values.azure.managedIdentity.enabled -}}
azure.workload.identity/client-id: {{ .Values.azure.managedIdentity.clientId | quote }}
{{- end -}}
{{- end -}}
{{- end }}