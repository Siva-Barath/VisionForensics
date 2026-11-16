# Final security report

13 November 2026. Controlled pilot review; not an independent penetration test or security certification.

| Area | Verified outcome |
|---|---|
| Authentication | Required in development and pilot; anonymous analyst fallback removed; active account and JWT checks retained |
| Asset access | No URL query tokens; authenticated HttpOnly access/refresh cookies support previews/downloads |
| Browser Origin / CSRF | Eleven canonical localhost checks: cookie refresh/logout succeed; untrusted-origin refresh/logout return 403; existing trust policy unchanged |
| HTTPS | Live requests verify hostname and the existing pilot CA; Secure + HttpOnly cookies verified over HTTPS |
| Authorization | Role, ownership, inactive-account and dual-document restrictions covered by isolated tests; document scope filtering before pagination |
| Original integrity | Original bytes checked against immutable ingestion digest; missing/unverifiable/tampered paths fail closed |
| Derived artifacts | Real ELA map hashes checked; altered or missing maps do not become synthetic success results |
| Persistence | Atomic ingestion commit; rollback/error on failed persistence, no false successful cache |
| Model supply chain | Pinned model/schema bytes verified before trusted deserialization |
| Logging | Startup DB URL and SQL echo removed; new verification scripts redact secrets and never print tokens |
| Upload limits | Bounded reads, content parsing, PDF/image dimensions/page limits and actual render failures |
| Custody/security ledgers | Runtime SELECT/INSERT-only grants and UPDATE/DELETE blocking triggers retained; negative tests run only against disposable data |
| Exposure | Existing pilot frontend binds only 127.0.0.1:8080/8443; backend/database stay internal |
| Response headers | HSTS, CSP, nosniff and frame policy verified on actual SPA routes, static assets and health API |

The Nginx security fix addresses a measured inheritance defect: adding Cache-Control within a location suppressed all server-level add_header directives. A common security-header include now applies at the server and both cache-setting locations. Remote Google Fonts links were removed so the interface works with the existing self-origin CSP and system font fallbacks.

Frontend package security updates preserve React 18 and the existing route model. Final npm audit reported zero known vulnerabilities at verification time. This is registry-advisory evidence, not proof that the entire application or container supply chain has no vulnerabilities. Backend/container dependency scanning and independent penetration testing were not completed.

Backups precede schema migration: native custom-format archive, verified isolated restoration, and pilot custom-format archive. The only schema addition is nullable `analyses.context_snapshot`; no historical backfill or record deletion was performed. The existing migrator lacks analyses ownership, so the existing database owner was used only for the migration process; runtime grants and ownership were not broadened. A temporary migration container used an automatically assigned network address because compose run inherited an occupied fixed backend IP.

Live validation used retained synthetic exhibits and a generated controlled analyst account. No existing account password was changed. Its random password was not retained or printed. A failed attempt using a previously documented native demo account did not authenticate to the separate pilot database; testing then used normal registration. Security/custody events from legitimate checks remain present.

Remaining security work: the browser bearer token is still held in localStorage by the existing authentication design; HttpOnly cookies protect asset authentication but do not remove this XSS exposure. CSP permits inline styles for the current React/SVG rendering. Rate limits and process cache are single-worker/local; distributed deployment needs a shared limiter and concurrency review. Existing secrets/certification authority private keys and demo credentials require operational governance and controlled rotation before wider deployment; none were exposed or reset here. The existing Docker frontend health probe skips certificate validation; the actual external verification used the trusted CA without bypass. No external/public hosting was enabled.

See [known limitations](known_limitations.md) and [deployment guide](deployment_and_demo_guide.md). Historical audit files document the original findings; this report records the final verified state.
