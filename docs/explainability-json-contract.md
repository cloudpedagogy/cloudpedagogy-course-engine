# Explainability JSON Contract

> **Applies to course-engine v1.10+**  
> This document defines the **contract-stable JSON output** produced by the validation command in explain mode.

The Course Engine provides a machine-readable explainability interface intended for:

- CI pipelines
- dashboards
- governance tooling
- automated provenance capture

This interface is **read-only** and **contract-stable**.

---

## How to generate

### Explain-only (no validation)

```bash
course-engine validate <dist/course-dir> \
  --policy <policy-source> \
  --profile <profile-name> \
  --explain \
  --json
```

Notes:

- In `--explain` mode, validation is **not executed**.
- No learning content is evaluated.
- No artefacts are modified.
- The output describes **resolved policy rules and signal interpretation logic** only.

---

## Stability promise

Within a major version, the meaning and structure of the JSON output is intended to remain stable.

Additions may occur in future minor versions (new optional keys), but existing keys will not change meaning, and existing structures will not be broken.

---

## Top-level JSON shape

The explainability JSON is an object with these top-level keys:

- `policy` (object) — provenance and identity of the loaded policy
- `profile` (object) — selected profile metadata
- `chain` (array of strings) — resolved inheritance chain, parent-first
- `rules` (object) — resolved effective rules after inheritance and overrides
- `strict` (boolean) — whether strict mode was requested (`--strict`)

---

> **Note on scope (v1.13+)**
>
> The explainability JSON describes **policy resolution only**:
> - which rules apply,
> - how profiles are inherited,
> - and how signal severities *would* be interpreted.
>
> It does **not** include:
> - computed absence signals,
> - course-specific governance facts,
> - or manifest-derived state.
>
> Those are recorded separately in `manifest.json` under the `signals` key.
> This separation is intentional and ensures:
> - explain output remains contract-stable and reusable,
> - governance facts remain tied to a specific build artefact.

---

## Field definitions

### `policy` (object)

Contains provenance/identity fields for the loaded policy.

Expected keys:

- `source` (string) — how the policy was sourced (e.g. `preset:strict-ci` or a filepath)
- `policy_id` (string)
- `policy_name` (string)
- `owner` (string)
- `last_updated` (string; ISO date recommended)
- `policy_version` (integer)

Additional informational keys may be included by institutional policy files.

---

### `profile` (object)

- `name` (string) — selected profile name
- `description` (string or null) — optional profile description

---

### `chain` (array)

An ordered list of profile names representing the resolved inheritance chain.

Example:

```json
["baseline", "strict-ci"]
```

---

### `rules` (object)

Resolved effective rules after applying inheritance and profile overrides.

Known rule keys include:

- `require_coverage.min_domains` (integer)
- `require_evidence.min_items_per_domain` (integer)
- `min_coverage_items_per_domain` (integer)
- `forbid_empty_domains` (boolean)

In v1.13+, policies may also define **signal handling rules**, including:

- default signal action (`ignore`, `info`, `warn`, `error`)
- per-signal overrides (e.g. `SIG-AI-001: warn`)

These rules describe **how signals would be interpreted** during validation;
the signals themselves are neither computed nor emitted in explain mode.

---

### `strict` (boolean)

Indicates whether strict mode was requested during validation.

Strict mode changes **severity** handling, not rule thresholds.

---

## Example output

```json
{
  "policy": {
    "source": "preset:strict-ci",
    "policy_id": "preset:strict-ci",
    "policy_name": "Strict CI Validation Policy (Example Preset)",
    "owner": "Course Engine (preset)",
    "last_updated": "2026-01-09",
    "policy_version": 1
  },
  "profile": {
    "name": "strict-ci",
    "description": null
  },
  "chain": [
    "baseline",
    "strict-ci"
  ],
  "rules": {
    "require_coverage": {
      "min_domains": 6
    },
    "require_evidence": {
      "min_items_per_domain": 2
    },
    "min_coverage_items_per_domain": 2,
    "forbid_empty_domains": true
  },
  "strict": false
}
```

---

## Important disclaimers

This JSON output:

- does not evaluate pedagogical quality
- does not infer alignment
- does not imply compliance
- describes resolved rules and provenance only
- does not represent the governance state of a specific course build

It is intended to support transparent, auditable assurance workflows.
