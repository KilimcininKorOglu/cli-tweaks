---
name: ssrf
description: >-
  Detect Server-Side Request Forgery (SSRF) vulnerabilities in a codebase using
  a two-phase approach: first find all outbound network call sites (HTTP, TCP,
  DNS requests to remote hosts), then trace whether user-supplied input reaches
  those call sites. Use when asked to find SSRF or
  server-side request forgery bugs.
---

# Server-Side Request Forgery (SSRF) Detection

You are performing a focused security assessment to find SSRF vulnerabilities in a codebase. This skill uses a two-phase approach with subagents: **recon** (find all places that make outbound TCP, DNS, or HTTP requests) then **taint** (confirm whether user-supplied input influences those call sites).

**Prerequisites**: `security/architecture.md` must exist. Run `/bug-report sec-recon` first if it doesn't.

---

## What is SSRF

SSRF occurs when an attacker can cause the server to make outbound network requests to an arbitrary destination — including internal services, cloud metadata endpoints, or other external targets — by supplying or influencing the URL, hostname, IP, or port used in a server-side request.

The core pattern: *unvalidated, user-controlled input reaches the destination argument of an outbound network call.*

### What SSRF IS

- HTTP client calls where the URL or host is built from user input: `requests.get(user_url)`
- Fetching a resource whose location is provided by the client: `fetch(req.body.webhook_url)`
- DNS lookups on a hostname supplied by the user: `dns.lookup(req.query.host)`
- Raw TCP connections to a host/port derived from user input: `socket.connect((user_host, user_port))`
- File-fetching functions used with HTTP/FTP URLs from user input: `file_get_contents($user_url)`
- URL redirectors that forward to a user-supplied destination without validation
- Webhooks, import-from-URL, screenshot services, PDF renderers, image proxies — any feature that fetches a remote resource on behalf of the user

### What SSRF is NOT

Do not flag these:

- **Open redirects**: Redirecting the browser (HTTP 302) to a user-supplied URL — that's a client-side redirect, not a server-side request
- **XSS via URL**: Rendering a user-supplied URL in an `<a>` tag without escaping — that's XSS
- **IDOR**: Accessing another user's data by changing an object ID — separate vulnerability class
- **Hardcoded outbound calls**: HTTP requests to fixed, fully hardcoded URLs with no user influence — not SSRF

### Patterns That Prevent SSRF

When you see these patterns, the code is likely **not vulnerable**:

**1. Strict allowlist of permitted destinations**
```python
ALLOWED_HOSTS = {"api.example.com", "cdn.example.com"}
parsed = urlparse(user_url)
if parsed.hostname not in ALLOWED_HOSTS:
    raise ValueError("Destination not allowed")
requests.get(user_url)
```

**2. Allowlist of permitted URL prefixes / schemes**
```python
ALLOWED_PREFIXES = ["https://api.example.com/", "https://cdn.example.com/"]
if not any(user_url.startswith(p) for p in ALLOWED_PREFIXES):
    abort(400)
requests.get(user_url)
```

**3. No user influence on the destination**
```python
# Destination fully hardcoded — no user input involved
response = requests.get("https://api.thirdparty.com/data")
```

> **Note**: IP blocklists (blocking 169.254.0.0/16, 10.0.0.0/8, etc.) are **not** sufficient protection — they can be bypassed via DNS rebinding, URL encoding, IPv6 notation, decimal IP representation, or redirect chains. Do not treat a blocklist as making a site safe; classify it as Likely Vulnerable.

---

## Vulnerable vs. Secure Examples

### Python — requests

```python
# VULNERABLE: URL fully controlled by user
@app.route('/fetch')
def fetch():
    url = request.args.get('url')
    response = requests.get(url)
    return response.text

# SECURE: strict allowlist on destination host
ALLOWED = {"api.example.com"}
@app.route('/fetch')
def fetch():
    url = request.args.get('url')
    if urlparse(url).hostname not in ALLOWED:
        abort(403)
    response = requests.get(url)
    return response.text
```

### Python — urllib

```python
# VULNERABLE: user controls the URL passed to urlopen
def preview(request):
    target = request.GET.get('target')
    data = urllib.request.urlopen(target).read()
    return HttpResponse(data)

# SECURE: only allow https scheme to a hardcoded host
def preview(request):
    target = request.GET.get('target')
    parsed = urlparse(target)
    if parsed.scheme != 'https' or parsed.hostname != 'media.example.com':
        return HttpResponse(status=400)
    data = urllib.request.urlopen(target).read()
    return HttpResponse(data)
```

### Node.js — fetch / axios

```javascript
// VULNERABLE: webhook URL comes directly from request body
app.post('/webhook/test', async (req, res) => {
  const { url } = req.body;
  const result = await fetch(url);
  res.json(await result.json());
});

// SECURE: allowlist check before fetch
const ALLOWED_HOSTS = new Set(['hooks.example.com']);
app.post('/webhook/test', async (req, res) => {
  const { url } = req.body;
  const { hostname } = new URL(url);
  if (!ALLOWED_HOSTS.has(hostname)) return res.status(403).send('Forbidden');
  const result = await fetch(url);
  res.json(await result.json());
});
```

### Node.js — http.request

```javascript
// VULNERABLE: host and path from query string
app.get('/proxy', (req, res) => {
  const { host, path } = req.query;
  http.get({ host, path }, (proxyRes) => proxyRes.pipe(res));
});
```

### Ruby on Rails — Net::HTTP / OpenURI

```ruby
# VULNERABLE: open() fetches arbitrary URL
def import
  url = params[:url]
  content = URI.open(url).read  # also triggers for open(url) via Kernel#open
  # ...
end

# SECURE: restrict scheme and host
def import
  url = params[:url]
  uri = URI.parse(url)
  raise "Forbidden" unless uri.is_a?(URI::HTTPS) && uri.host == "data.example.com"
  content = uri.open.read
  # ...
end
```

### PHP — cURL

```php
// VULNERABLE: user-supplied URL piped into curl
function fetch_preview($url) {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    $result = curl_exec($ch);
    curl_close($ch);
    return $result;
}
// Called as: fetch_preview($_GET['url'])

// SECURE: validate URL against allowlist before curl
function fetch_preview($url) {
    $allowed = ['https://cdn.example.com/'];
    foreach ($allowed as $prefix) {
        if (strpos($url, $prefix) === 0) {
            // ... proceed with curl
        }
    }
    throw new Exception("Destination not allowed");
}
```

### PHP — file_get_contents

```php
// VULNERABLE: file_get_contents with http:// wrapper and user input
$url = $_GET['source'];
$data = file_get_contents($url);  // fetches remote URL if scheme is http/https/ftp
```

### Java — Spring / OkHttp

```java
// VULNERABLE: RestTemplate with user-controlled URL
@GetMapping("/proxy")
public ResponseEntity<String> proxy(@RequestParam String url) {
    RestTemplate restTemplate = new RestTemplate();
    return restTemplate.getForEntity(url, String.class);
}

// VULNERABLE: OkHttp with user-controlled host
public String fetch(String host, String path) {
    Request request = new Request.Builder()
        .url("https://" + host + path)
        .build();
    return client.newCall(request).execute().body().string();
}
```

### Go — net/http

```go
// VULNERABLE: user-supplied URL passed to http.Get
func proxyHandler(w http.ResponseWriter, r *http.Request) {
    target := r.URL.Query().Get("url")
    resp, err := http.Get(target)
    if err != nil {
        http.Error(w, err.Error(), 500)
        return
    }
    io.Copy(w, resp.Body)
}

// VULNERABLE: user controls host in net.Dial
func dialHandler(w http.ResponseWriter, r *http.Request) {
    host := r.URL.Query().Get("host")
    port := r.URL.Query().Get("port")
    conn, _ := net.Dial("tcp", host+":"+port)
    // ...
}
```

### C# — HttpClient

```csharp
// VULNERABLE: user-supplied URL passed to HttpClient
[HttpGet("proxy")]
public async Task<IActionResult> Proxy([FromQuery] string url)
{
    var response = await _httpClient.GetAsync(url);
    var content = await response.Content.ReadAsStringAsync();
    return Content(content);
}
```

---

## Execution

This skill runs in two phases using subagents. Pass the contents of `security/architecture.md` to both subagents as context.

### Phase 1: Find All Outbound Network Call Sites

Launch a subagent with the following instructions:

> **Goal**: Find every location in the codebase where the application makes an outbound network request — HTTP, HTTPS, FTP, TCP, or DNS — regardless of whether that destination is user-controlled. Write results to `Phase 1 findings`.
>
> **Context**: You will be given the project's architecture summary. Use it to understand the tech stack, HTTP client libraries in use, and any networking or webhook-related components.
>
> **What to search for — outbound request call sites**:
>
> You are looking for any code that opens a network connection or fetches a remote resource. Flag ANY call where a non-trivially-hardcoded URL, host, or address value is passed as an argument. You are not yet tracing whether that value is user-controlled; that is Phase 2's job.
>
> 1. **Python HTTP clients**:
>    - `requests.get(url)`, `requests.post(url)`, `requests.put(url)`, `requests.request(method, url)`, `requests.Session().get(url)`
>    - `urllib.request.urlopen(url)`, `urllib2.urlopen(url)`
>    - `httpx.get(url)`, `httpx.post(url)`, `httpx.AsyncClient().get(url)`
>    - `aiohttp.ClientSession().get(url)`, `aiohttp.ClientSession().post(url)`
>
> 2. **Python socket / DNS**:
>    - `socket.connect((host, port))`, `socket.create_connection((host, port))`
>    - `dns.resolver.resolve(name)`, `socket.getaddrinfo(host, ...)`
>
> 3. **Python file-fetching with remote schemes**:
>    - `urllib.request.urlopen(url)` where url may be http/https/ftp
>    - `open(url)` via `from urllib.request import urlopen` or similar (flag if url may be remote)
>
> 4. **Node.js / JavaScript HTTP clients**:
>    - `fetch(url)`, `node-fetch(url)`
>    - `axios.get(url)`, `axios.post(url)`, `axios.request({url})`
>    - `http.get(url)`, `https.get(url)`, `http.request(options)`, `https.request(options)`
>    - `got(url)`, `superagent.get(url)`, `needle.get(url)`, `undici.request(url)`
>    - `require('request')(options)`
>
> 5. **Node.js socket / DNS**:
>    - `net.createConnection({host, port})`, `net.connect(port, host)`
>    - `dns.lookup(hostname, ...)`, `dns.resolve(hostname, ...)`, `dns.resolve4(hostname)`
>
> 6. **Ruby HTTP clients**:
>    - `Net::HTTP.get(uri)`, `Net::HTTP.start(host, ...)`, `Net::HTTP.get_response(url)`
>    - `URI.open(url)`, `open(url)` (Kernel#open / OpenURI)
>    - `RestClient.get(url)`, `RestClient::Resource.new(url)`
>    - `Faraday.new(url).get(path)`, `HTTParty.get(url)`
>    - `Typhoeus::Request.new(url)`
>
> 7. **PHP HTTP clients and file functions**:
>    - `curl_setopt($ch, CURLOPT_URL, $url)` followed by `curl_exec($ch)`
>    - `file_get_contents($url)` — flag when `$url` may be an http/https/ftp URL
>    - `fopen($url, 'r')` with a remote URL scheme
>    - `Guzzle`: `$client->request('GET', $url)`, `$client->get($url)`
>    - `Symfony HttpClient`: `$client->request('GET', $url)`
>
> 8. **Java HTTP clients**:
>    - `new URL(url).openConnection()`, `new URL(url).openStream()`
>    - `HttpURLConnection` / `HttpsURLConnection` with a dynamic URL
>    - `OkHttpClient().newCall(new Request.Builder().url(url)...)`
>    - `RestTemplate.getForObject(url, ...)`, `RestTemplate.getForEntity(url, ...)`
>    - `WebClient.get().uri(url)`, `WebClient.create(url)`
>    - `Apache HttpClient`: `httpClient.execute(new HttpGet(url))`
>
> 9. **Go HTTP clients and network dials**:
>    - `http.Get(url)`, `http.Post(url, ...)`, `http.NewRequest("GET", url, ...)`
>    - `net.Dial("tcp", addr)`, `net.DialTCP(...)`, `net.DialTimeout("tcp", addr, ...)`
>    - `net.LookupHost(hostname)`, `net.LookupAddr(addr)`, `net.ResolveIPAddr(...)`
>    - `net.ResolveTCPAddr("tcp", addr)`
>
> 10. **C# / .NET HTTP clients**:
>     - `HttpClient.GetAsync(url)`, `HttpClient.PostAsync(url, ...)`, `HttpClient.SendAsync(request)`
>     - `WebRequest.Create(url)`, `WebClient.DownloadString(url)`, `WebClient.DownloadData(url)`
>     - `HttpWebRequest` with a dynamic URL
>
> 11. **Shell-out to network tools** (via subprocess, exec, system, etc.):
>     - `subprocess.run(["curl", url, ...])`, `subprocess.Popen(["wget", url, ...])`
>     - `os.system("curl " + url)`, `exec("wget " + url)`
>     - Any `curl`, `wget`, `nc`, `ncat`, `nmap` invocation where the target is a variable
>
> **What to skip** (these are safe — do not flag):
> - Calls where the entire URL and hostname are fully hardcoded string literals with no dynamic parts: `requests.get("https://api.example.com/data")`
> - Internal loopback connections to `localhost` or `127.0.0.1` that are clearly part of service-to-service architecture (e.g., connecting to a local queue) — flag these if the address is dynamic
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # SSRF Recon: [Project Name]
>
> ## Summary
> Found [N] outbound network call sites.
>
> ## Outbound Call Sites
>
> ### 1. [Descriptive name — e.g., "HTTP GET in webhook dispatcher"]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Function / endpoint**: [function name or route]
> - **Call type**: [HTTP GET / HTTP POST / TCP dial / DNS lookup / subprocess curl / etc.]
> - **Library / method**: [requests.get / fetch / http.Get / curl_exec / etc.]
> - **Destination argument**: `var_name` or `url_expression` — [brief note, e.g., "assembled from query param" or "partially hardcoded path with variable host"]
> - **Code snippet**:
>   ```
>   [the outbound call and the lines immediately before it that construct the destination]
>   ```
>
> [Repeat for each site]
> ```

### Phase 2: Trace User Input to Outbound Call Sites

Launch a second subagent **after Phase 1 completes**, providing Phase 1 findings as context. Instructions:

>
> **Context**: You will be given the project's architecture summary and the Phase 1 recon output. Use the architecture to understand entry points, middleware, and how data flows through the application.
>
> **For each outbound call site, trace the destination argument(s) backwards to their origin**:
>
> 1. **Direct user input** — the destination is assigned directly from a request source with no transformation:
>    - HTTP query params: `request.GET.get('url')`, `req.query.url`, `params[:url]`, `$_GET['url']`, `c.Query("url")`
>    - Request body / JSON fields: `request.json['webhook_url']`, `req.body.target`, `params[:source]`
>    - Path parameters: `req.params.host`, `params[:endpoint]`
>    - HTTP headers: `request.headers.get('X-Forwarded-For')`, `req.headers['destination']`
>    - Cookies: `req.cookies.redirect_url`
>
> 2. **Indirect / assembled destination** — the URL is built by concatenating a hardcoded prefix with a user-supplied suffix or path:
>    - `"https://example.com/" + user_path` — may still be exploitable via path traversal or scheme injection depending on the HTTP client
>    - `base_url + user_query` — user controls the query string, potentially injectable
>    - Flag these as Likely Vulnerable and note which portion is user-controlled
>
> 3. **User input stored and later fetched** — the destination was previously saved from user input (e.g., a stored webhook URL) and is now retrieved from the database to make a request:
>    - Find where the stored value was written — was it accepted from user input without allowlist validation at write time?
>    - Was any validation applied at read time before the request?
>
> 4. **Server-side / hardcoded value** — the destination comes from config, an environment variable, a hardcoded constant, or server-side logic with no user influence — this site is NOT exploitable.
>
> **For each call site, also check for mitigations**:
> - **Strict allowlist of hosts/prefixes**: A hardcoded set of permitted hostnames or URL prefixes that the destination is validated against before the request is made — this is an effective mitigation. Mark as Not Vulnerable.
> - **Scheme-only restriction** (e.g., only allow `https://`): Partial mitigation — reduces impact but does not prevent SSRF to arbitrary HTTPS hosts. Still flag as Likely Vulnerable.
> - **Blocklist of private IP ranges / metadata endpoints**: `169.254.169.254`, `10.0.0.0/8`, `192.168.0.0/16`, etc. — **not** sufficient. Bypassable via DNS rebinding, alternate IP representations, and redirect chains. Flag as Likely Vulnerable.
> - **DNS resolution + IP check** (resolve hostname first, then check resolved IP against blocklist): Stronger than a pure blocklist, but still susceptible to DNS rebinding between the check and the request (TOCTOU). Flag as Likely Vulnerable unless the same resolved IP is explicitly pinned for the request.
>
> **Classification**:
> - **Vulnerable**: User input demonstrably reaches the outbound request destination with no effective mitigation (no allowlist or only a blocklist/scheme check).
> - **Likely Vulnerable**: User input probably reaches the destination (indirect flow or partial construction), or only weak mitigation is present (blocklist, scheme-only check, partial URL prefix).
> - **Not Vulnerable**: The destination is fully server-side, OR a strict host/prefix allowlist is enforced before the request.
> - **Needs Manual Review**: Cannot determine the destination's origin with confidence (opaque helpers, complex conditional flows, or external libraries that resolve the URL).
>
> **Output format** — write confirmed findings to `BUG-REPORT.md` using the shared report format from `../SKILL.md`. Read existing `BUG-REPORT.md` first to continue the ID sequence (start at BUG-001 if none exists).
>
> **Severity mapping**:
> - Reaches internal services / cloud metadata → HIGH
> - External-only targets → MEDIUM
>
> For **Verification**: include the full taint trace and a dynamic test command or payload.
> For **Suggested Commit**: conventional commit message without BUG-IDs.
>
> Do **NOT** write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Read `security/architecture.md` and pass its content to both subagents as context.
- Phase 2 must run AFTER Phase 1 completes — it depends on Phase 1 results.
- **Phase 1 is purely structural**: flag any call site where the destination argument is dynamic (a variable, expression, or assembled string), regardless of whether user input flows there. Do not attempt to trace user input in Phase 1 — that is Phase 2's job.
- **Phase 2 is purely taint analysis**: for each site found in Phase 1, trace the destination argument back to its origin. If it comes from a user-controlled source without an effective allowlist, the site is a real vulnerability.
- **Blocklists are not mitigations**: IP blocklists for private ranges and cloud metadata endpoints are easily bypassed. Always classify such sites as Vulnerable or Likely Vulnerable, not as safe.
- **Partial URL control is still dangerous**: even if the attacker only controls the path or query string portion of the URL, flag it as Likely Vulnerable — depending on the HTTP client behavior, redirect following, and target service, partial control can be enough.
- **Stored destinations are tainted**: if a URL or hostname was accepted from user input at write time and is later used for an outbound request, trace the write-time acceptance. Lack of allowlist validation at write time makes it SSRF.
- **Subprocess curl/wget is SSRF too**: shell-outs that run `curl` or `wget` with a user-supplied URL are just as dangerous as HTTP client calls. Check for these, especially in image-processing, import, or download features.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable". False negatives are worse than false positives in security assessment.
- DNS rebinding note: for findings where only a DNS-resolution-then-blocklist check is present, note the TOCTOU window explicitly in the finding — this is a known bypass technique.