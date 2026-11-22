# Documentation claim audit

This offline static audit compares documentation claims about judging JSON data against a declared schema with Python source patterns. It never executes inspected code or uses the network.

## Usage

```sh
json-schema-validation-claim-audit audit .
python3 -m json_schema_validation_claim_audit audit . --json
json-schema-validation-claim-audit audit . --verbose --fail-on medium --ignore vendor
json-schema-validation-claim-audit --version
```

The optional repository defaults to the current directory. Repeat `--ignore` for additional relative path prefixes. The default failure threshold is high; medium includes test-only evidence. Exit status 0 means pass at the selected threshold, 2 indicates a finding at that threshold, and 1 indicates a usage or I/O error. JSON output includes findings, claims, and evidence paths.

## How it works

The audit reads the root README and Markdown files under a docs directory, ignoring fenced blocks but including inline code. It matches a fixed list after normalizing case, whitespace, contractions, and hyphens. Denial spans are removed before positive matches. It inspects Python syntax without execution, excluding symlinks, documentation, fixtures and examples. Tests are counted separately. Invalid Python yields no evidence.

A positive claim with no production evidence produces a high finding, or a medium finding when only tests provide evidence. A denial with production evidence produces a high finding. The identifiers are:

```
documented-json-schema-validation-claim-false
documented-no-json-schema-validation-claim-false
```

## Differentiation

This family concerns judging whether JSON data conforms to a declared schema. It does not cover generic input checks, schema field names, email sending, SMS sending, authentication by a one-time code or confirmation link, document extraction, barcode or QR decoding, email address well-formedness or deliverability, or phone number validity for a region. Decoding JSON text into a value, declaring a model shape, reading a schema file, and matching a JSON-shaped regex are distinct operations.

Other families cover spreadsheet reading and generation, word-document reading and generation, presentation reading and generation, PDF extraction, generation, merging, splitting, encryption, rotation, form-filling, watermarking, redaction, compression and annotation, table extraction, OCR, document extraction, e-signature, payment processing, screen recording, video generation, QR code generation, barcode generation and scanning, audio mixing, generation and editing, source separation, speech recognition, text-to-speech, noise suppression, music generation and transcription. These claims are outside this phrase list.

## Limitations

Each of these phrases may be used in a different sense, producing a false positive:

- A remote or database-held check may be intended:

  ```
  validate json against schema
  ```

- The author may mean only parsing:

  ```
  validate json
  ```

- The author may mean well-formed text:

  ```
  valid json
  ```

- The author may mean that text parses:

  ```
  is valid json
  ```

- The author may be describing a roadmap:

  ```
  json schema validation
  ```

- The author may mean a hosted page:

  ```
  json schema validator
  ```

- The author may mean a syntax check:

  ```
  json validation
  ```

- The author may mean a manual runbook step:

  ```
  check json against schema
  ```

- The author may mean a downstream service:

  ```
  validate data against json schema
  ```

- The author may mean finding parse failures:

  ```
  detect invalid json
  ```

- Static matching cannot determine whether a call actually runs.
- A module held through an untracked variable chain is missed.
- A library import alone is not evidence.
- Roadmap, changelog and TODO prose still counts as a claim.
- Denials outside the fixed list may be missed.
- Other documentation locations are not read.
- Evidence split across modules does not count as a pair.
- Locally defined route names shadow imports and calls.
- Dead code counts as evidence.
- External commands invoked through subprocess are not evidence.
- A generic input check alone is not evidence.
- An email address check alone is not evidence.
- A phone number check alone is not evidence.
- Extraction alone is not evidence.
- A locally defined generic route is shadowed even if it performs the operation.
- Generic routes through untracked alias chains are missed.
- Exact phrases do not capture every paraphrase or intended meaning.
- Implementations in other languages are invisible.
- Dynamically loaded routes are invisible.
- A JSON decoding call alone is not evidence.
- A draft checker construction alone is not evidence.
- An adapter construction alone is not evidence.
- A document checker construction alone is not evidence.
- Compiling a schema alone is not evidence.
- A call-argument decorator alone is not evidence.
- A syntax-checking call alone is not evidence.
- A model class definition alone is not evidence.
- Loading a schema alone is not evidence.
- Catching or constructing a validation exception alone is not evidence.
- Matching a JSON-shaped pattern alone is not evidence.
