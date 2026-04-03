# File Upload & Media Processing Security Audit

This subcommand replaces the old standalone `/upload-security` skill.

## Command

```bash
/bug-report upload-security [--focus validation|storage|processing|download|all]
```

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

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
