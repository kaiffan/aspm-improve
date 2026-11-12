# Diagnostic metadata correction

The first profile collector inferred Finding page ordering from the queryset rebuilt by `prefetch_for_findings`. That queryset holds an evaluated page cache and its model Meta.ordering no longer describes the actual page SELECT. The verification correctly refused to waive mismatched primary values.

The corrected collector uses the original `context["filtered"].qs` before pagination/prefetch. All104 diagnostic cases per build were recaptured on the same protected seed, with the worker stopped and the same credentials. These files preserve the first diagnostic attempt and its failed verification. No measured load observations, HTTP latency, SQL counts or actor schedule were edited. The105 load runs/17,100 measured requests are unchanged; final profiles/plans live two levels above this archive.

The subsequent checker also initially required HTTP200 for every profile. Restricted users correctly receive403 on the global users/notes endpoints in all three builds. The final checker explicitly requires these403 outcomes (and byte-equal denial payloads); every other profiled route must return200. The failed diagnostic check is retained in expected-denials-check.txt. No permissions, application code or response data were changed.
