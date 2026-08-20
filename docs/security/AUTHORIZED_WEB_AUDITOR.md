# Authorized Web Security Auditor

The platform now includes a voice-addressable, non-destructive web security auditor for owner-approved assessments.

## Voice flow

A command such as `website security audit karo` is parsed as `security_audit`. Voice parsing does not perform a scan. The authenticated operator must then supply the target URL and the explicit authorization phrase required by the API.

## Scan API

`POST /api/security-audit/scan`

Required payload:

- `target`: absolute HTTP(S) URL
- `authorization`: `i-authorize-this-security-test`

The scanner checks security headers, cookie flags, permissive credentialed CORS, version disclosure, security.txt availability, redirect behavior, and similar non-destructive signals.

## Responsible disclosure

`POST /api/security-audit/disclose` sends a report only when the operator explicitly supplies a recipient and the authorization phrase `i-authorize-this-disclosure`.

SMTP configuration uses `SECURITY_SMTP_*` environment variables. The application never guesses a company address and never sends a disclosure automatically from a scan.

## Safety boundaries

- Authentication bypass, exploitation, persistence, credential theft, data extraction, and destructive testing are not implemented.
- Private, loopback, link-local, multicast, reserved, and unspecified target IPs are blocked.
- Redirects are not followed automatically.
- The auditor is not a proof of exploitability; application-specific authorization, business-logic, and authenticated testing require a separately authorized test plan.
