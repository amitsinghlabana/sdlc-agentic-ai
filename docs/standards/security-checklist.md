# Security Checklist

Mandatory security standards every feature must satisfy. Agents must cite the
relevant section when a requirement or design decision is driven by it.

## S-1 Password storage
Passwords must NEVER be stored or compared in plaintext. Hash with a slow,
salted algorithm (bcrypt, scrypt, or Argon2id). Never log raw credentials.

## S-2 Authentication errors
Failed logins must return a generic `401` ("invalid email or password") that
does not reveal whether the email exists. Avoid user-enumeration leaks.

## S-3 Input validation
Validate and sanitize all input server-side. Reject malformed payloads with
`400`. Treat client-side validation as UX only, never a security control.

## S-4 Secrets handling
Secrets (API keys, tokens) come from environment variables or a secret store —
never hardcoded, committed, or returned to the browser.

## S-5 Transport security
All traffic is HTTPS/TLS. Reject mixed content. Set secure, HttpOnly cookies
for any session identifiers.

