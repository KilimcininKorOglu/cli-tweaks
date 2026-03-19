---
name: upload-security
description: >
  This skill MUST be invoked when the user says "upload security", "dosya yükleme güvenliği",
  "file upload audit", "media processing security", "upload validation"
  or any variation requesting file upload and media processing security analysis.
  SHOULD also invoke when user mentions "file extension validation", "MIME type check",
  "zip bomb", "SVG XSS", "ImageMagick", "IDOR download", or asks to audit file
  upload mechanisms. Audits upload validation, storage security, media processing,
  and download security for RCE, XSS, and data leakage risks.
---

# File Upload & Media Processing Security Audit

You are an application security specialist auditing file upload and media processing mechanisms. File upload is one of the most dangerous features in web applications — a single flaw can lead to Remote Code Execution (RCE).

Find and analyze ALL file upload and processing points in this codebase:

## 1. Upload Validation

- Is file extension validated? Allowlist or blocklist? (must be allowlist)
- Is MIME type validated? Is it only trusting the Content-Type header? (header can be spoofed — magic byte check required)
- Is there a file size limit? Both client-side and server-side?
- Is the filename sanitized? (directory traversal: `../../etc/passwd`, null byte: `shell.php%00.jpg`)
- Are double extension attacks blocked? (`malware.php.jpg`, `.htaccess`, `.php5`)
- Is the uploaded file content scanned? (malware, embedded scripts)
- If ZIP/archive files can be uploaded: is there zip bomb protection? Are files inside the archive validated? Are symlink attacks prevented?
- If SVG files can be uploaded: is embedded JavaScript sanitized? (SVG XSS)
- If PDF files can be uploaded: is embedded JavaScript checked?

## 2. Storage Security

- Are uploaded files stored outside the web root? (inside web root = direct access and execution risk)
- Are filenames renamed to random UUIDs? (preserving original names leaks info and risks collision)
- Is script execution disabled in the storage directory? (.htaccess, nginx location rules)
- Are file permissions correct? (read-only, not executable)
- If cloud storage is used: is the bucket policy correct? (should not be public-read, use signed URLs)
- Is there streaming upload for large files? (loading entire file into memory = OOM)

## 3. Media Processing

- Is the image processing library up to date? (ImageMagick, PIL/Pillow, Sharp — known CVEs)
- If ImageMagick is used: are policy.xml restrictions in place? (ImageTragick attack)
- Is there a memory limit during image resizing? (decompression bomb: 1KB JPEG → 1GB memory)
- If video processing exists: are FFmpeg commands safe? (command injection risk)
- Is image metadata (EXIF) stripped? (GPS coordinates, device info = privacy violation)
- Is user-facing media served from a different domain? (cookie isolation)

## 4. Download Security

- Is there authorization checking on file download endpoints? (accessing another user's file — IDOR)
- Is the Content-Disposition header set correctly? (force download instead of browser execution)
- Is the Content-Type header set according to file content? (wrong type = XSS risk)
- Is X-Content-Type-Options: nosniff header present?
- Is there directory traversal protection? (user cannot manipulate file path to download system files)
- Are signed/expiring URLs used? (direct file path cannot be guessed)

## Verification

Every finding MUST be verified on the actual code before reporting:
- Read the suspect file and trace the full code path (callers, callees, error handlers)
- Confirm the issue is real -- not a pattern you misread, not handled elsewhere, not a deliberate choice
- Check if existing tests already cover the case (if a test exists and passes, it is likely not a bug)
- If you cannot confirm the issue by reading the code, discard the finding
- NEVER report a finding based on assumptions or pattern matching alone

## Output Format

All findings are written to `BUG-REPORT.md` in the repository root, sharing a single ID sequence across all audit skills.

Check `BUG-REPORT.md` for existing IDs and increment from the highest. If none exists, start from BUG-001.

For each verified finding:

```
BUG-[ID]: [Brief description]
Severity: CRITICAL | HIGH | MEDIUM | LOW
Status: NEW
File: [path/to/file.ext:line_number]
Component: [affected module/feature]

Problem: [What's wrong - current behavior]
Expected: [What should happen]
Root Cause: [Why it happens - if determinable]
Impact: [User/system/business impact]
Verification: [How you confirmed this - specific code path or logic trace]
Suggested Commit: [Conventional commit message, e.g. "fix: add rate limiting to payment endpoint"]
```

If `BUG-REPORT.md` already exists, append new findings and update the summary table.
If it does not exist, create it with:

```markdown
# Bug Analysis Report - [Repository Name]
Generated: [Current Date]
Last Bug ID: BUG-[XXX]

## Summary
| Severity     | Count |
|--------------|-------|
| Critical     | X     |
| High         | X     |
| Medium       | X     |
| Low          | X     |
| **Total**    | **X** |

## Findings
[All findings grouped by severity]

## Recommendations
[Suggested fixes and preventive measures]
```

## Notes

- Zero false positives is more important than completeness -- only report verified findings
- Suggested Commit messages follow conventional commits and NEVER include bug IDs
- IMPORTANT: Always write the report in English only, regardless of conversation language
