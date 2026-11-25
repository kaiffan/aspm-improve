# ASPM qualification helpers

These helpers never push images, promote releases, delete snapshots or disable disk guards.

- validate-chart.sh: schemas, real Helm behavioral tests, templates, kubeconform and chart package.
- kubernetes-smoke.sh: explicit owned lab context/namespace install, upgrade and replacement smoke.
- capacity.py: read-only disk budget (51 GiB including reserve) and native-host detection.
- native.py: exact A=25da29aa and explicit immutable B, frozen Core9/Acceptance inputs and guarded Linux AMD64 build/campaign.

Use Python without -O. The native wrapper reuses the existing immutable kit; include integration-report/zero-finalize-final-qualification/native when moving it. See enterprise-report/aspm-hardening/REPRODUCE.md for invocation and untested gates.
