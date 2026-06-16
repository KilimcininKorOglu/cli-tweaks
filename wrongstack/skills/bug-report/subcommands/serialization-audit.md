# Data Serialization & Transformation Security

This subcommand replaces the old standalone `/serialization-audit` skill.

## Command

```bash
/bug-report serialization-audit [--focus serialization|transformation|schema|pipeline|all]
```

You are a security and reliability engineer reviewing data serialization, transformation, and parsing operations. Conversion between data formats is one of the most common sources of both security vulnerabilities and insidious data loss bugs.

## 1. Serialization Security

- Is there unsafe deserialization of data from untrusted sources? (pickle, unserialize, yaml.load, Marshal, Java ObjectInputStream, gob — all carry RCE risk)
- Does the XML parser have XXE (XML External Entity) protection?
- Are JSON parsing errors handled properly? (malformed JSON = uncaught exception)
- Is there a limit on large/deep structures for JSON parsing? (DoS: very deep JSON = stack overflow)
- Is the YAML parser running in safe mode? (SafeLoader/safe_load)
- Is there formula injection risk in CSV/TSV parsing? (`=CMD("calc")` cell value)
- If Protocol Buffers / MessagePack / CBOR are used: are unknown fields handled safely?

## 2. Data Transformation Correctness

- Are there overflow/truncation issues in numeric conversions? (int64 → int32, float → int, large numbers)
- Is there floating point precision loss? (monetary amounts stored as float — CRITICAL)
- Is there data loss in character encoding conversions? (UTF-8 → Latin-1 → UTF-8 round trip)
- Is timezone information lost during date/time serialization?
- Is there ambiguity in boolean conversions? (`"false"` string → `true` boolean in some languages)
- Is there inconsistency in null/nil/undefined conversions? (JSON `null` → language null → database NULL)
- Are enum values forward/backward compatible when serialized? (adding a new enum value breaks old code?)

## 3. Schema Validation

- Is incoming data schema validated at API entry points? (Pydantic, Zod, joi, JSON Schema, protobuf)
- Are unknown/extra fields silently accepted? (should reject or log unexpected data)
- What happens when required fields are missing? (meaningful error or crash)
- Is there a depth limit for nested objects?
- Is there a length limit on string fields? (a 1GB string can crash a field)
- Do numeric fields have range limits? (age: -99999, price: -1)
- Do date fields reject invalid values? ("2024-02-30", "2024-13-01")

## 4. Data Cleaning and Transformation Pipeline

- If a step fails in the ETL/data pipeline, what happens? Does partial data remain?
- Is there validation between data transformation steps? (not just at input, but at each step)
- Are large datasets processed via streaming? (loading everything into memory vs chunk-by-chunk processing)
- Is data transformation logic tested? (edge cases: empty input, single item, very large input)

## XML External Entity (XXE) Deep Scan

XML parsers that have external entity resolution enabled are vulnerable to XXE. Run an automated two-phase scan when the codebase parses XML from user-supplied input.

### What XXE Is

XXE occurs when an XML parser processes a document containing an external entity reference and the parser has entity resolution enabled. An attacker who can supply XML can read arbitrary local files, probe internal services (SSRF), trigger DoS (Billion Laughs), or execute OS commands in some stacks.

### Patterns That Prevent XXE

```python
# Python — defusedxml (always safe)
import defusedxml.ElementTree as ET
tree = ET.parse(source)

# Python — lxml with hardening
parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)

# Java — DocumentBuilderFactory
dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
dbf.setFeature("http://xml.org/sax/features/external-general-entities", false);

# .NET
XmlReaderSettings settings = new XmlReaderSettings {
    DtdProcessing = DtdProcessing.Prohibit, XmlResolver = null
};
```

### Phase 1: Find Vulnerable XML Parsing Sites

Launch a subagent with the following instructions:

> **Goal**: Find every XML parsing call in the codebase where external entity resolution is NOT explicitly disabled. Return findings in your response.
>
> **Flag these patterns (vulnerable — no hardening adjacent)**:
> - Python: `xml.etree.ElementTree.*`, `xml.dom.minidom.*`, `xml.sax.*`, `lxml.etree.*` without `resolve_entities=False`
> - Java: `DocumentBuilderFactory`, `SAXParserFactory`, `XMLInputFactory`, `TransformerFactory` — any instantiation without the disallow-doctype-decl / external-entity features set
> - PHP: `simplexml_load_string()`, `DOMDocument::loadXML()` — without `libxml_disable_entity_loader(true)` or `LIBXML_NONET`
> - .NET: `XmlDocument`, `XmlTextReader`, `XPathDocument` — without `DtdProcessing.Prohibit` and `XmlResolver = null`
> - Node.js: `libxmljs.parseXmlString()`, `node-expat`
> - Ruby: `Nokogiri::XML(...) { |c| c.noent }` (noent enables entity expansion)
>
> **Skip** (safe): `defusedxml` usage, Nokogiri default (no options), Go `encoding/xml` standard library, Java parsers with `disallow-doctype-decl=true`.
>
> Return findings as structured markdown with file, lines, parser used, missing hardening, and code snippet.

If Phase 1 finds no vulnerable parsing sites, skip Phase 2.

### Phase 2: Trace User Input to Vulnerable Parsers

Launch a second subagent **after Phase 1 completes**, providing Phase 1 findings as context. Instructions:

> For each parsing site, trace the XML input to its origin:
> - **Direct**: HTTP request body, file upload, query params
> - **Indirect**: user-supplied URL fetched and parsed, user input embedded in XML template
> - **Server-side only**: bundled config file at startup — NOT exploitable
>
> Assess: is the response returned (reflected XXE) or only side effects observable (blind XXE via DNS/HTTP callback)?
>
> **Output format** — write confirmed findings to `BUG-REPORT.md` using the shared report format from `../SKILL.md`.
>
> **Severity mapping**:
> - Local file read or internal SSRF → HIGH
> - Limited reachability → MEDIUM
>
> Do **NOT** write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

**Key reminders**: `LIBXML_NOENT` in PHP EXPANDS entities — it does NOT protect. Blind XXE is still exploitable via DNS/HTTP callbacks. Trace full async pipelines (file uploaded in one handler, parsed in a background job).

---

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
