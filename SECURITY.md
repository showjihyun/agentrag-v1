# 🔐 Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

The Workflow Platform team and community take security bugs seriously. We appreciate your efforts to responsibly disclose your findings, and will make every effort to acknowledge your contributions.

### How to Report a Security Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@workflowplatform.dev** or **showjihyun@gmail.com**

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

### What to Include

Please include the following information in your report:

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

This information will help us triage your report more quickly.

### Preferred Languages

We prefer all communications to be in English or Korean.

## Security Measures

### Current Security Features

#### Authentication & Authorization
- **JWT-based Authentication**: Secure token-based authentication system
- **Role-Based Access Control (RBAC)**: Granular permission system
- **API Key Management**: Secure credential storage and management
- **Session Management**: Secure session handling with Redis

#### Input Validation & Sanitization
- **Pydantic Validation**: Comprehensive input validation on all API endpoints
- **SQL Injection Prevention**: Parameterized queries and ORM usage
- **XSS Protection**: Input sanitization and output encoding
- **CSRF Protection**: Cross-site request forgery prevention

#### Infrastructure Security
- **HTTPS Enforcement**: All communications encrypted in transit
- **Secure Headers**: HSTS, CSP, X-Frame-Options, etc.
- **Rate Limiting**: Prevent abuse and DoS attacks
- **CORS Configuration**: Proper cross-origin resource sharing setup

#### Data Protection
- **Encryption at Rest**: Sensitive data encrypted in database
- **Encryption in Transit**: TLS 1.3 for all communications
- **Secret Management**: Secure storage of API keys and credentials
- **Data Anonymization**: PII protection in logs and analytics

#### Container Security
- **Minimal Base Images**: Using Alpine Linux for reduced attack surface
- **Non-root Containers**: Containers run as non-privileged users
- **Security Scanning**: Regular vulnerability scans of container images
- **Resource Limits**: Proper resource constraints to prevent resource exhaustion

### Security Best Practices

#### For Users
- Use strong, unique passwords
- Enable two-factor authentication when available
- Regularly rotate API keys
- Monitor workflow execution logs for suspicious activity
- Keep your deployment updated with latest security patches

#### For Developers
- Follow secure coding practices
- Validate all inputs
- Use parameterized queries
- Implement proper error handling
- Regular security testing
- Keep dependencies updated

## Vulnerability Disclosure Process

1. **Report Received**: We acknowledge receipt of your vulnerability report within 48 hours
2. **Initial Assessment**: We perform an initial assessment within 5 business days
3. **Detailed Investigation**: We conduct a thorough investigation
4. **Fix Development**: We develop and test a fix
5. **Coordinated Disclosure**: We coordinate the disclosure timeline with you
6. **Public Disclosure**: We publicly disclose the vulnerability after the fix is released

### Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 5 business days
- **Fix Timeline**: Varies based on severity (Critical: 7 days, High: 14 days, Medium: 30 days, Low: 90 days)

## Security Updates

Security updates will be released as patch versions (e.g., 1.0.1, 1.0.2) and will be clearly marked in the changelog. We recommend all users update to the latest version as soon as possible.

### Notification Channels

- **GitHub Security Advisories**: https://github.com/showjihyun/agentrag-v1/security/advisories
- **Release Notes**: Included in all releases
- **Email Notifications**: For critical vulnerabilities (if you've subscribed)

## Security Hardening Guide

### Production Deployment

#### Environment Configuration
```bash
# Use strong secrets
JWT_SECRET_KEY=<strong-random-key>
DATABASE_PASSWORD=<strong-password>

# Enable security features
ENABLE_HTTPS=true
ENABLE_RATE_LIMITING=true
ENABLE_CORS_PROTECTION=true

# Disable debug mode
DEBUG=false
DEVELOPMENT_MODE=false
```

#### Docker Security
```yaml
# docker-compose.yml security settings
services:
  backend:
    security_opt:
      - no-new-privileges:true
    read_only: true
    user: "1000:1000"
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

#### Network Security
- Use reverse proxy (nginx) with proper SSL configuration
- Implement firewall rules to restrict access
- Use VPN for administrative access
- Regular security audits and penetration testing

#### Database Security
- Use strong passwords and rotate regularly
- Enable SSL/TLS for database connections
- Implement database-level access controls
- Regular database security updates

## Compliance

The Workflow Platform is designed to help organizations meet various compliance requirements:

- **GDPR**: Data protection and privacy controls
- **SOC 2**: Security, availability, and confidentiality controls
- **ISO 27001**: Information security management
- **HIPAA**: Healthcare data protection (with proper configuration)

## Security Contact

For security-related questions or concerns:

- **Email**: security@workflowplatform.dev or showjihyun@gmail.com
- **PGP Key**: Available upon request
- **Response Time**: Within 48 hours

## Bug Bounty Program

We are considering implementing a bug bounty program. Stay tuned for updates!

## Acknowledgments

We would like to thank the following security researchers and organizations for their contributions to the security of the Workflow Platform:

- [List will be updated as we receive security reports]

---

**Remember**: Security is a shared responsibility. While we work hard to secure the platform, users must also follow security best practices in their deployments and usage.