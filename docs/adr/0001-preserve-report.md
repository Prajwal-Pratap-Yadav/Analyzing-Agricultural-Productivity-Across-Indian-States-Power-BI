# ADR 0001: Preserve the original report and add a companion audit

Status: accepted, 2026-10-04.

The original PBIX is useful evidence but cannot be refreshed or rendered in this Linux environment. Repacking it without Desktop validation would not prove its behavior. Preserve its bytes and Git history, extract sanitized metadata read-only and implement a standalone CSV audit. Alternative: edit/rebuild the report in an unvalidated binary workflow. Trade-off: the existing visualizations retain their old source path and integer area issue until a separate working copy is manually reviewed.
