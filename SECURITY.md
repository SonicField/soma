# Security Policy

## Scope

SOMA is a research programming language interpreter. It is not intended for production use in security-critical environments.

## Supported Versions

Only the latest version on the `main` branch is actively maintained.

## Reporting a Vulnerability

If you discover a security vulnerability in SOMA, please report it by:

1. **Opening a GitHub issue** if the vulnerability is not sensitive
2. **Emailing the maintainer directly** for sensitive security issues (see GitHub profile for contact)

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Response Timeline

As this is a research project maintained by one person:
- Acknowledgment: Within 1 week
- Initial assessment: Within 2 weeks
- Fix timeline: Depends on severity and complexity

## Security Considerations

When using SOMA, be aware:
- **No sandboxing**: SOMA code has access to the host system via FFI
- **File I/O**: Programs can read/write files with user permissions
- **Code execution**: SOMA can execute arbitrary Python via FFI extensions
- **Input validation**: Minimal input sanitization is performed

SOMA is designed for educational and research purposes, not for running untrusted code.
