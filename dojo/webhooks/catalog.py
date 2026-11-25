EVENT_VERSION = "1"
EVENT_TYPES = (
    "scan.accepted", "scan.processing", "scan.completed", "scan.failed",
    "report.generated", "report.failed", "finding.created", "finding.updated",
    "finding.severity_changed", "finding.status_changed", "finding.false_positive_changed",
    "repository.created", "commit.first_seen", "commit.scan_completed", "webhook.test",
)
FILTER_FIELDS = {"repository_id", "scanner", "severity", "finding_status", "source", "pipeline_id"}
