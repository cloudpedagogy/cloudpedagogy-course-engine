from __future__ import annotations

import json
from typing import Any, Dict, List


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value]
    return [str(value)]


def build_capability_report(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a stable, machine-readable report from a manifest dict.

    Reads capability mapping metadata from manifest.json (v1.1+) and produces a
    summary suitable for human output or JSON output.
    """
    course = manifest.get("course", {}) or {}
    cap = manifest.get("capability_mapping", {}) or {}

    framework = cap.get("framework")
    version = cap.get("version")
    status = cap.get("status", "informational (not enforced)")

    domains: Dict[str, Any] = cap.get("domains", {}) or {}
    domains_declared = cap.get("domains_declared")
    if not isinstance(domains_declared, int):
        domains_declared = len(domains)

    per_domain: Dict[str, Any] = {}
    gaps: List[str] = []

    for key, dm in sorted(domains.items(), key=lambda kv: kv[0]):
        dm = dm or {}
        label = dm.get("label") or None

        coverage = _as_list(dm.get("coverage"))
        evidence = _as_list(dm.get("evidence"))

        coverage_count = len(coverage)
        evidence_count = len(evidence)

        gap = (coverage_count == 0 and evidence_count == 0)
        if gap:
            gaps.append(key)

        per_domain[key] = {
            "label": label,
            "coverage_count": coverage_count,
            "evidence_count": evidence_count,
            "gap": gap,
            "coverage": coverage,
            "evidence": evidence,
        }

    report: Dict[str, Any] = {
        "course": {
            "id": course.get("id"),
            "title": course.get("title"),
            "version": course.get("version"),
        },
        "capability_mapping": {
            "framework": framework,
            "version": version,
            "status": status,
            "domains_declared": domains_declared,
        },
        "domains": per_domain,
        "summary": {
            "gaps": len(gaps),
            "gap_domains": gaps,
        },
    }
    return report


def report_to_json(report: Dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False) + "\n"


def _format_table(rows: List[List[str]], headers: List[str]) -> str:
    # Compute column widths
    all_rows = [headers] + rows
    widths = [0] * len(headers)
    for r in all_rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(r: List[str]) -> str:
        return "| " + " | ".join(r[i].ljust(widths[i]) for i in range(len(headers))) + " |"

    sep = "|-" + "-|-".join("-" * widths[i] for i in range(len(headers))) + "-|"
    out = [fmt_row(headers), sep]
    out.extend(fmt_row(r) for r in rows)
    return "\n".join(out) + "\n"


def report_to_text(report: Dict[str, Any], *, verbose: bool = False) -> str:
    course = report.get("course", {}) or {}
    cap = report.get("capability_mapping", {}) or {}
    domains: Dict[str, Any] = report.get("domains", {}) or {}
    summary = report.get("summary", {}) or {}

    lines: List[str] = []
    lines.append("Capability Coverage Report (v1.2)")
    lines.append(f"Course: {course.get('title')} ({course.get('id')}) v{course.get('version')}")
    lines.append(f"Framework: {cap.get('framework')} ({cap.get('version')})")
    lines.append(f"Status: {cap.get('status')}")
    lines.append("")
    lines.append("Domains")
    lines.append(f"- Declared: {cap.get('domains_declared')}")
    lines.append("")

    rows: List[List[str]] = []
    for key in sorted(domains.keys()):
        d = domains[key] or {}
        label = d.get("label") or ""
        cov = str(d.get("coverage_count", 0))
        ev = str(d.get("evidence_count", 0))
        note = "GAP" if d.get("gap") else "OK"
        rows.append([key, label, cov, ev, note])

    headers = ["Domain key", "Label", "Coverage items", "Evidence items", "Notes"]
    lines.append(_format_table(rows, headers).rstrip())
    lines.append("")
    lines.append("Summary")
    lines.append(f"- Domains with gaps: {summary.get('gaps', 0)}")

    if verbose:
        lines.append("")
        lines.append("Details (verbose)")
        for key in sorted(domains.keys()):
            d = domains[key] or {}
            lines.append(f"{key}")
            lines.append(f"  coverage: {d.get('coverage', [])}")
            lines.append(f"  evidence: {d.get('evidence', [])}")
    else:
        lines.append("- Tip: run with --verbose to see declared coverage/evidence lists.")

    return "\n".join(lines) + "\n"
