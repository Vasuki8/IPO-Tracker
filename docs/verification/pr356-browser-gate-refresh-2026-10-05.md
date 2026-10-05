# PR #356 refresh after browser-gate stabilization

Refresh basis: merged browser repair PR #357, main revision
`ea0301aa5f4a02c2f5beaa3fa846a21d92fe6e4c` (2026-10-05 UTC).
Original admission repair: `1a21c35d97456e02a2d2324b738016434cc7eedb`.

The seven admission production/test files and original two evidence/verification
files are reused without modification from the reviewed PR #356. The complete
latest main recovery, metadata, browser fixtures, focus repair, workflow and
operational state are retained. The publication builder must regenerate the public
projection from that current recovery, excluding only SMCG04's retained DEBT issue.
Every other public object, dataset metadata and all recovery files must remain
unchanged against this refresh basis. No source collector or historical import is run.

The isolated preparation validates these preservation conditions and runs every
non-browser test plus all four browser scripts three times. Its final snapshot
contains no temporary preparation workflow. The retained runner reports and final
PR #356 checks are the authority for pass/fail; this document does not predeclare
successful execution, merge, or deployment.

After updating PR #356, inspect its normal PR checks before merge, then verify the
actual served output. BUG-001/005 are the admission batch, BUG-014 and duplicate
route focus are the separate PR #357 batch. Other defects and SSEK #352 stay open.
