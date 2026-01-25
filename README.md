# CloudPedagogy Course Engine (v1.21.0)

A Python-first, Quarto-backed **course compiler** that generates
consistent, auditable learning artefacts from a single `course.yml`
source of truth.

The Course Engine is designed for **reproducible course production** in
educator, learning design, quality assurance (QA), and academic
governance contexts.

It prioritises **determinism, transparency, and explainability** over
automation or enforcement.

------------------------------------------------------------------------

## What it does

-   Treats `course.yml` as the **single source of truth**
-   Validates course structure and metadata
-   Compiles publishable artefacts via templates
-   Produces **auditable, reproducible outputs** with a machine-readable
    `manifest.json`
-   Records declared **design intent** (rationale, AI positioning,
    governance context) and surfaces it in `manifest.json` and
    `course-engine explain`
-   Defaults to **non-destructive builds** (explicit `--overwrite`
    required)
-   Supports optional **capability mapping metadata** for governance and
    audit
-   Supports **external lesson source files with provenance tracking**
-   Supports **explain-only policy resolution** (read-only) for CI,
    dashboards, and QA workflows via\
    `course-engine validate --policy … --explain --json`\
    (see `docs/explainability-json-contract.md`)

------------------------------------------------------------------------

## Why this matters

Universities increasingly need to demonstrate **how** and **why**
courses are designed --- particularly where AI, capability frameworks,
or external expectations are involved --- without turning curriculum
design into a compliance exercise.

The **CloudPedagogy Course Engine** provides a practical middle ground:
it makes **design intent**, **structural decisions**, and **declared
alignments** explicit, inspectable, and reproducible, while deliberately
avoiding automated judgement or enforcement.

This supports **quality assurance, audit, and review conversations**
with clearer evidence, reduced ambiguity, and lower operational risk ---
**without constraining academic autonomy or pedagogical practice**.

------------------------------------------------------------------------

## Explain modes (source vs artefact)

`course-engine explain` operates in two complementary modes:

-   **Source mode** (point at `course.yml`)\
    Reports declarations exactly as authored in YAML. This mode is
    intentionally strict and pre-normalisation.

-   **Artefact mode** (point at a built output directory containing
    `manifest.json`)\
    Reports the canonical, normalised facts used for QA, audit,
    automation, and governance workflows.

Both modes are deterministic and non-evaluative, but artefact explain
should be treated as the authoritative record for downstream processes.

------------------------------------------------------------------------

## What's new in v1.21

v1.21 introduces **deterministic governance snapshots** via
`course-engine snapshot`.

A snapshot is a **minimal, diff-friendly, facts-only** record of course
state intended for:

-   change tracking (git diffs / CI),
-   QA and governance review,
-   reproducible auditing without re-running builds.

### Highlights

-   **New `snapshot` command**

    ``` bash
    course-engine snapshot path/to/course.yml --format json
    course-engine snapshot dist/<course-id> --format json
    ```

    -   Automatically resolves:
        -   a **source snapshot** from `course.yml`
        -   an **artefact snapshot** from
            `dist/<course-id>/manifest.json`

-   **Contract-stable, facts-only output**

    -   No evaluation, scoring, or policy execution
    -   Designed for automation and review workflows

-   **Determinism**

    -   Output is stable across runs\
        (aside from the explicitly declared `generated_at_utc`
        timestamp)

------------------------------------------------------------------------

## What's new in v1.20

v1.20 introduces a **formal, CI-grade preflight contract** for
`course-engine check`, completing the separation between:

-   *environment inspection* (facts),
-   *requirement declaration* (intent), and
-   *exit semantics* (decision).

### Highlights

-   **Deterministic preflight exit codes**
-   **Explicit requirement declaration**
-   **Strict and targeted requirement modes**
-   **Stable, machine-readable JSON contract**
-   **Backwards compatibility preserved**

(Default behaviour remains informational and non-blocking.)

------------------------------------------------------------------------

## CLI commands

-   **init** -- Scaffold a new course project
-   **build** -- Compile `course.yml` into an output package
-   **render** -- Render outputs with Quarto
-   **explain** -- Explain course structure, provenance, and governance
    signals
-   **report** -- Generate capability coverage reports
-   **validate** -- Validate or explain policy resolution
-   **clean** -- Remove generated artefacts safely
-   **check** -- Run dependency preflight checks (informational or
    CI-grade)
-   **snapshot** -- Emit deterministic governance snapshots

> Note: Policy handling is accessed via\
> `course-engine validate --policy … --explain --json`\
> There is no separate `course-engine policy` subcommand.

------------------------------------------------------------------------

## Capability mapping

Course Engine supports optional, **informational capability mapping
metadata**.

Capability mapping:

-   is optional
-   is never enforced at build time
-   is intended for governance, QA, and audit contexts

------------------------------------------------------------------------

## Design intent

An optional `design_intent` block allows authors to declare:

-   rationale behind design choices,
-   AI positioning and constraints,
-   relevant frameworks or policy contexts,
-   review cadence and evolution expectations.

Design intent is:

-   informational only
-   recorded in `manifest.json`
-   surfaced via `course-engine explain`

------------------------------------------------------------------------

## Versioning and evolution

The Course Engine evolves conservatively through minor releases,
prioritising:

-   backward compatibility
-   non-destructive defaults
-   governance safety

Detailed history is maintained in `CHANGELOG.md`.

------------------------------------------------------------------------

## Licensing

-   Course Engine code: **MIT License**
-   CloudPedagogy frameworks and models: licensed separately

------------------------------------------------------------------------

## Disclaimer

The CloudPedagogy Course Engine is a technical tool for compiling,
inspecting, and explaining course artefacts.

It records declared intent and structure for transparency, but does
**not** evaluate pedagogical quality or replace institutional governance
processes.
