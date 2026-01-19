# Policy Files Guide

> **Applies to course-engine v1.4+ (policy-based validation), including v1.10+ explainability contract (`--explain --json`) and v1.6+ external lesson source support.**

This document explains how **policy files** are used with the CloudPedagogy Course Engine to configure **capability-mapping validation** in a transparent, defensible way.

Policy files define **local validation thresholds**.
They do **not** define quality standards, pedagogical effectiveness, or compliance with external frameworks.

---

## What is a policy file?

A policy file is a human-editable configuration file (YAML or JSON) that defines:

- one or more **validation profiles**
- the **thresholds** applied by each profile
- optional metadata for audit and governance contexts

Policy files are evaluated by the engine during validation, but they are **owned by the user or institution**, not by the tool.

The engine:
- evaluates declared structure and traceability
- applies thresholds defined in the policy
- reports results transparently

The engine does **not**:
- interpret meaning
- infer quality
- enforce compliance

---

## Presets vs institutional policy files

There are two ways to use policy files.

### Preset policies (examples)

Preset policies are shipped with the engine and selected via:

```bash
--policy preset:<name>
```

**Examples:**
- `preset:baseline`
- `preset:higher-ed-example`
- `preset:strict-ci`

**Presets:**
- are examples only
- are not standards or recommendations
- include explicit disclaimers
- are intended to be copied and adapted

You should not modify preset files directly.

---

### Institutional policy files (recommended)

Institutional policy files are external files owned by you or your organisation.

They:
- live in your own repository or project
- reflect local assurance expectations
- can be reviewed, versioned, and audited independently

**Example:**

```bash
course-engine validate dist/course \
  --policy policies/my-institution.yml \
  --profile qa-lite
```

This is the preferred pattern for sustained use.

---

## Basic policy file structure

All policy files follow the same high-level structure.

```yaml
policy_version: 1

policy_id: "example:institution-policy"
policy_name: "Institution Validation Policy"
owner: "Example Institution"
last_updated: "2026-01-09"
notes: >
  Example policy file. Thresholds are structural defensibility checks only.
  Passing does not imply quality, completeness, or compliance.

default_profile: "qa-lite"

profiles:
  qa-lite:
    description: "Routine QA thresholds"
    rules:
      require_coverage:
        min_domains: 4
      require_evidence:
        min_items_per_domain: 1
      min_coverage_items_per_domain: 1
      forbid_empty_domains: false
```

Only `policy_version` and `profiles` are required.
All other fields are informational and intended for governance and audit contexts.

---

## Profiles

A profile is a named set of validation rules.

Profiles allow the same course to be validated under different conditions, for example:
- early design review
- routine QA
- automated CI gating

Profiles are selected via the CLI:

```bash
course-engine validate dist/course --policy policy.yml --profile qa-lite
```

If no profile is specified:
- the policy’s `default_profile` is used (if defined)
- otherwise the engine default (`baseline`) is used

---

## Profile inheritance (`extends`)

Profiles may inherit rules from another profile using `extends`.

This allows thresholds to be layered incrementally.

```yaml
profiles:
  baseline:
    rules:
      require_coverage:
        min_domains: 1
      require_evidence:
        min_items_per_domain: 0
      min_coverage_items_per_domain: 0
      forbid_empty_domains: false

  strict-ci:
    extends: "baseline"
    rules:
      require_coverage:
        min_domains: 6
      require_evidence:
        min_items_per_domain: 2
      min_coverage_items_per_domain: 2
      forbid_empty_domains: true
```

---

## Capability mapping required for validation (v1.6+)

Policy validation operates on declared **capability mapping** only.

If a course declares **no `capability_mapping`**, validation fails with a clear message indicating that there is nothing to validate.

---

## Explain-only JSON output (v1.10+)

This output is intended as a stable interface for CI pipelines, dashboards, and external tooling.

```bash
course-engine validate dist/course \
  --policy policies/my-policy.yml \
  --profile strict-ci \
  --explain \
  --json
```

This mode is **read-only** and contract-stable.

---

## Final note

Policy files exist to make validation **transparent, adaptable, and defensible**.

The engine evaluates structure.
You decide what matters.
