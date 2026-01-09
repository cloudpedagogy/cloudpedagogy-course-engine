from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


DEFAULT_PROFILE: Dict[str, Any] = {
    "rules": {
        # Require at least N domains declared in capability mapping
        "require_coverage": {"min_domains": 1},
        # Require at least N evidence items per domain (if domain is declared)
        "require_evidence": {"min_items_per_domain": 0},
        # Treat domains with zero coverage AND zero evidence as gaps
        "forbid_empty_domains": False,
        # Optional minimum coverage items per domain (if domain is declared)
        "min_coverage_items_per_domain": 0,
    }
}


@dataclass(frozen=True)
class ValidationIssue:
    rule: str
    severity: str  # "warning" | "error"
    domain: Optional[str] = None
    message: str = ""
    suggested_action: Optional[str] = None


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    strict: bool
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def load_profile(profile_path: Optional[str]) -> Dict[str, Any]:
    """
    Load a rule profile YAML. If none provided, returns DEFAULT_PROFILE.

    The profile is a simple ruleset used to validate the *defensibility* of
    declared capability mapping metadata, without assuming any specific framework.
    """
    if not profile_path:
        return DEFAULT_PROFILE

    p = Path(profile_path)
    if not p.exists():
        raise FileNotFoundError(f"Profile not found: {p}")

    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    # Shallow merge: user profile overrides defaults
    merged = dict(DEFAULT_PROFILE)
    merged_rules = dict(DEFAULT_PROFILE.get("rules", {}))
    merged_rules.update((data.get("rules") or {}))
    merged["rules"] = merged_rules
    return merged


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def validate_manifest(
    *,
    manifest: Dict[str, Any],
    report: Dict[str, Any],
    profile: Dict[str, Any],
    strict: bool = False,
) -> ValidationResult:
    """
    Validate manifest/report using a profile ruleset.

    Philosophy:
    - Framework-agnostic: rules never assume semantics of domains.
    - Non-strict mode: surfaces issues as warnings (does not fail the command).
    - Strict mode: treats issues as errors (non-zero exit via CLI).
    """
    issues: List[ValidationIssue] = []
    rules = profile.get("rules", {}) or {}

    cap = report.get("capability_mapping", {}) or {}
    domains = report.get("domains", {}) or {}
    declared = cap.get("domains_declared")
    if not isinstance(declared, int):
        declared = len(domains)

    # If no capability mapping is present at all:
    if manifest.get("capability_mapping") is None:
        # Treat as pass unless the profile explicitly requires mapping
        min_domains = _as_int((rules.get("require_coverage") or {}).get("min_domains", 0), 0)
        if min_domains > 0:
            issues.append(
                ValidationIssue(
                    rule="require_coverage",
                    severity="error" if strict else "warning",
                    message="No capability_mapping present in manifest, but the profile requires declared domains.",
                    suggested_action="Add capability_mapping to course.yml and rebuild.",
                )
            )

        # Make the ok logic explicit:
        if strict:
            ok_final = len([i for i in issues if i.severity == "error"]) == 0
        else:
            ok_final = True

        return ValidationResult(ok=ok_final, strict=strict, issues=issues)

    # --- Rule: require_coverage (min_domains) ---
    min_domains = _as_int((rules.get("require_coverage") or {}).get("min_domains", 1), 1)
    if declared < min_domains:
        issues.append(
            ValidationIssue(
                rule="require_coverage",
                severity="error" if strict else "warning",
                message=f"Only {declared} domains declared; minimum required is {min_domains}.",
                suggested_action="Declare additional domains in capability_mapping.domains, or lower min_domains in the profile.",
            )
        )

    # --- Rule: require_evidence (min_items_per_domain) ---
    min_evidence = _as_int((rules.get("require_evidence") or {}).get("min_items_per_domain", 0), 0)
    if min_evidence > 0:
        for key, d in domains.items():
            ev_count = _as_int(d.get("evidence_count", 0), 0)
            if ev_count < min_evidence:
                issues.append(
                    ValidationIssue(
                        rule="require_evidence",
                        severity="error" if strict else "warning",
                        domain=key,
                        message=f"Evidence items declared: {ev_count}; minimum required: {min_evidence}.",
                        suggested_action="Add evidence references for this domain, or lower the threshold in the profile.",
                    )
                )

    # --- Rule: min_coverage_items_per_domain ---
    min_cov = _as_int(rules.get("min_coverage_items_per_domain", 0), 0)
    if min_cov > 0:
        for key, d in domains.items():
            cov_count = _as_int(d.get("coverage_count", 0), 0)
            if cov_count < min_cov:
                issues.append(
                    ValidationIssue(
                        rule="min_coverage_items_per_domain",
                        severity="error" if strict else "warning",
                        domain=key,
                        message=f"Coverage items declared: {cov_count}; minimum required: {min_cov}.",
                        suggested_action="Add coverage references for this domain, or lower the threshold in the profile.",
                    )
                )

    # --- Rule: forbid_empty_domains ---
    forbid_empty = bool(rules.get("forbid_empty_domains", False))
    if forbid_empty:
        for key, d in domains.items():
            if bool(d.get("gap")):
                issues.append(
                    ValidationIssue(
                        rule="forbid_empty_domains",
                        severity="error" if strict else "warning",
                        domain=key,
                        message="Domain is declared but has no coverage and no evidence (gap).",
                        suggested_action="Either add coverage/evidence for this domain, or remove it from the mapping.",
                    )
                )

    # Determine ok:
    if strict:
        ok = len([i for i in issues if i.severity == "error"]) == 0
    else:
        ok = True

    return ValidationResult(ok=ok, strict=strict, issues=issues)


def validation_to_json(result: ValidationResult) -> str:
    payload = {
        "ok": result.ok,
        "strict": result.strict,
        "issues": [
            {
                "rule": i.rule,
                "severity": i.severity,
                "domain": i.domain,
                "message": i.message,
                "suggested_action": i.suggested_action,
            }
            for i in result.issues
        ],
        "summary": {
            "errors": len(result.errors),
            "warnings": len(result.warnings),
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def validation_to_text(result: ValidationResult) -> str:
    """
    Human-readable validation output intended for QA / governance workflows.

    Notes:
    - "Passed" means "no rule violations in strict mode" OR "non-strict reporting completed".
    - This does not grade quality; it checks whether declared mapping meets the profile's
      minimum defensibility rules (coverage/evidence completeness signals).
    """
    lines: List[str] = []

    if result.ok:
        if result.strict:
            lines.append("✔ Capability mapping validation passed")
        else:
            lines.append("✔ Capability mapping validation completed (non-strict)")
    else:
        lines.append("✖ Capability mapping validation failed")

    lines.append(f"Mode: {'STRICT' if result.strict else 'Non-strict'}")
    lines.append(f"Summary: {len(result.errors)} error(s) | {len(result.warnings)} warning(s)")
    lines.append("")

    if not result.issues:
        lines.append("No issues found.")
        return "\n".join(lines) + "\n"

    # Present errors first, then warnings (stable + easier to scan)
    def _sort_key(i: ValidationIssue) -> tuple[int, str, str]:
        sev_rank = 0 if i.severity == "error" else 1
        return (sev_rank, i.rule, i.domain or "")

    for issue in sorted(result.issues, key=_sort_key):
        tag = "ERROR" if issue.severity == "error" else "WARN"
        loc = f" ({issue.domain})" if issue.domain else ""
        lines.append(f"- {tag} [{issue.rule}]{loc}: {issue.message}")
        if issue.suggested_action:
            lines.append(f"  Suggested action: {issue.suggested_action}")

    lines.append("")
    return "\n".join(lines) + "\n"
