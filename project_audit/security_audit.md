# Security audit

13 November 2026. Source and read-only catalogs, not complete security certification. No credentials, tokens or connection secrets are reproduced here.

Strengths: Argon2id; JWT allowlisted algorithm and required claims/access type; active account, role and object ownership checks; dual-parent comparison authorization; refresh rotation/grace-window design; per-IP/account limits; SHA-256 primitives; magic-byte/Pillow/PDF validation; dimension/page ceilings; append-only ledger grants/triggers.

| Severity | Weakness | Evidence / repair direction |
|---|---|---|
| P0 | Anonymous development analyst fallback writes/uses account | core/auth.py; require auth consistently, isolate tests with explicit authenticated fixtures |
| P0 | Access tokens in asset URLs; access cookie not HttpOnly | frontend/services/api.ts and api/auth.py; authenticated cookies or blobs without query credentials |
| P0 | Missing original bypasses integrity; false VERIFIED custody | api/documents.py; fail closed, distinguish missing/unverifiable/tampered |
| P0 | Unverified executable model deserialization | inference_service.py; expected model/schema hashes before joblib |
| P1 | Memory/resource denial of service | Whole upload read before limit; giant PDF scaling bug; synchronous async-handler CPU work |
| P1 | Secrets can enter logs | Startup prints DB URL; SQLAlchemy echo logs parameters; shallow audit-detail redaction |
| P2 | Configuration/deployment ambiguity | cwd-dependent env-file precedence; preview not HTTPS pilot |
| P2 | Broad proxy trust defaults | Settings trust private CIDRs; pilot Uvicorn narrows forwarded-allow-ips; verify effective chain, never broaden to pass tests |
| P2 | Credentials/demo values in source/config | Do not expose or propagate; future rotation separately controlled, no credential reset during audit |
| P2 | CSP/header behavior | CSP blocks external Google fonts; add_header location inheritance requires deployed checks |

Default docker-compose.yml postgres port mapping lacks explicit 127.0.0.1 binding. Pilot compose correctly keeps backend/db internal and binds frontend 127.0.0.1 only. Do not weaken that isolation. Nginx TLS is configured, not runtime-verified in this phase.

Report download hash validation exists; report generation must also verify exhibit before compiling/versioning. Missing/changed originals, revoked sessions, inactive users, cross-user access, CSRF and trusted-proxy spoofing need negative tests on disposable records. Existing tamper/ledger tests must never run blindly against historical data. Remove secrets from operational logs without deleting historical security/custody records.
