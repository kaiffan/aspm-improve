# Outbound events

The existing transactional webhook module captures scan.completed, scan.failed, report.generated, finding.updated and finding.false_positive_changed. These events use the original durable delivery tables and shared periodic dispatcher. Each subscription is Product-scoped. SecOps permission gates configuration and delivery history.

Existing HMAC and HTTPS validation, retry, leases, delivery history and secret rotation continue to apply. The targeted regression covers signed payload verification, transactional events, and concurrent independent Finding changes. Production endpoint connectivity and staging secret rotation still require target evidence.
