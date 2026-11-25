# Core9 A/B

Full 1M Core9 A/B is NOT TESTED for this candidate. Do not reuse the old 19cd7b→25da29aa comparison as enterprise candidate evidence. Required A is exactly 25da29aaff229d3a815e223d8af8bdc4ecca7c5e; B is the final immutable application commit recorded in provenance.json.

The native wrapper deploy/scripts/native.py overrides A/B explicitly while reusing the checksum-locked nine routes/weights and cohorts in integration-report/zero-finalize-final-qualification/native. It keeps c1/c5/c10/c15/c25 and three repeats at important high-concurrency points, restoration/fingerprint guards and captured SQL/CPU/WAL/I/O evidence. The original frozen workload inputs remain unchanged. Native build/campaign reject unsupported architectures and insufficient disk. See raw/capacity.json and REPRODUCE.md. Any small synthetic overview timings are diagnostics, not 1M capacity or strict hardware-comparable A/B.
