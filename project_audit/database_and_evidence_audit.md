# Database and evidence audit

13 November 2026. Read-only transaction through the configured runtime role. Snapshot counts: 303 documents, 305 analysis versions, 12 cases, 952 custody entries, 446 security entries. Concurrent usage may change counts; these are not hardcoded product metrics.

Catalog: users, refresh_tokens, cases, documents, document_pages, analyses, evidence_records, detected_regions, document_comparisons, forensic_reports, exhibit_custody_logs, security_audit_logs, alembic_version. Runtime role is visionforensics_app. SELECT on alembic_version was denied; effective migration revision is not asserted. Source migration chain has four revisions: 542c3ab525d8 -> 91b447dad22a -> 103f466da39f -> 146af5c0448f.

Verified ledger protections: runtime role grants SELECT/INSERT only on both ledgers; enabled BEFORE UPDATE and DELETE triggers prevent modification. No ledger mutation test was performed against live data.

Defects:

- Repository methods and AuditService commit independently; ingestion is not atomic. An exception after earlier commits leaves partial records. DocumentService swallows persistence exceptions and caches the result.
- Analysis schema omits per-page inference, full vector, actual metadata, quality metrics, compression/visual summaries and execution state. Restart reconstructs a smaller and misleading result, including substituting unified tier for raw ML tier.
- max(version)+1 can race; evidence/region IDs can collide across repeated analyses. Existing unique version constraint is helpful but not concurrency control.
- Missing original paths bypass checks in analysis/image retrieval. Derived artifact integrity is not independently anchored. Original download API absent.
- Paths depend on working directory/native vs Docker mounts. Missing historical files must be reported missing, not replaced by a generated graphic.
- Case model exists but UI details are never persisted. Uploader/case-lead/admin ownership exists; senior-investigator behavior differs from its docstring.
- Report context path uses wrong score key and version 1; fallback accesses nonexistent region fields.

Before any migration: pg_dump custom-format backup using configured administrative/migration credentials without printing them; verify archive listing/hash; preserve relevant files/source manifest; test migration on isolated copy. Add versioned snapshot nullable for legacy records. Do not fabricate missing historical values, overwrite prior analyses, delete evidence, alter custody/security records, or change frozen artifacts. Preserve orphaned files on persistence failure for recovery. Full restart equivalence/backup restore still unverified.
