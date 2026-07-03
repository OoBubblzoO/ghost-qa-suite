# [FINDING-002] E2E login blocked: staff device verification requires email in a mail-less test environment

**Component:** Ghost Admin — Sign-in flow / test environment configuration
**Severity:** N/A — not a product defect (environment/configuration finding)
**Priority:** N/A
**Environment:** Ghost 5.x (Docker, `ghost:5-alpine`), local, SQLite, no mail transport configured
**Discovered by:** automated suite (`tests/e2e/test_publish_journey.py`), root-caused via headed-mode inspection (`pytest -m e2e --headed`)
**Date:** 2026-07-03

## Summary
Playwright E2E login tests failed with the page remaining on `/ghost/#/signin`
despite valid owner credentials. Headed-mode inspection revealed the banner
"Failed to send email. Please check your site configuration and try again."
Root cause: Ghost's staff device verification feature emails a verification
code on sign-in from an unrecognized browser. Playwright launches a fresh
browser profile every run (always an unrecognized device), and the test
container has no mail transport, so the verification email fails and login
cannot complete. API-based authentication was unaffected, which is why the
API suite passed while E2E failed.

## Steps to Reproduce
1. Start Ghost via `docker compose up -d` with no mail configuration
2. Run the Playwright login flow (fresh browser context) with valid owner credentials
3. Observe the sign-in page does not navigate away
4. Re-run with `--headed` and observe the "Failed to send email" error banner

## Expected Result (initial test assumption)
Valid credentials submitted through the sign-in form result in a successful
login and navigation away from `/signin`.

## Actual Result
Login halts with "Failed to send email. Please check your site configuration
and try again." — the device-verification email cannot be sent, so the
verification step can never be completed.

## Impact Assessment
No product defect: device verification behaved as designed, and the failure
mode (surfacing an email-send error) is arguably correct. Impact is limited
to automated testing in environments without mail transport — a common CI
configuration — where all browser-based login is blocked.

An initial hypothesis (brute-force lockout from a sibling negative login
test) was investigated and disproved by the headed-mode evidence; that test
was nonetheless hardened to use a nonexistent account, eliminating a real
test-pollution risk.

## Resolution
Disabled device verification for the disposable test target only, via
Docker environment config in `docker-compose.yml`:
`security__staffDeviceVerification: "false"`.
Explicitly documented as a test-environment setting that must not be applied
to production instances. Alternative for environments requiring the feature
enabled: run a local mail-capture service (e.g., Mailpit) and complete the
verification step programmatically.

## Notes
Diagnostic sequence: URL-based assertion failure → hypothesis (lockout) →
headed-mode inspection → contradicting evidence (email banner) → revised
root cause → targeted config fix. Ghost maps nested config keys to
environment variables using `__` separators.
