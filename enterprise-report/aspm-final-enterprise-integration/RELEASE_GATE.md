# Release gates

**Decision HOLD.** Use the integrated code in the isolated qualification environment. Production promotion and Stable publication remain gated.

| Gate | Outcome |
| --- | --- |
| Engagement assignment and local cross-Product guards | PASS locally |
| Scanner compatibility | PASS for the six verified fixtures. Corporate FF selection is open. |
| Real Keycloak protocol and local role isolation | PASS for the synthetic realm and tested routes |
| Corporate Keycloak/AD and enterprise networking | NOT TESTED |
| Corporate UI | Responsive Chromium smoke. Formal WCAG 2.2 AA audit remains open. |
| Full Django, JS and schema regression | PASS on the candidate. 8,350 Django passed, 553 inherited skips. 17 JavaScript passed. |
| Helm schema, rendering and Kubernetes API dry run | PASS locally |
| Kubernetes staging install, upgrade and rollback | NOT TESTED |
| Core9 and Acceptance A/B | NOT TESTED |
| Native Linux/AMD64 and Ryzen VM | NOT TESTED |
| Backup and restore | PASS locally. Target storage restore remains open. |
| Enterprise scanner format variants and warning handling | See compatibility gaps and limits. |

The reported local result includes inspected browser assets and backend access checks. It does not stand in for the deployment, corporate security or strict A/B gates. [Test results](E2E_TEST_RESULTS.md) · [Performance](PERFORMANCE_AB.md) · [Known limitations](KNOWN_LIMITATIONS.md)
