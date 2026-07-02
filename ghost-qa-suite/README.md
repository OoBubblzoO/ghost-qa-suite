# Ghost CMS — Automated Test Suite

Automated API and E2E test suite for [Ghost](https://ghost.org), the open-source publishing platform, built with **pytest**, **httpx**, and **Playwright**, running in **GitHub Actions** against a Dockerized Ghost instance.

**Author:** Pedro — QA/Quality Engineering (former Apple Home QE intern)

---

## Why this project exists

This repo demonstrates how I approach testing a real production application: risk-based test selection, a maintainable automation architecture, and clear documentation of *what* is tested, *what isn't*, and *why*. It's the same process I'd apply to a client's application.

## Test strategy

### What I test, and why

| Layer | Tooling | Scope | Rationale |
|---|---|---|---|
| **Content API** (public, read-only) | pytest + httpx | Smoke + contract tests on posts, tags, pages | Highest-traffic surface; cheap, fast, stable tests |
| **Admin API** (authenticated) | pytest + httpx | Auth (JWT), CRUD on posts, validation & negative tests | Where the business logic and permission rules live — highest risk of regression |
| **UI critical paths** | Playwright | Login → create post → publish → verify public render | The one journey that, if broken, means the product is broken |

### What I deliberately don't test here

- **Exhaustive UI coverage.** UI tests are slow and brittle relative to API tests. I automate only critical user journeys and push everything else down to the API layer, where the same logic can be verified faster and more reliably.
- **Ghost's internal units.** That's the responsibility of Ghost's own unit suite. My suite treats Ghost as a black box, the way a client's QA vendor would.
- **Performance/load.** Out of scope for a functional regression suite; noted as a natural extension.

### Risk-based prioritization

Tests are tagged by priority:
- `@pytest.mark.smoke` — must pass on every commit; fast, no auth, read-only
- `@pytest.mark.critical` — auth + core CRUD; the "is the product usable" set
- `@pytest.mark.regression` — negative tests, validation, edge cases

CI runs smoke first and fails fast before spending time on the full suite.

## Architecture decisions

- **Auth handled once, in a fixture.** Ghost's Admin API uses short-lived JWTs signed with an API key. Token generation lives in `utils/ghost_auth.py`, exposed via a session-scoped fixture — no test ever handles credentials directly.
- **A thin API client, not raw requests in tests.** `utils/api_client.py` wraps httpx with base URLs, headers, and JSON handling so tests read as intent ("create a post") rather than plumbing.
- **Test data is created and destroyed by the tests that use it.** Factory fixtures create uniquely-named resources and clean up in teardown, so the suite is safe to run repeatedly and in parallel.
- **Config via environment variables** (`.env.example` provided) so the same suite runs locally and in CI without changes.

## Running it yourself

```bash
# 1. Start Ghost locally
docker compose up -d

# 2. Complete the one-time Ghost setup at http://localhost:2368/ghost
#    then create an Admin API integration (Settings → Integrations → Add custom integration)
#    and copy the keys into .env  (see .env.example)

# 3. Install and run
pip install -r requirements.txt
playwright install chromium
pytest -m smoke          # fast smoke set
pytest                   # full suite
pytest -m e2e            # Playwright UI tests only
```

## CI

GitHub Actions (`.github/workflows/ci.yml`) spins up Ghost in Docker, provisions an API key, runs smoke → full API suite → E2E, and publishes a JUnit test report on every push and PR.

## Findings

Real issues and quirks discovered while building this suite are documented as professional bug reports in [`docs/bug-reports/`](docs/bug-reports/), with reproduction steps, expected vs. actual behavior, and severity assessments.

## Extending this suite

Natural next steps for a production engagement: webhooks testing, member/subscription flows, email delivery verification, schema/contract testing against Ghost's OpenAPI spec, and visual regression on themes.
