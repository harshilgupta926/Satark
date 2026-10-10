"""Deterministic, UI-neutral finding model for SATARK results."""

import re

_SEVERITY = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "clear": 0,
    "unknown": 0,
}
_NEGATORS = re.compile(
    r"(?:\bnot\s+considered|\bnot\s+classified\s+as|"
    r"\bnever\s+considered|\bno\s+(?:evidence|indication|signs?|indicators?)"
    r"(?:\s+of)?|\bwithout|\bnot|\bno|\bnever|\bisn['’]?t|\bis\s+not)"
    r"\s+(?:(?:a|an|the)\s+)?$"
)
_LABEL_NEGATION_AFTER = re.compile(
    r"^\s*(?:risk\s+)?(?:was\s+)?(?:not\s+(?:detected|present|confirmed|found)|"
    r"absent|ruled\s+out)\b"
)
_LABELS = (
    ("critical", re.compile(r"\b(?:critical|severe)\b")),
    ("high", re.compile(r"\bhigh\b")),
    ("medium", re.compile(r"\b(?:medium|moderate)\b")),
    ("low", re.compile(r"\blow\b")),
)


def _clause_prefix(text, position):
    """Return only the current clause, so old negation cannot mask new evidence."""
    prefix = text[max(0, position - 96):position]
    return re.split(r"[.!?;,\n]|—|–", prefix)[-1]


def _has_unnegated_label(text, pattern):
    """Match a severity label only when it is not directly negated."""
    for match in pattern.finditer(text):
        prefix = _clause_prefix(text, match.start())
        suffix = text[match.end():match.end() + 40]
        if not _NEGATORS.search(prefix) and not _LABEL_NEGATION_AFTER.search(suffix):
            return True
    return False


def finding_severity(value):
    """Map a displayed check value to a conservative severity.

    Absence of one severity (for example, no critical risk) does not establish
    that the item is clear. Only an unqualified negative result maps to clear.
    """
    text = str(value or "").strip().lower()
    if not text:
        return "unknown"

    # Only broad, unqualified negative statuses are clear. Severity-specific
    # negatives remain unknown unless another unnegated severity is present.
    broad_negative = re.compile(
        r"^(?:(?:status\s*:\s*)?clear|not detected|no signs? of (?:malware|phishing|fraud|"
        r"threats?|suspicious activity|indicators?)|no indicators?(?: of (?:malware|phishing|"
        r"fraud|threats?|suspicious activity))?|none detected|absent|false)[.! ]*$"
    )
    clauses = [part.strip() for part in re.split(r"[.!?;\n]|—|–", text) if part.strip()]
    if re.fullmatch(r"(?:status\s*:\s*)?clear[.! ]*", text):
        return "clear"
    if clauses and any(broad_negative.fullmatch(clause) for clause in clauses):
        if not any(_has_unnegated_label(text, pattern) for _, pattern in _LABELS):
            return "clear"

    saw_severity_label = False
    for severity, pattern in _LABELS:
        if pattern.search(text):
            saw_severity_label = True
            if _has_unnegated_label(text, pattern):
                return severity

    # Generic detection is only a fallback when no explicit severity is stated.
    if not saw_severity_label and _has_unnegated_label(
        text, re.compile(r"\b(?:detected|present|confirmed)\b")
    ):
        return "high"

    return "unknown"


def build_findings(result):
    """Normalize threat checks into stable finding objects for every UI/export."""
    checks = result.get("threat_analysis", {}) if isinstance(result, dict) else {}
    if not isinstance(checks, dict):
        checks = {}
    findings = []
    for name, value in checks.items():
        title = str(name)
        severity = finding_severity(value)
        findings.append({
            "id": re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "finding",
            "title": title,
            "status": str(value or "Needs review"),
            "severity": severity,
            "action": (
                "Verify independently before acting."
                if severity in {"critical", "high", "medium", "unknown"}
                else (
                    "This check did not report an indicator; that does not prove the item is safe."
                    if severity == "clear"
                    else "Review this low-severity signal in context."
                )
            ),
        })
    findings.sort(key=lambda item: _SEVERITY.get(item["severity"], 0), reverse=True)
    return findings
