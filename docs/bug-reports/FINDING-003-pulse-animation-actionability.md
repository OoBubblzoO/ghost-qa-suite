# [FINDING-003] Perpetual CSS animation on publish-confirm button defeats Playwright actionability checks

**Component:** Ghost Admin — Publish flow UI (testability)
**Severity:** Low — no end-user impact; automation-only friction on a critical-path control
**Priority:** P3
**Environment:** Ghost 5.x (Docker, `ghost:5-alpine`), Playwright 1.49 (Chromium)
**Discovered by:** automated suite (`tests/e2e/test_publish_journey.py::test_login_create_publish_and_verify_public_render`)
**Date:** 2026-07-03

## Summary
The final "Publish post, right now" click timed out after 30 seconds. The
Playwright call log showed the locator resolving correctly to the button
(`data-test-button="confirm-publish"`) followed by 53 retries of
"waiting for element to be visible, enabled and stable — element is not
stable." The button's class list includes `gh-btn-pulse`, a perpetual CSS
pulse animation. Playwright's actionability model requires an element's
bounding box to be stable across animation frames before clicking; an
infinite animation means that condition can never be satisfied, so the
click never fires.

## Steps to Reproduce
1. Drive Ghost admin with Playwright: create a post, click Publish, then "Continue, final review"
2. Attempt a standard `.click()` on the confirm button ("Publish post, right now")
3. Observe `TimeoutError: Locator.click: Timeout 30000ms exceeded` with repeated "element is not stable" entries in the call log

## Expected Result
A visible, enabled, stationary button is clickable by automation using
default actionability checks.

## Actual Result
The stability check never passes due to the element's infinite
`gh-btn-pulse` animation; the click times out despite the button being
functionally clickable (position is constant; the animation affects
scale/appearance only).

## Impact Assessment
End users: none — the button works normally for humans.
Automation: any tool with actionability/stability gating will fail on this
control by default, on the most critical step of the publishing journey.
Noted as a minor product testability concern rather than a functional
defect; Ghost does ship `data-test-button` hooks, indicating automation is
a supported concern.

## Resolution
Documented force-click in the test (`confirm.click(force=True)`) with an
inline comment recording the root cause — safe here because the animation
does not move the element's position. Locator retained/upgraded to the
product's own test hook (`[data-test-button="confirm-publish"]`).
Scaling alternative for larger suites: inject a global
animation/transition-disabling stylesheet at context setup, which also
stabilizes visual comparisons.

## Notes
`force=True` bypasses actionability checks and can mask real defects
(e.g., overlapped or obscured elements); it is used here only with a
verified root cause, which is the criterion for acceptable use. The
53-retry call log is preserved in the test run history as evidence.
