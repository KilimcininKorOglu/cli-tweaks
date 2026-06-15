---
name: ssti
description: >-
  Detect Server-Side Template Injection (SSTI) vulnerabilities in a codebase
  using a two-phase approach: first find all template rendering sites where
  user-supplied input is used as the template string itself (not as context
  data), then trace whether user-supplied input actually reaches those sites. Use when asked to find SSTI or template injection bugs.
---

# Server-Side Template Injection (SSTI) Detection

You are performing a focused security assessment to find Server-Side Template Injection vulnerabilities in a codebase. This skill uses a two-phase approach with subagents: **recon** (find all places where templates are rendered from dynamic strings) then **taint** (confirm whether user-supplied input reaches those rendering sites as the template string).

---

## What is SSTI

Server-Side Template Injection occurs when user-supplied input is embedded directly into a template string that is then evaluated by a template engine. Unlike passing user data as *context variables* to a static template, SSTI means the user can write template syntax that the engine will execute — leading to arbitrary code execution, file read, or full server compromise.

The core pattern: *unvalidated user input is used as the template string passed to a template engine's render/compile/evaluate function.*

### What SSTI IS

- Passing user input as the template string to be compiled or rendered:
  - `Template(user_input).render()` — Jinja2
  - `env.from_string(user_input).render()` — Jinja2
  - `render_template_string(user_input)` — Flask
  - `ejs.render(user_input, ctx)` — EJS (Node.js)
  - `nunjucks.renderString(user_input, ctx)` — Nunjucks
  - `Handlebars.compile(user_input)(ctx)` — Handlebars
  - `pug.render(user_input, ctx)` — Pug/Jade
  - `_.template(user_input)(ctx)` — Lodash/Underscore
  - `Velocity.evaluate(ctx, user_input)` — Apache Velocity (Java)
  - `new Template("anon", new StringReader(user_input), cfg).process(...)` — FreeMarker (Java)
  - `new ST(user_input).render()` — StringTemplate4 (Java)
  - `thymeleafEngine.process(user_input, ctx)` — Thymeleaf (Java)
  - `\Twig\Environment::createTemplate(user_input)->render(ctx)` — Twig (PHP)
  - `$smarty->fetch("string:" . user_input)` — Smarty (PHP)
  - `Liquid::Template.parse(user_input).render(ctx)` — Liquid (Ruby)
  - `ERB.new(user_input).result(binding)` — ERB (Ruby)
  - `t, _ := template.New("x").Parse(user_input); t.Execute(w, data)` — Go `text/template`
  - `Template.fromString(user_input).render(ctx)` — Pebble (Java)

- Dynamic template name construction where the name itself comes from user input and the engine resolves arbitrary files:
  - `render_template(user_input)` (Flask) where `user_input` is not validated against a safe list
  - `res.render(req.query.template)` (Express) where the template name is user-controlled

### What SSTI is NOT

Do not flag these patterns:

- **User input as context data** (safe — the template is static, only the data changes):
  ```
  render_template("profile.html", name=request.args.get("name"))
  env.get_template("report.html").render(user=user_obj)
  res.render("dashboard", { title: req.body.title })
  ```
- **XSS via template output**: If the template outputs unsanitized user data that is then rendered in a browser — that's XSS, not SSTI
- **Static templates with dynamic filenames validated against an allowlist**: If the template name comes from user input but is strictly validated against a hardcoded set of allowed template names, it's not SSTI
- **Sandboxed template engines configured with a restricted environment**: Liquid, Mustache, and similar logic-less engines cannot execute arbitrary code even if the template string comes from user input — but still flag them as "Needs Manual Review" unless you can confirm the engine is logic-less

### Patterns That Prevent SSTI

When you see these patterns, the code is likely **not vulnerable**:

**1. Static template file with dynamic context (most common safe pattern)**
```python
# Flask — static template, user input only in context dict
return render_template("user_profile.html", username=request.args.get("name"))

# Express — static view name
res.render("dashboard", { user: req.user })
```

**2. Allowlist validation for template names**
```python
ALLOWED_TEMPLATES = {"invoice.html", "receipt.html", "summary.html"}
template_name = request.args.get("tmpl", "invoice.html")
if template_name not in ALLOWED_TEMPLATES:
    abort(400)
return render_template(template_name)
```

**3. Logic-less / sandboxed engines that don't support code execution**
```javascript
// Mustache — logic-less, cannot execute arbitrary code even if template is user-supplied
const output = Mustache.render(userTemplate, ctx);  // lower risk, but still flag for review
```

---

## Vulnerable vs. Secure Examples

### Python — Flask / Jinja2

```python
# VULNERABLE: user input rendered as template string
@app.route('/greet')
def greet():
    name = request.args.get('name', '')
    template = f"<h1>Hello {name}!</h1>"
    return render_template_string(template)
    # Payload: ?name={{7*7}} → renders "49"
    # RCE:    ?name={{config.__class__.__init__.__globals__['os'].popen('id').read()}}

# SECURE: user input passed as context variable to a static template
@app.route('/greet')
def greet():
    name = request.args.get('name', '')
    return render_template("greet.html", name=name)
```

```python
# VULNERABLE: env.from_string with user-controlled template
@app.route('/preview')
def preview():
    tmpl = request.form.get('template')
    return Environment().from_string(tmpl).render()

# SECURE: load template from trusted file, pass user data as context
@app.route('/preview')
def preview():
    data = request.form.get('data')
    return env.get_template("preview.html").render(data=data)
```

### Node.js — EJS

```javascript
// VULNERABLE: user input as template string
app.get('/render', (req, res) => {
  const tmpl = req.query.template;
  res.send(ejs.render(tmpl, { user: req.user }));
  // Payload: ?template=<%- global.process.mainModule.require('child_process').execSync('id') %>
});

// SECURE: user input only in context data
app.get('/render', (req, res) => {
  res.render('report', { content: req.query.content });
});
```

### Node.js — Nunjucks

```javascript
// VULNERABLE: renderString with user-controlled template
app.post('/preview', (req, res) => {
  const output = nunjucks.renderString(req.body.tmpl, { user: req.user });
  res.send(output);
  // Payload: {{ range.constructor("return global.process.mainModule.require('child_process').execSync('id').toString()")() }}
});

// SECURE: render from a file, user input only as context
app.post('/preview', (req, res) => {
  res.render('preview.html', { content: req.body.content });
});
```

### Node.js — Handlebars

```javascript
// VULNERABLE: compile with user-supplied template string
app.get('/email', (req, res) => {
  const template = Handlebars.compile(req.query.tmpl);
  res.send(template({ user: req.user }));
  // Payload: {{#with "s" as |string|}}{{#with "e"}}{{#with split as |conslist|}}...
});

// SECURE: compile static template, user data in context
const template = Handlebars.compile(fs.readFileSync('email.hbs', 'utf8'));
app.get('/email', (req, res) => {
  res.send(template({ name: req.query.name }));
});
```

### Ruby — ERB

```ruby
# VULNERABLE: user input passed to ERB constructor
get '/render' do
  tmpl = params[:template]
  ERB.new(tmpl).result(binding)
  # Payload: <%= `id` %>
end

# SECURE: static ERB file, user data in binding only
get '/render' do
  @name = params[:name]
  erb :profile
end
```

### Java — FreeMarker

```java
// VULNERABLE: template string sourced from user input
@PostMapping("/preview")
public String preview(@RequestParam String tmplStr, Model model) throws Exception {
    Template t = new Template("preview", new StringReader(tmplStr), cfg);
    StringWriter out = new StringWriter();
    t.process(model.asMap(), out);
    return out.toString();
    // Payload: <#assign ex="freemarker.template.utility.Execute"?new()>${ex("id")}
}

// SECURE: load template from classpath, user data only in model
@GetMapping("/report")
public String report(@RequestParam String userId, Model model) {
    model.addAttribute("user", userService.findById(userId));
    return "report";  // resolves to templates/report.ftl
}
```

### Java — Velocity

```java
// VULNERABLE: user input evaluated as template
public String render(String userTemplate) {
    VelocityContext ctx = new VelocityContext();
    StringWriter sw = new StringWriter();
    Velocity.evaluate(ctx, sw, "template", userTemplate);
    return sw.toString();
    // Payload: #set($e="")#set($x=$e.class.forName("java.lang.Runtime"))...
}

// SECURE: load template from file
Template t = Velocity.getTemplate("report.vm");
t.merge(ctx, sw);
```

### Java — Thymeleaf (Spring)

```java
// VULNERABLE: user input used as template expression evaluated by Thymeleaf
@GetMapping("/hello")
public String hello(@RequestParam String lang, Model model) {
    return "user/" + lang + "/welcome";  // path traversal + SSTI if lang is e.g. "__${T(java.lang.Runtime).getRuntime().exec('id')}"
}

// SECURE: validate lang against an allowlist
private static final Set<String> ALLOWED_LANGS = Set.of("en", "fr", "de");

@GetMapping("/hello")
public String hello(@RequestParam String lang, Model model) {
    if (!ALLOWED_LANGS.contains(lang)) return "error";
    return "user/" + lang + "/welcome";
}
```

### PHP — Twig

```php
// VULNERABLE: user input as template string
$app->get('/render', function (Request $request) use ($twig) {
    $tmpl = $request->query->get('template');
    return $twig->createTemplate($tmpl)->render([]);
    // Payload: {{_self.env.registerUndefinedFilterCallback("exec")}}{{_self.env.getFilter("id")}}
});

// SECURE: static template, user data in context array
$app->get('/profile', function (Request $request) use ($twig) {
    return $twig->render('profile.html.twig', ['name' => $request->query->get('name')]);
});
```

### PHP — Smarty

```php
// VULNERABLE: user-controlled template string via fetch("string:...")
$template = $_GET['tmpl'];
$smarty->fetch("string:" . $template);
// Payload: {php}echo shell_exec('id');{/php}

// SECURE: pass user data as template variable
$smarty->assign('name', $_GET['name']);
$smarty->display('profile.tpl');
```

### Go — text/template

```go
// VULNERABLE: user input parsed as template
func handler(w http.ResponseWriter, r *http.Request) {
    tmpl := r.URL.Query().Get("tmpl")
    t, _ := template.New("x").Parse(tmpl)
    t.Execute(w, data)
    // Payload: {{.Func "os/exec" "id"}} — depends on data methods exposed
}

// SECURE: static template string or file; user input only in data
func handler(w http.ResponseWriter, r *http.Request) {
    t := template.Must(template.ParseFiles("tmpl/page.html"))
    t.Execute(w, map[string]string{"Name": r.URL.Query().Get("name")})
}
// Note: Go's html/template auto-escapes output, but text/template does not.
// Even html/template is vulnerable to SSTI if user input reaches .Parse().
```

---

## Execution

### Phase 1: Find Template Rendering Sites Using Dynamic Strings

Launch a subagent with the following instructions:

> **Goal**: Find every location in the codebase where a template engine renders, compiles, or evaluates a **dynamically built string** as the template itself — rather than loading a static template file. Write results to `Phase 1 findings`.
>
> **Context**: You will be given the project's architecture summary. Use it to understand the tech stack, template engines in use, and how views/responses are rendered.
>
> **What to search for — vulnerable template rendering patterns**:
>
> Flag any call where the first argument (the template string) is a variable, a concatenated string, or any non-literal value. You are not yet checking whether that variable comes from user input — that is Phase 2's job.
>
> 1. **Python — Jinja2 / Flask**:
>    - `render_template_string(var)` — any non-literal argument
>    - `Environment().from_string(var)` or `env.from_string(var)`
>    - `jinja2.Template(var).render(...)`
>    - `Template(var)` where Template is imported from jinja2
>
> 2. **Python — Mako**:
>    - `Template(var).render(...)` where Template is from `mako.template`
>    - `mako.template.Template(var)`
>
> 3. **Node.js — EJS**:
>    - `ejs.render(var, ...)` or `ejs.renderFile(var, ...)` where var is not a static string literal
>
> 4. **Node.js — Nunjucks**:
>    - `nunjucks.renderString(var, ...)` — any non-literal first argument
>    - `env.renderString(var, ...)`
>
> 5. **Node.js — Handlebars**:
>    - `Handlebars.compile(var)` — any non-literal argument
>    - `Handlebars.precompile(var)`
>
> 6. **Node.js — Pug/Jade**:
>    - `pug.render(var, ...)` — any non-literal argument
>    - `pug.compile(var, ...)`
>
> 7. **Node.js — Lodash/Underscore**:
>    - `_.template(var)` — any non-literal argument
>    - `Handlebars.compile(var)`
>
> 8. **Node.js — Swig / Twig.js**:
>    - `swig.render(var, ...)`
>    - `twig({ data: var })`
>
> 9. **Ruby — ERB**:
>    - `ERB.new(var).result(...)` — any non-literal argument
>    - `ERB.new(var).result_with_hash(...)`
>
> 10. **Ruby — Liquid**:
>     - `Liquid::Template.parse(var).render(...)` — any non-literal argument
>
> 11. **Java — FreeMarker**:
>     - `new Template(name, new StringReader(var), cfg)` — var is not a literal
>     - `cfg.getTemplate(var)` where var is not a literal (potential template path injection)
>
> 12. **Java — Velocity**:
>     - `Velocity.evaluate(ctx, writer, logTag, var)` — any non-literal fourth argument
>     - `ve.evaluate(ctx, writer, logTag, var)`
>
> 13. **Java — StringTemplate / ST4**:
>     - `new ST(var)` — any non-literal argument
>     - `new STGroup(var, ...)` with non-literal path
>
> 14. **Java — Thymeleaf**:
>     - Controller methods returning a view name built by string concatenation: `return "user/" + var + "/page"` or `return String.format("prefix/%s/suffix", var)`
>     - `templateEngine.process(var, ctx)` with non-literal var
>
> 15. **PHP — Twig**:
>     - `$twig->createTemplate($var)->render(...)` — any non-literal argument
>     - `$environment->createTemplate($var)`
>
> 16. **PHP — Smarty**:
>     - `$smarty->fetch("string:" . $var)` or `$smarty->display("string:" . $var)`
>     - `$smarty->fetch($var)` where var may contain a "string:" prefix
>
> 17. **PHP — Blade / Laravel**:
>     - `Blade::render($var, ...)` — any non-literal argument
>     - `\Illuminate\Support\Facades\View::make($var, ...)` with non-literal name (template path injection)
>
> 18. **Go — text/template or html/template**:
>     - `template.New(name).Parse(var)` — any non-literal argument to Parse
>     - `t.Parse(var)` on any template variable
>     - `t.ParseFiles(var)` with non-literal var (template path injection)
>
> 19. **C# — Scriban / Handlebars.Net / DotLiquid / Fluid**:
>     - `Template.Parse(var)` (Scriban) — non-literal
>     - `Handlebars.Compile(var)` — non-literal
>     - `DotLiquid.Template.Parse(var)` — non-literal
>     - `FluidParser.TryParse(var, ...)` — non-literal
>
> **What to skip** (safe patterns — do not flag):
> - Calls where the first argument is a **string literal**: `render_template_string("<h1>Hello</h1>")`, `ejs.render("<p>static</p>", ctx)`
> - Calls where a file path is loaded from a trusted constant and user input only appears in context: `render_template("profile.html", user=user_obj)`
> - Template engine configuration calls that do not render user-supplied content: `env = Environment(loader=FileSystemLoader("templates/"))`
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # SSTI Recon: [Project Name]
>
> ## Summary
> Found [N] locations where a template engine renders a dynamic (non-literal) string as the template.
>
> ## Candidate Rendering Sites
>
> ### 1. [Descriptive name — e.g., "render_template_string in /greet endpoint"]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Function / endpoint**: [function name or route]
> - **Template engine**: [Jinja2 / EJS / Handlebars / FreeMarker / Twig / ERB / etc.]
> - **Rendering call**: [render_template_string / from_string / ejs.render / Handlebars.compile / etc.]
> - **Dynamic argument**: `var_name` — [brief note on what it appears to represent, e.g., "looks like it comes from a form field" or "unknown origin"]
> - **Code snippet**:
>   ```
>   [the rendering call with the dynamic argument]
>   ```
>
> [Repeat for each site]
> ```

### Phase 2: Batched Verify — Trace User Input to Template Rendering Sites

After Phase 1 completes, count the numbered site sections (`### 1.`, `### 2.`, ...) from Phase 1 findings.

**If 3 or fewer sites**: Launch a single subagent with all sites (skip batching).

**If more than 3 sites**: Split into batches of up to 3 each. Launch all batch subagents **in parallel**. Each subagent returns findings in its response (NOT to a file).

Give each batch subagent the following instructions (include assigned sites from Phase 1):

>
> **Context**: You will be given the project's architecture summary and the Phase 1 recon output. Use the architecture to understand request entry points, middleware, and how data flows through the application.
>
> **For each rendering site, trace the dynamic template argument backwards to its origin**:
>
> 1. **Direct user input** — the argument is assigned directly from a request source with no transformation:
>    - HTTP query params: `request.GET.get(...)`, `req.query.x`, `params[:x]`, `$_GET['x']`, `c.Query("x")`
>    - Path parameters: `request.path_params['id']`, `req.params.id`, `params[:id]`
>    - Request body / form fields: `request.POST.get(...)`, `req.body.x`, `params[:x]`, `$_POST['x']`
>    - HTTP headers: `request.headers.get(...)`, `req.headers['x']`
>    - Cookies: `request.COOKIES.get(...)`, `req.cookies.x`
>    - File upload content: if a file's content is read and passed as the template string
>
> 2. **Indirect user input** — the argument is derived from user input through transformations, function calls, or intermediate assignments. Trace the full chain:
>    - Variable assigned from a function return value → check that function's parameter origin
>    - Variable passed as a function argument → check the call site(s)
>    - Variable read from a class attribute or shared state set elsewhere → find the setter
>    - Variable conditionally assigned — check all branches
>
> 3. **Second-order input** — the template string is read from the database, a config store, or a file, but the stored value originally came from user input (e.g., user-submitted "custom email template" feature):
>    - Find where this value was written — was it stored from a user-supplied field?
>    - Was it sanitized before storage? Note: sanitizing SSTI payloads is unreliable — still flag.
>
> 4. **Server-side / hardcoded value** — the template string comes from a file loaded at startup, a hardcoded constant, or server-side logic with no user influence — this site is NOT exploitable.
>
> **For each rendering site, also assess the template engine's risk level**:
> - **Critical**: Jinja2, Mako, Twig, Smarty, FreeMarker, Velocity, ERB, Pug, EJS, Go `text/template`, Thymeleaf — full code execution possible
> - **High**: Handlebars (with prototype pollution gadgets), Nunjucks, Lodash `_.template`, Blade, Razor
> - **Medium / Logic-less**: Mustache, Liquid (without dangerous tags enabled) — arbitrary code execution not typically possible, but still check for data leakage
>
> **For each rendering site, also check for mitigations**:
> - Is the template engine running in a sandboxed mode? (e.g., Jinja2 `SandboxedEnvironment`, Twig `sandbox` extension with strict policy)
> - Is the input validated or filtered before being used as a template? Note: blocklist-based filtering of template syntax characters (`{`, `}`, `%`) is **not** a reliable mitigation — attackers can often bypass it.
> - Is the result of rendering passed directly to the response, or is it used in a non-dangerous context?
>
> **Classification**:
> - **Vulnerable**: User input demonstrably reaches the template string argument with no effective mitigation, using a critical/high-risk engine.
> - **Likely Vulnerable**: User input probably reaches the template string (indirect flow or second-order), or a medium-risk engine is used, or only blocklist filtering is applied.
> - **Not Vulnerable**: The template string is server-side only (file, constant, hardcoded), OR a properly configured sandbox is confirmed in place.
> - **Needs Manual Review**: Cannot determine the argument's origin with confidence, or a logic-less engine is used and data leakage scope is unclear.
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # SSTI Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Endpoint / function**: [route or function name]
> - **Template engine**: [Jinja2 / Twig / etc.]
> - **Issue**: [description of taint flow]
> - **Taint trace**: [Step-by-step from source to template render]
> - **Impact**: [What attacker can do]
> - **Remediation**: [Use template context vars, sandbox, etc.]
> - **Dynamic test**: [curl command or payload]
>
> ### [LIKELY VULNERABLE] / [NOT VULNERABLE] / [NEEDS MANUAL REVIEW]
> [Similar format]
> ```
>
> **Severity mapping** (for use in Phase 3 reporting):
> - Code execution via template engine → CRITICAL

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity per the mapping above
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - For **Verification**: include the full taint trace and a dynamic test command or payload
   - Separate each field with a blank line; end each entry with a `---` separator
4. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1 completes. Phase 3 runs AFTER all batches complete.
- Batch size is **3 sites per subagent**. If 1-3 total, use a single subagent. Launch all batches **in parallel**.
- Each batch subagent receives only its assigned sites, not all Phase 1 findings.
- **Phase 1 is purely structural**: flag any dynamic (non-literal) variable used as the template string argument. Do not attempt to trace user input in Phase 1 — that is Phase 2's job.
- **Phase 2 is purely taint analysis**: for each site found in Phase 1, trace the dynamic template argument back to its origin. If it comes from a user-controlled source, the site is a real vulnerability.
- The critical distinction is **template string vs. template context**: user input passed as a *variable name/value* inside `render_template("page.html", user=input)` is safe. User input passed as the *template string itself* to `render_template_string(input)` is dangerous.
- **Second-order SSTI is easy to miss**: a "custom template" feature may let users store Jinja2/Twig syntax in the database. When that stored template is later loaded and rendered server-side without sandboxing, it's SSTI. In Phase 2, treat DB-read template strings as potentially tainted.
- **Thymeleaf fragment expressions**: in Spring Boot, if a controller returns a view name constructed from user input (e.g., `return "user/" + lang + "/view"`), Thymeleaf may process Spring EL expressions embedded in the path segment, enabling RCE. Flag any controller that builds a view name string using user-supplied values.
- **Blocklist filtering is not a mitigation**: attempts to strip `{{`, `}}`, `<%`, `%>` etc. from user input are routinely bypassed via encoding, alternate syntax, or nested expressions. Do not classify a finding as "Not Vulnerable" solely because filtering is present.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable". False negatives are worse than false positives in security assessment.
- Include engine-appropriate proof-of-concept payloads for all Vulnerable and Likely Vulnerable findings. Payloads should first test with a math expression (e.g., `{{7*7}}`) to confirm template execution before escalating to RCE payloads.