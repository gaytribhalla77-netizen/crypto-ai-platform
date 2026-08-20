from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass, asdict
from email.message import EmailMessage
from urllib.parse import urlparse
import os
import smtplib

import httpx


@dataclass(frozen=True)
class Finding:
    id: str
    severity: str
    title: str
    description: str
    evidence: str
    remediation: str


class AuthorizationError(ValueError):
    pass


class TargetSafetyError(ValueError):
    pass


def _validate_target(target: str) -> tuple[str, str]:
    parsed = urlparse(target.strip())
    if parsed.scheme not in {"https", "http"} or not parsed.hostname:
        raise TargetSafetyError("Target must be an absolute HTTP(S) URL.")
    if parsed.username or parsed.password:
        raise TargetSafetyError("Credential-bearing URLs are not accepted.")
    host = parsed.hostname
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except OSError as exc:
        raise TargetSafetyError("Target hostname could not be resolved.") from exc
    addresses = {item[4][0] for item in infos}
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            raise TargetSafetyError("Private, local, reserved, or otherwise non-public targets are blocked.")
    normalized = parsed._replace(fragment="").geturl()
    return normalized, host


def _severity_rank(value: str) -> int:
    return {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}[value]


class AuthorizedWebAuditor:
    """Non-destructive web security checks for explicitly authorized targets.

    This auditor never attempts authentication bypass, exploitation, credential
    theft, persistence, data extraction, or destructive actions. It is designed
    for owner-approved assessments and responsible disclosure.
    """

    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout_seconds = timeout_seconds

    async def scan(self, target: str, authorization: str) -> dict:
        if authorization.strip().lower() != "i-authorize-this-security-test":
            raise AuthorizationError("Explicit target authorization is required.")
        target, host = _validate_target(target)
        findings: list[Finding] = []

        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=self.timeout_seconds,
            headers={"User-Agent": "AI-Trading-Platform-Authorized-Security-Auditor/1.0"},
        ) as client:
            response = await client.get(target)
            headers = {k.lower(): v for k, v in response.headers.items()}

            if "strict-transport-security" not in headers and target.startswith("https://"):
                findings.append(Finding("WEB-001", "medium", "HSTS is missing", "HTTPS is used but Strict-Transport-Security was not returned.", "Missing: Strict-Transport-Security", "Enable HSTS with an appropriate max-age after confirming all relevant subdomains support HTTPS."))
            if "content-security-policy" not in headers:
                findings.append(Finding("WEB-002", "medium", "Content Security Policy is missing", "No Content-Security-Policy response header was observed.", "Missing: Content-Security-Policy", "Deploy a restrictive CSP appropriate to the application and gradually tighten it using report-only mode first."))
            if headers.get("x-content-type-options", "").lower() != "nosniff":
                findings.append(Finding("WEB-003", "low", "MIME sniffing protection is missing", "X-Content-Type-Options is absent or not set to nosniff.", f"Observed: {headers.get('x-content-type-options', '<missing>')}", "Set X-Content-Type-Options: nosniff."))
            if "x-frame-options" not in headers and "frame-ancestors" not in headers.get("content-security-policy", ""):
                findings.append(Finding("WEB-004", "medium", "Clickjacking protection is missing", "Neither X-Frame-Options nor a CSP frame-ancestors directive was observed.", "Missing frame protection", "Set an appropriate frame-ancestors CSP directive or X-Frame-Options where compatible."))
            if "referrer-policy" not in headers:
                findings.append(Finding("WEB-005", "low", "Referrer-Policy is missing", "No Referrer-Policy response header was observed.", "Missing: Referrer-Policy", "Set a deliberate policy such as strict-origin-when-cross-origin."))
            if "permissions-policy" not in headers:
                findings.append(Finding("WEB-006", "info", "Permissions-Policy is missing", "No Permissions-Policy response header was observed.", "Missing: Permissions-Policy", "Consider disabling browser capabilities that the application does not need."))

            server = headers.get("server", "")
            if server and any(ch.isdigit() for ch in server):
                findings.append(Finding("WEB-007", "low", "Server version disclosure", "The Server header appears to expose a version number.", f"Observed: {server[:120]}", "Remove unnecessary product/version details from response headers."))

            set_cookie = response.headers.get_list("set-cookie")
            for cookie in set_cookie:
                low = cookie.lower()
                if "secure" not in low and target.startswith("https://"):
                    findings.append(Finding("WEB-008", "medium", "Cookie without Secure attribute", "A cookie was set over an HTTPS target without the Secure attribute.", cookie.split(";", 1)[0][:160], "Mark sensitive cookies Secure."))
                if "httponly" not in low:
                    findings.append(Finding("WEB-009", "low", "Cookie without HttpOnly attribute", "A cookie was set without HttpOnly.", cookie.split(";", 1)[0][:160], "Use HttpOnly for cookies that do not need JavaScript access."))
                if "samesite" not in low:
                    findings.append(Finding("WEB-010", "low", "Cookie without SameSite attribute", "A cookie was set without SameSite.", cookie.split(";", 1)[0][:160], "Set an appropriate SameSite value for session and security-sensitive cookies."))

            if headers.get("access-control-allow-origin", "").strip() == "*" and "access-control-allow-credentials" in headers:
                findings.append(Finding("WEB-011", "medium", "Permissive CORS with credentials", "The response combines wildcard CORS origin with credential support.", "Access-Control-Allow-Origin: * plus Access-Control-Allow-Credentials", "Restrict allowed origins and avoid wildcard origins for credentialed requests."))

            sec_txt = await client.get(f"{parsed_origin(target)}/.well-known/security.txt")
            if sec_txt.status_code >= 400:
                findings.append(Finding("WEB-012", "info", "security.txt is not published", "A standard security contact file was not available at /.well-known/security.txt.", f"HTTP {sec_txt.status_code}", "Publish a security.txt file with a monitored vulnerability disclosure contact."))

            robots = await client.get(f"{parsed_origin(target)}/robots.txt")
            if robots.status_code < 400 and len(robots.content) > 1_000_000:
                findings.append(Finding("WEB-013", "low", "Oversized robots.txt response", "robots.txt returned an unexpectedly large response.", f"{len(robots.content)} bytes", "Keep discovery metadata concise and review unusual generated content."))

            if 300 <= response.status_code < 400:
                findings.append(Finding("WEB-014", "info", "Redirect observed", "The target returned a redirect; the auditor intentionally does not follow it automatically.", f"HTTP {response.status_code}", "Review the redirect destination and enforce the intended canonical HTTPS host."))

        findings.sort(key=lambda item: (-_severity_rank(item.severity), item.id))
        return {
            "target": target,
            "host": host,
            "status_code": response.status_code,
            "findings": [asdict(item) for item in findings],
            "summary": {
                "critical": sum(x.severity == "critical" for x in findings),
                "high": sum(x.severity == "high" for x in findings),
                "medium": sum(x.severity == "medium" for x in findings),
                "low": sum(x.severity == "low" for x in findings),
                "info": sum(x.severity == "info" for x in findings),
            },
            "limitations": [
                "This is a non-destructive surface audit, not a proof of exploitability.",
                "Authentication, authorization/IDOR, business-logic, and application-specific vulnerabilities require an authorized test plan and suitable test accounts.",
                "The scanner blocks private/local targets and does not follow redirects automatically.",
            ],
        }


def parsed_origin(target: str) -> str:
    p = urlparse(target)
    return f"{p.scheme}://{p.netloc}"


def send_disclosure_email(report: dict, recipient: str) -> None:
    host = os.getenv("SECURITY_SMTP_HOST")
    port = int(os.getenv("SECURITY_SMTP_PORT", "587"))
    username = os.getenv("SECURITY_SMTP_USERNAME")
    password = os.getenv("SECURITY_SMTP_PASSWORD")
    sender = os.getenv("SECURITY_DISCLOSURE_FROM")
    if not all([host, username, password, sender]):
        raise RuntimeError("Security disclosure SMTP is not configured.")
    msg = EmailMessage()
    msg["Subject"] = f"Responsible security disclosure — {report['host']}"
    msg["From"] = sender
    msg["To"] = recipient
    lines = [f"Authorized security assessment for {report['target']}", "", "Findings:"]
    for finding in report["findings"]:
        lines.extend([f"- [{finding['severity'].upper()}] {finding['title']} ({finding['id']})", f"  Evidence: {finding['evidence']}", f"  Remediation: {finding['remediation']}"])
    lines.extend(["", "This disclosure contains non-destructive observations only."])
    msg.set_content("\n".join(lines))
    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(msg)
