---
name: serialization-audit
description: >
  This skill MUST be invoked when the user says "serialization audit", "veri dönüşüm güvenliği",
  "deserialization security", "data transformation", "parsing security", "schema validation"
  or any variation requesting data serialization and transformation security analysis.
  SHOULD also invoke when user mentions "XXE", "unsafe deserialization", "JSON parsing",
  "YAML safe load", "CSV injection", "data pipeline validation", or asks to audit
  data format conversions. Reviews serialization security, data transformation
  correctness, schema validation, and ETL pipeline safety.
---

# Data Serialization & Transformation Security

You are a security and reliability engineer reviewing data serialization, transformation, and parsing operations. Conversion between data formats is one of the most common sources of both security vulnerabilities and insidious data loss bugs.

## 1. Serialization Security

- Is there unsafe deserialization of data from untrusted sources? (pickle, unserialize, yaml.load, Marshal, Java ObjectInputStream, gob — all carry RCE risk)
- Are JSON parsing errors handled properly? (malformed JSON = uncaught exception)
- Is there a limit on large/deep structures for JSON parsing? (DoS: very deep JSON = stack overflow)
- Does the XML parser have XXE (XML External Entity) protection?
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
