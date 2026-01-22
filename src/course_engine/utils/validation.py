# src/course_engine/utils/validation.py

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from course_engine.model import Signal, SignalAction, SignalSeverity, SignalsPolicy


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
    },
    # v1.13+: default signals interpretation (non-blocking unless escalated)
    "signals": {
        "default_action": "info",
        "overrides": {},
        "ignore": [],
    },
}


_ALLOWED_SIGNAL_ACTIONS: set[str] = {"ignore", "info", "warn", "error"}
_ALLOWED_SIGNAL_SEVERITIES: set[str] = {"info", "warning"}


@dataclass(frozen=True)
class ValidationIssue:
    rule: str
    severity: str  # "warning" | "error"
    domain: Optional[str] = None
    message: str = ""
    suggested_action: Optional[str] = None


@dataclass(frozen=True)
class ResolvedSignal:
    """
    v1.13+: A computed Signal plus a policy-resolved action.

    - `signal` remains the computed fact object (stable contract)
    - `action` is policy interpretation (ignore/info/warn/error)
    - `action_source` helps explain precedence (ignore|override|default)
    """

    signal: Signal
    action: SignalAction
    action_source: str  # "ignore" | "override" | "default"

    def to_dict(self) -> dict:
        d = self.signal.to_dict()
        d["action"] = self.action
        d["action_source"] = self.action_source
        return d


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    strict: bool
    issues: List[ValidationIssue] = field(default_factory=list)

    # v1.13+: signals interpretation surfaced in validate outputs
    resolved_signals: List[ResolvedSignal] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def signal_action_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {"ignore": 0, "info": 0, "warn": 0, "error": 0}
        for rs in self.resolved_signals:
            counts[rs.action] = counts.get(rs.action, 0) + 1
        return counts

    @property
    def signal_errors(self) -> List[ResolvedSignal]:
        return [s for s in self.resolved_signals if s.action == "error"]

    @property
    def signal_warnings(self) -> List[ResolvedSignal]:
        return [s for s in self.resolved_signals if s.action == "warn"]


def load_profile(profile_path: Optional[str]) -> Dict[str, Any]:
    """
    Load a rule profile YAML. If none provided, returns DEFAULT_PROFILE.

    Legacy (v1.3) profile loader retained for backward compatibility.
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

    # v1.13+: signals policy block (optional)
    merged_signals = dict(DEFAULT_PROFILE.get("signals", {}) or {})
    merged_signals.update((data.get("signals") or {}))
    merged["signals"] = merged_signals

    return merged


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _signals_policy_from_profile(profile: Dict[str, Any]) -> SignalsPolicy:
    """
    Convert a resolved profile's `signals` dict (from utils.policy.resolve_profile)
    into a typed SignalsPolicy with safe defaults.
    """
    raw = profile.get("signals") or {}
    if not isinstance(raw, dict):
        raw = {}

    default_action = raw.get("default_action", "info")
    if not isinstance(default_action, str) or default_action not in _ALLOWED_SIGNAL_ACTIONS:
        default_action = "info"

    overrides = raw.get("overrides") or {}
    if not isinstance(overrides, dict):
        overrides = {}

    ignore = raw.get("ignore") or []
    if not isinstance(ignore, list):
        ignore = []

    overrides_norm: Dict[str, SignalAction] = {}
    for sid, action in overrides.items():
        if not isinstance(sid, str) or not sid.strip():
            continue
        if not isinstance(action, str) or action not in _ALLOWED_SIGNAL_ACTIONS:
            continue
        overrides_norm[sid.strip()] = action  # type: ignore[assignment]

    ignore_norm: List[str] = []
    for x in ignore:
        if isinstance(x, str) and x.strip():
            ignore_norm.append(x.strip())

    return SignalsPolicy(
        default_action=default_action,  # type: ignore[arg-type]
        overrides=overrides_norm,
        ignore=ignore_norm,
    )


def resolve_signal_actions(signals: List[Signal], policy: SignalsPolicy) -> List[ResolvedSignal]:
    """
    Resolve computed signals into policy actions.

    Precedence:
      1) ignore list
      2) overrides
      3) default_action
    """
    resolved: List[ResolvedSignal] = []

    for s in signals:
        if s.id in policy.ignore:
            resolved.append(ResolvedSignal(signal=s, action="ignore", action_source="ignore"))
            continue

        if s.id in policy.overrides:
            resolved.append(ResolvedSignal(signal=s, action=policy.overrides[s.id], action_source="override"))
            continue

        resolved.append(ResolvedSignal(signal=s, action=policy.default_action, action_source="default"))

    return resolved


def _parse_signals_from_manifest(manifest: Dict[str, Any]) -> List[Signal]:
    """
    Best-effort parsing of manifest['signals'] into typed Signal objects.
    Tolerant by design: invalid entries are skipped.
    """
    computed: List[Signal] = []
    raw_signals = manifest.get("signals")

    if not isinstance(raw_signals, list):
        return computed

    for item in raw_signals:
        if not isinstance(item, dict):
            continue

        sid = item.get("id")
        severity = item.get("severity")
        summary = item.get("summary")
        detail = item.get("detail")

        if not (isinstance(sid, str) and sid.strip()):
            continue
        if not (isinstance(severity, str) and severity in _ALLOWED_SIGNAL_SEVERITIES):
            continue
        if not (isinstance(summary, str) and isinstance(detail, str)):
            continue

        evidence_raw = item.get("evidence")
        evidence = [x for x in evidence_raw if isinstance(x, str)] if isinstance(evidence_raw, list) else []

        review_question = item.get("review_question") if isinstance(item.get("review_question"), str) else None
        source = item.get("source") if isinstance(item.get("source"), str) else None

        tags_raw = item.get("tags")
        tags = [x for x in tags_raw if isinstance(x, str)] if isinstance(tags_raw, list) else []

        sev: SignalSeverity = "info"  # type: ignore[assignment]
        if severity in {"info", "warning"}:
            sev = severity  # type: ignore[assignment]

        computed.append(
            Signal(
                id=sid.strip(),
                severity=sev,
                summary=summary,
                detail=detail,
                evidence=evidence,
                review_question=review_question,
                source=source,
                tags=tags,
            )
        )

    return computed


def _issues_from_resolved_signals(resolved: List[ResolvedSignal]) -> List[ValidationIssue]:
    """
    Convert resolved signals into ValidationIssue entries *only* for warn/error actions.

    NOTE: We keep signals separately in ValidationResult.resolved_signals.
    Adding them to issues is deliberate so existing validate output patterns
    continue to work (errors/warnings lists include signal escalations).
    """
    issues: List[ValidationIssue] = []

    for rs in resolved:
        if rs.action == "warn":
            issues.append(
                ValidationIssue(
                    rule=f"signal:{rs.signal.id}",
                    severity="warning",
                    message=f"{rs.signal.summary} ({rs.signal.id})",
                    suggested_action=rs.signal.review_question
                    or "Review this signal and update course metadata if appropriate.",
                )
            )
        elif rs.action == "error":
            issues.append(
                ValidationIssue(
                    rule=f"signal:{rs.signal.id}",
                    severity="error",
                    message=f"{rs.signal.summary} ({rs.signal.id})",
                    suggested_action=rs.signal.review_question
                    or "Resolve this signal or adjust policy to avoid gating.",
                )
            )

    return issues


def _ok_from_issues(issues: List[ValidationIssue]) -> bool:
    return all(i.severity != "error" for i in issues)


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
    - Non-strict mode: surfaces rule violations as warnings (does not fail).
    - Strict mode: surfaces rule violations as errors (CLI can fail).

    v1.13+:
    - Governance signals may be present in the manifest and are interpreted
      by policy (ignore/info/warn/error) without changing signal computation.
    - If any signal resolves to action=error, validation produces errors and ok=False
      (policy explicitly requested gating behaviour).
    """
    issues: List[ValidationIssue] = []
    rules = profile.get("rules", {}) or {}

    # -------------------------
    # v1.13+: signals resolution
    # -------------------------
    computed_signals = _parse_signals_from_manifest(manifest)
    signals_policy = _signals_policy_from_profile(profile)
    resolved_signals = resolve_signal_actions(computed_signals, signals_policy)

    # Convert warn/error signals into issues
    issues.extend(_issues_from_resolved_signals(resolved_signals))

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

        ok_final = _ok_from_issues(issues)
        return ValidationResult(ok=ok_final, strict=strict, issues=issues, resolved_signals=resolved_signals)

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

    ok = _ok_from_issues(issues)

    return ValidationResult(ok=ok, strict=strict, issues=issues, resolved_signals=resolved_signals)


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
        # v1.13+: signal contract
        "resolved_signals": [s.to_dict() for s in result.resolved_signals],
        "summary": {
            "errors": len(result.errors),
            "warnings": len(result.warnings),
            "signal_actions": result.signal_action_counts,
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def validation_to_text(result: ValidationResult) -> str:
    """
    Human-readable validation output intended for QA / governance workflows.

    v1.13+:
    - Signals are included via issues (warn/error) and summarised explicitly.
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

    if result.resolved_signals:
        c = result.signal_action_counts
        lines.append(
            f"Signals: {c.get('error', 0)} error | {c.get('warn', 0)} warn | {c.get('info', 0)} info | {c.get('ignore', 0)} ignored"
        )

    lines.append("")

    if not result.issues:
        lines.append("No issues found.")
        return "\n".join(lines) + "\n"

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
