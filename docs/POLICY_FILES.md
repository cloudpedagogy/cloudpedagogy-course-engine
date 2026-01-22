# Policy Files Guide

> **Applies to course-engine v1.4+ (policy-based validation), including v1.10+ explainability contract (`--explain --json`), v1.12+ design intent, and v1.13+ governance signals.**

This document explains how **policy files** are used with the CloudPedagogy Course Engine to configure **capability-mapping validation** and **governance signal interpretation** in a transparent, defensible way.

Policy files define **local validation thresholds and interpretation rules**.
They do **not** define quality standards, pedagogical effectiveness, or compliance with external frameworks.

---

## What is a policy file?

A policy file is a human-editable configuration file (YAML or JSON) that defines:

- one or more **validation profiles**
- the **structural thresholds** applied by each profile
- optional **governance signal interpretation rules**
- optional metadata for audit and governance contexts

Policy files are evaluated by the engine during validation and explain workflows, but they are **owned by the user or institution**, not by the tool.

The engine:
- evaluates declared structure and traceability
- computes governance signals at build time (informational facts)
- applies thresholds and interpretation rules during validation
- reports results transparently

The engine does **not**:
- interpret pedagogical meaning
- infer educational quality
- enforce compliance with external standards

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

A profile is a named set of validation rules and interpretation settings.

Profiles allow the same course to be evaluated under different conditions, for example:
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

Inheritance applies only to **rules** and **signals** blocks.
Metadata fields are not inherited.

---

## Governance signals (v1.13+)

Governance signals are **informational facts** computed by the engine about what is **present or absent** in a course specification.

Examples include:
- design intent not declared
- framework alignment missing
- learning objectives missing
- assessments not declared
- attribution or citation metadata absent

Signals:
- are computed by the engine
- are **non-blocking by default**
- do not score, rank, or judge quality
- are intended to support QA, audit, and review conversations

### Policy-driven interpretation of signals

Policies may define how signals should be **interpreted or escalated**.

This allows institutions to decide:
- which signals to ignore
- which to surface as informational messages
- which to treat as warnings
- which (if any) should be treated as errors in CI contexts

Signals are interpreted **by policy**, not by the engine itself.

### Signals configuration (profile-level)

Signals are configured per profile using a `signals` block:

```yaml
profiles:
  baseline:
    rules:
      require_coverage:
        min_domains: 1

    signals:
      # One of: ignore | info | warn | error
      default_action: "warn"

      overrides:
        SIG-INTENT-001: "warn"        # Design intent not declared
        SIG-FRAMEWORK-001: "warn"     # Missing framework alignment
        SIG-ASSESS-001: "warn"        # Missing assessment declaration

      ignore:
        - SIG-EXPERIMENTAL-999        # Suppress entirely
```

### Interpretation rules

Signal handling follows this precedence order:

1. **ignore list** – signal is suppressed entirely
2. **explicit override** – action defined per signal ID
3. **default_action** – applied if no override exists

This ensures deterministic, auditable behaviour.

### Design principles

- signals never enforce policy
- policies interpret signals
- defaults are safe and backwards-compatible
- CI escalation is explicit and opt-in

---

## Capability mapping required for validation (v1.6+)

Policy validation operates on declared **capability mapping** only.

If a course declares **no `capability_mapping`**, validation fails with a clear message indicating that there is nothing to validate.

Governance signals may still be computed and surfaced even when validation cannot proceed.

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

This mode is:

- read-only
- contract-stable
- safe for automation

Governance signals do **not** appear in explain output.

Explain mode resolves:
- which validation rules apply,
- how profiles are inherited,
- and how signal severities *would* be interpreted by the selected policy.

Actual governance signals (presence/absence facts) are:
- computed at build time,
- recorded in `manifest.json` under the `signals` key,
- and interpreted during validation — not during explain-only runs.

This separation ensures explain output remains contract-stable and reusable,
while governance facts remain tied to a specific build artefact.

---

## Final note

Policy files exist to make validation and governance interpretation:

- transparent
- adaptable
- defensible

The engine computes facts.
You decide what matters.
