# [FINDING-001] Ghost distinguishes malformed vs. Invalid credentials in admin API auth errors

**COMPONENT:** Admin API - Authentication
**SEVERITY:** N/A - not a defect (behavior finding)
**PRIORITY:** N/A
**ENVIRONMENT:** Ghost 5.x (Docker, `ghost:5-alpine`), local, SQLite
**Discovered by:** automated suite (`tests/api/admin/test_admin_auth.py::test_garbage_token_is_rejected`)
**DATE:** 07-02-26

## SUMMARY
The test suite initially assumed all failed aunthetication attempts return '401 unauthorized'.
Ghost returns '400 Bad Request' when the Authorization token cannot be parsed as a JWT at all, and reserves '401' for well formed tokens that fail validation. Investigation concludes this is a 
reasonable API design, not a defect. The test suite was updated to reflect the actual behavior

## STEPS TO REPRODUE
1) Start Ghost locally ('docker compose up -d')
2) Send 'GET /ghost/api/admin/posts/' with header 'Authorization: Ghost not.a.jwt'
3) Observe the response status code
4) Compare against the same request with a valid but expired JWT

# EXPECTED RESULT (initial assumption)
'401 Unauthorized' for any failed aunthentication, regardless of cause.

## ACTUAL RESULT
- Unparsable token ('not.a.jwt') -> **400 Bad Request**
- Expired token (valid JWT stucture) -> **401 Unauthorized**
- Token signed with wrong secret -> ** 401 Unauthorized**
- Token with wrong audience claim -> **401 Unauthorized**

## IMPACT ASSESSMENT

No user impact. Behavior is consistent and more correct than the test assumption: '400' signals
"request malformed, could not be interpreted as credentials," whlie '401' signals "credentials 
understood and rejected." API consumers building retry/error handling logic benefit from the distinction

Suite Impact: one assertion updated ('==401' -> '==400') with an explanatory comment. No product change
proposed.

## NOTES
Root cause analysis followed the standard question: is the defect in the product or test? Evidence 
from sibling tests showed Ghost applies a deliberate parse vs validate distinction, resolving
this as a test assumption error
