# Security policy

Version 0.1.x is the current preview series. The audit reads a bounded checksum-declared local CSV, runs no remote queries and invokes no Power BI service. The optional extractor is read-only but still parses a complex binary format: use it only on reviewed trusted files. The notebook runner executes this repository's ordinary Python cells; it is not a sandbox for arbitrary notebooks.

For a credential, private record or exploitable parser/path issue, contact Prajwal Pratap Yadav privately at prajwalpratapyadav5@gmail.com or use GitHub private vulnerability reporting if enabled. Include affected version, safe reproduction and expected impact. Do not publish a real secret or sensitive data in an issue. No guaranteed response time is claimed.

CI scans full Git history with checksum-verified gitleaks and checks pinned dependency advisories. Staged hooks scan changes. These text scans do not inspect compressed PBIX internals; the original archive/model/import query/cached table were separately reviewed. The preserved original binary contains its owner's historical local source path, while the published metadata redacts it. Dataset rows are agricultural aggregates, not person-level records. These are scoped controls, not a security certification.
