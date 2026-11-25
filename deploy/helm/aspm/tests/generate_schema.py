"""Generate the chart's strict, typed schema from its checked-in defaults."""
# ruff: noqa: INP001 -- standalone CLI helpers invoke installed git/helm tools
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
# Kubernetes API subobjects deliberately retain extensible maps.
EXTENSIBLE = {"resources", "nginxResources", "startupProbe", "readinessProbe", "livenessProbe", "securityContext", "podSecurityContext", "affinity", "nodeSelector", "podLabels", "podAnnotations", "annotations", "labels", "namespaceSelector", "podSelector"}


def schema(value, key=""):
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        result = {"type": "integer", "minimum": 0}
        if key in {"replicas", "concurrency", "processes", "threads", "minReplicas", "maxReplicas", "activeDeadlineSeconds"}:
            result["minimum"] = 1
        if key == "port":
            result.update(minimum=1, maximum=65535)
        return result
    if isinstance(value, str):
        result = {"type": "string"}
        if key in {"existingSecret", "existingClaim", "mediaExistingClaim", "repository", "tag", "host", "tlsSecretName"}:
            result["minLength"] = 1
        if key == "digest":
            result["pattern"] = "^$|^sha256:[a-f0-9]{64}$"
        if key == "pullPolicy":
            result["enum"] = ["Always", "IfNotPresent", "Never"]
        return result
    if isinstance(value, list):
        return {"type": "array", "items": {"type": "object"}}
    if key == "config":
        return {"type": "object", "additionalProperties": {"type": "string"}, "propertyNames": {"pattern": "^DD_[A-Z0-9_]+$"}}
    if key in EXTENSIBLE:
        return {"type": "object"}
    result = {"type": "object", "additionalProperties": False, "properties": {k: schema(v, k) for k, v in value.items()}, "required": list(value)}
    if key in {"databaseTLS", "oidc"}:
        result["properties"]["existingSecret"].pop("minLength", None)
    if key == "oidc":
        result["properties"]["clientAuth"]["enum"] = ["client_secret_basic", "client_secret_post"]
        result["properties"]["sessionAge"].update(minimum=30, maximum=43200)
        result["properties"]["groupTtl"].update(minimum=30, maximum=600)
    return result


if __name__ == "__main__":
    result = schema(yaml.safe_load((ROOT / "values.yaml").read_text()))
    result["properties"]["worker"]["properties"]["terminationGracePeriodSeconds"]["minimum"] = 901
    result["$schema"] = "http://json-schema.org/draft-07/schema#"
    (ROOT / "values.schema.json").write_text(json.dumps(result, indent=2) + "\n")
