---
name: http-cache
description: >
  This skill MUST be invoked when the user says "http cache", "cache ekle",
  "add caching", "ETag ekle", "cache headers", "304 not modified",
  "static file caching", "browser cache", "tarayıcı cache",
  "cache-control ekle", "conditional requests" or any variation requesting
  HTTP caching with ETag and Cache-Control headers for static/embedded files.
  Scans the project, detects the framework, and implements content-hash-based
  ETag caching with 304 Not Modified support.
argument-hint: "[scan | apply]"
---

# HTTP Cache — ETag + Cache-Control

Scan the project's HTTP layer, identify static and dynamic endpoints, and implement content-hash-based ETag caching with Cache-Control headers and 304 Not Modified support.

**Default behavior is `scan` (dry-run).** Cache bugs are notoriously sinister — users see stale JS, admins see stale HTML, API responses get cached unexpectedly, and detection often takes days. Apply changes only after reviewing the scan output.

## Usage

```
/http-cache          # Scan only — show what would change, don't modify (DEFAULT)
/http-cache scan     # Same as default
/http-cache apply    # Apply the changes from the scan
```

## How It Works

### Phase 1: Project Scan

Detect the project's language and HTTP framework:

| Language   | Frameworks to detect                                          |
|------------|---------------------------------------------------------------|
| Go         | net/http, chi, gin, echo, fiber, gorilla/mux                  |
| Node.js    | express, fastify, koa, hapi, next.js, nuxt                    |
| Python     | flask, django, fastapi, starlette                             |
| Rust       | actix-web, axum, warp, rocket                                 |
| PHP        | laravel, symfony, plain (no framework)                        |

Identify:
1. **Static endpoints** — serve files from disk, embed, or public directory (HTML, CSS, JS, JSON, XML, TXT, images, fonts)
2. **Dynamic endpoints** — API routes returning computed data (JSON APIs, SSE, WebSocket)
3. **Template-rendered pages** — HTML generated from templates with dynamic data
4. **Sensitive endpoints** — auth, admin panels, payment, banking, user PII, internal dashboards

### Phase 2: Classify Endpoints

Assign each endpoint a caching strategy:

| Type                                            | Cache-Control                          | ETag   | 304 Support |
|-------------------------------------------------|----------------------------------------|--------|-------------|
| Immutable assets (JS/CSS with hash in filename) | `public, max-age=31536000, immutable`  | no     | no          |
| Static files (HTML, robots.txt, sitemap, etc.)  | `public, max-age=3600`                 | yes    | yes         |
| Landing page / index HTML                       | `public, max-age=300`                  | yes    | yes         |
| Public API responses (non-sensitive, cacheable) | `public, max-age=60` (or as suitable)  | yes    | yes         |
| Real-time API responses (live data)             | `no-store`                             | no     | no          |
| Template-rendered pages with non-sensitive user data | `private, no-cache`               | yes    | yes         |
| Sensitive pages (auth, admin, payment, banking) | `no-store`                             | no     | no          |
| SSE / WebSocket streams                         | `no-store`                             | no     | no          |

**Important distinctions:**
- `no-cache` ≠ "don't cache" — it means "cache but revalidate every use." For truly sensitive data use `no-store`.
- `private` allows browser to cache but blocks shared caches (CDN, proxy). On shared devices this is still risky for sensitive content — prefer `no-store`.
- For `immutable` assets, ETag is unnecessary and counterproductive; some browsers will still send conditional requests, wasting round-trips.

### Phase 3: Implementation

#### ETag Generation

Compute a content hash at **startup time** (not per-request) for embedded/static files. Use the fastest available hash:

| Language | Hash function                 | Format                              |
|----------|-------------------------------|-------------------------------------|
| Go       | `crypto/sha256`               | `fmt.Sprintf(`"%x"`, hash)`         |
| Node.js  | `crypto.createHash('sha256')` | `'"' + hash.digest('hex') + '"'`    |
| Python   | `hashlib.sha256()`            | `f'"{h.hexdigest()}"'`              |
| Rust     | `sha2::Sha256`                | `format!("\"{}\"", hex)`            |
| PHP      | `hash_file('sha256', $path)`  | `'"' . hash_file('sha256', $p) . '"'` |

ETag value MUST be wrapped in double quotes per RFC 7232: `"abc123..."`.

**Strong vs Weak ETags:**
- Strong ETag (`"abc123"`) — bytewise identical content guarantee.
- Weak ETag (`W/"abc123"`) — semantically equivalent content (e.g., same data, different whitespace). Use when:
  - Computing ETag from metadata (mtime + size) instead of content
  - Response goes through compression middleware (gzip/brotli)
  - Template-rendered pages where minor formatting differences are acceptable

**Note on "startup time":** This applies to long-running processes (Go, Node.js, Python servers, Rust). PHP-FPM and request-per-process models compute on demand — cache the hash via APCu or filesystem-derived metadata to avoid hashing on every request.

#### Conditional Request Handling

Before writing the response body, check the `If-None-Match` request header. The header may contain a comma-separated list of ETags or `*`:

```
If-None-Match: "abc"
If-None-Match: "abc", "def", W/"ghi"
If-None-Match: *
```

Parse it as a list, not an exact-match string:

```go
func matchETag(ifNoneMatch, etag string) bool {
    if ifNoneMatch == "" {
        return false
    }
    if strings.TrimSpace(ifNoneMatch) == "*" {
        return true
    }
    for _, tag := range strings.Split(ifNoneMatch, ",") {
        tag = strings.TrimSpace(tag)
        // Compare ignoring weak prefix per RFC 7232 §2.3.2 weak comparison
        tag = strings.TrimPrefix(tag, "W/")
        candidate := strings.TrimPrefix(etag, "W/")
        if tag == candidate {
            return true
        }
    }
    return false
}
```

Set these headers on ALL cacheable responses (both 200 and 304):
- `ETag: "content-hash"`
- `Cache-Control: <strategy from table above>`
- `Vary: <relevant axes>` (see Vary section below)
- `Last-Modified: <RFC 1123 date>` (optional but recommended for static files — improves proxy/CDN compatibility)

#### Vary Header

Set `Vary` whenever the response varies along an axis the cache should distinguish:

| Condition                                     | Required Vary value           |
|-----------------------------------------------|-------------------------------|
| Response uses gzip/brotli compression         | `Accept-Encoding`             |
| Response varies by language (i18n)            | `Accept-Language`             |
| Response varies by auth state                 | `Cookie` or `Authorization`   |
| Content negotiation (JSON vs HTML)            | `Accept`                      |

**Compression + ETag interaction:** If a compression middleware (gzip/brotli) sits AFTER your handler, ETag is computed on the uncompressed body but the wire body differs by `Accept-Encoding`. Two safe options:

1. **Weak ETag + `Vary: Accept-Encoding`** — declares semantic equivalence across encodings.
2. **Compute ETag after compression** — strong ETag remains valid but couples handler with middleware.

Never use a strong ETag with multiple encoded variants and no `Vary` — this is a spec violation and can cause cache poisoning across users.

#### Per-Framework Patterns

**Go (net/http) — Prefer `http.ServeContent` for static files:**

The standard library already handles `If-None-Match`, `If-Modified-Since`, Range requests, and Content-Type detection. Use it instead of manual implementation when possible:

```go
func cachedFileHandler(content fs.FS, filename, cacheControl string) http.HandlerFunc {
    data, err := fs.ReadFile(content, filename)
    if err != nil {
        return func(w http.ResponseWriter, r *http.Request) {
            http.Error(w, "not found", http.StatusNotFound)
        }
    }
    etag := fmt.Sprintf(`"%x"`, sha256.Sum256(data))
    modTime := time.Now() // or actual file mtime if available

    return func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Cache-Control", cacheControl)
        w.Header().Set("ETag", etag)
        // ServeContent handles If-None-Match, If-Modified-Since, Range, HEAD,
        // and sets Content-Type from filename.
        http.ServeContent(w, r, filename, modTime, bytes.NewReader(data))
    }
}
```

**Go (net/http) — Manual handler when ServeContent is not suitable:**

```go
func contentETag(data []byte) string {
    return fmt.Sprintf(`"%x"`, sha256.Sum256(data))
}

func cachedHandler(data []byte, contentType, cacheControl string) http.HandlerFunc {
    etag := contentETag(data)
    return func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", contentType)
        w.Header().Set("Cache-Control", cacheControl)
        w.Header().Set("ETag", etag)

        if matchETag(r.Header.Get("If-None-Match"), etag) {
            w.WriteHeader(http.StatusNotModified)
            return
        }
        if r.Method == http.MethodHead {
            return
        }
        w.Write(data)
    }
}
```

**Express (Node.js) — Built-in ETag:**

Express auto-generates weak ETags by default. For most cases this is enough:

```javascript
app.set('etag', 'strong'); // or 'weak' (default), or false to disable
```

For custom static handlers with strong content-hashed ETag:

```javascript
const crypto = require('crypto');
const fs = require('fs');

function etag(data) {
  return '"' + crypto.createHash('sha256').update(data).digest('hex') + '"';
}

function matchETag(header, tag) {
  if (!header) return false;
  if (header.trim() === '*') return true;
  const stripWeak = (s) => s.trim().replace(/^W\//, '');
  return header.split(',').some(t => stripWeak(t) === stripWeak(tag));
}

function cachedStatic(filePath, contentType, maxAge) {
  const data = fs.readFileSync(filePath);
  const tag = etag(data);

  return (req, res) => {
    res.set('Content-Type', contentType);
    res.set('Cache-Control', `public, max-age=${maxAge}`);
    res.set('ETag', tag);

    if (matchETag(req.get('If-None-Match'), tag)) {
      return res.status(304).end();
    }
    res.send(data);
  };
}
```

**FastAPI (Python):**

```python
import hashlib
from fastapi import Request
from fastapi.responses import Response

def content_etag(data: bytes) -> str:
    return f'"{hashlib.sha256(data).hexdigest()}"'

def match_etag(header: str | None, tag: str) -> bool:
    if not header:
        return False
    if header.strip() == "*":
        return True
    strip_weak = lambda s: s.strip().removeprefix("W/")
    return any(strip_weak(t) == strip_weak(tag) for t in header.split(","))

def cached_file_response(data: bytes, media_type: str, max_age: int):
    etag = content_etag(data)

    async def handler(request: Request):
        headers = {
            "Cache-Control": f"public, max-age={max_age}",
            "ETag": etag,
        }
        if match_etag(request.headers.get("if-none-match"), etag):
            return Response(status_code=304, headers=headers)
        return Response(content=data, media_type=media_type, headers=headers)

    return handler
```

**PHP (plain, no framework) — Weak ETag from metadata:**

When computing ETag from `filemtime + filesize` (not full content hash), use a **weak validator**. mtime+size cannot guarantee bytewise identity (same-second writes with same size are theoretically possible), so a strong ETag would be a spec violation:

```php
// Weak ETag from file metadata — fast, no hashing per request
$mtime = filemtime($filePath);
$size  = filesize($filePath);
$etag  = 'W/"' . $mtime . '-' . $size . '"';

header('ETag: ' . $etag);
header('Cache-Control: public, max-age=3600');

// Parse If-None-Match as a list
function matchETag($header, $tag) {
    if (!$header) return false;
    if (trim($header) === '*') return true;
    $stripWeak = fn($s) => preg_replace('/^W\//', '', trim($s));
    foreach (explode(',', $header) as $candidate) {
        if ($stripWeak($candidate) === $stripWeak($tag)) {
            return true;
        }
    }
    return false;
}

if (matchETag($_SERVER['HTTP_IF_NONE_MATCH'] ?? '', $etag)) {
    http_response_code(304);
    exit;
}
```

For strong content-based ETag in PHP, use `hash_file('sha256', $filePath)` and cache the result via APCu to avoid hashing on every request. Always check `If-None-Match` BEFORE loading/processing data to skip expensive work on cache hits.

### Phase 3.5: Asset Cache-Busting

**Critical:** Changing server-side `Cache-Control` headers does NOT invalidate files already cached by browsers with a previous `max-age`. The only reliable way to force browsers to fetch updated JS/CSS is to change the URL.

**Two approaches, in order of preference:**

#### 1. Hashed Filenames (preferred when build pipeline exists)

Modern bundlers (Vite, Webpack, esbuild, Rollup, Parcel) emit content-hashed filenames:

```
app.8f3a91.js
style.24aa10.css
```

Combined with `Cache-Control: public, max-age=31536000, immutable`, this is the gold standard:
- New deploy → new filename → guaranteed fresh fetch
- Old filename → still cached forever, no waste
- Works correctly across all CDNs and proxies (no query-string edge cases)

#### 2. Query-String Versioning (fallback for projects without a build pipeline)

For PHP/Go/server-rendered projects without a bundler, append a version query string. The version changes automatically when the file changes on disk:

**PHP:**
```php
function asset($path) {
    $file = __DIR__ . '/' . $path;
    $version = file_exists($file) ? filemtime($file) : time();
    return $path . '?v=' . $version;
}

// Usage in templates
<script src="<?= asset('js/app.js') ?>"></script>
<link rel="stylesheet" href="<?= asset('css/style.css') ?>">
```

**Node.js / Express:**
```javascript
function asset(filePath) {
  const stat = fs.statSync(path.join(__dirname, 'public', filePath));
  return `${filePath}?v=${stat.mtimeMs | 0}`;
}
```

**Go (html/template):**
```go
funcMap := template.FuncMap{
    "asset": func(path string) string {
        info, err := os.Stat(filepath.Join("static", path))
        if err != nil { return path }
        return fmt.Sprintf("%s?v=%d", path, info.ModTime().Unix())
    },
}
// Template: <script src="{{ asset "js/app.js" }}"></script>
```

**Caveats for query-string versioning:**
- Some legacy proxies/CDNs ignore query strings in cache keys — verify behavior in your environment.
- Hashed filenames remain the safer default when feasible.

Apply cache-busting to ALL local `<script src>` and `<link href>` tags. Do NOT apply to CDN URLs (they already use versioned paths).

### Phase 4: Verification

After applying changes, verify:

```bash
# 1. Build succeeds
<project-build-command>

# 2. First request returns 200 + ETag + Cache-Control
curl -sI <url> | grep -iE 'etag|cache-control|vary'

# 3. Conditional request returns 304
ETAG=$(curl -sI <url> | grep -i etag | awk '{print $2}' | tr -d '\r')
curl -sI -H "If-None-Match: $ETAG" <url> | head -1
# Expected: HTTP/1.1 304 Not Modified

# 4. Multi-ETag list is handled
curl -sI -H 'If-None-Match: "wrong", '"$ETAG"', "alsowrong"' <url> | head -1
# Expected: HTTP/1.1 304 Not Modified

# 5. Wildcard match
curl -sI -H 'If-None-Match: *' <url> | head -1
# Expected: HTTP/1.1 304 Not Modified

# 6. Sensitive endpoints have no-store
curl -sI <auth-url> | grep -i cache-control
# Expected: Cache-Control: no-store

# 7. Real-time API endpoints have no-store
curl -sI <api-url> | grep -i cache-control
# Expected: Cache-Control: no-store

# 8. Compression + ETag consistency
curl -sI -H 'Accept-Encoding: gzip' <url> | grep -iE 'etag|vary|content-encoding'
curl -sI -H 'Accept-Encoding: identity' <url> | grep -iE 'etag|vary|content-encoding'
# Expected: Vary includes Accept-Encoding, ETag is weak OR ETags differ between encodings
```

## Rules

- **Default to `scan` mode.** Cache bugs are sinister and hard to detect — apply only after explicit review.
- NEVER cache authenticated HTML unless route is explicitly classified as safe.
- NEVER cache SSE or WebSocket endpoints.
- Use `no-store` (not `no-cache`, not "no header") for: auth, admin, payment, banking, medical, user PII, real-time API responses.
- Use `private, no-cache` only for non-sensitive personalized HTML (e.g., user dashboard with public-ish data).
- ALWAYS wrap ETag values in double quotes (RFC 7232).
- ALWAYS parse `If-None-Match` as a comma-separated list and support `*` and weak validators (`W/`).
- Use weak ETags (`W/"..."`) when:
  - Computing from metadata (mtime + size)
  - Response passes through compression middleware
  - Template render output may have non-semantic differences
- ALWAYS compute hash at startup for static/embedded files in long-running processes; use APCu/equivalent for request-per-process runtimes (PHP-FPM).
- ALWAYS set both `ETag` and `Cache-Control` together.
- ALWAYS handle `If-None-Match` before writing response body or doing expensive work.
- ALWAYS set `Vary` when response varies by encoding, language, auth, or content negotiation.
- For files with content hash in filename (e.g., `app.a1b2c3.js`), use `immutable` and skip ETag (it's redundant and may trigger unnecessary conditional requests).
- Prefer hashed filenames over query-string cache-busting when a build pipeline exists.
- Keep max-age reasonable: HTML 5min, static 1hr, immutable assets 1yr.
- If the project uses a CDN (Cloudflare, Fastly), use `s-maxage` for edge cache TTL distinct from browser `max-age`.
- ALWAYS add URL-based cache-busting (hashed filename or `?v=hash`) to local asset includes — server header changes alone cannot invalidate existing browser caches.
- Never include volatile fields (timestamps, random tokens, request IDs) in responses that use ETag — they make every ETag unique and defeat caching.
- Consider `Last-Modified` alongside `ETag` for static files — improves compatibility with older proxies and clients using `If-Modified-Since`.
- For embedded assets, consider memory cost: loading multi-MB files into RAM at startup may not be appropriate for large media; stream from disk with `http.ServeContent` or equivalent instead.
- Handle `HEAD` requests correctly: same headers as `GET`, no body. Most frameworks do this automatically; verify in manual handlers.
