from iacguard.rules.base import ResourceChange, Finding, Severity
from iacguard.rules.rds001 import RDS001
from iacguard.rules.sg001  import SG001
from iacguard.rules.s3001  import S3001

RULES = [RDS001(), SG001(), S3001()]

SEVERITY_ORDER = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]


def run_rules(changes: list) -> list:
    findings = []
    for change in changes:
        for rule in RULES:
            try:
                result = rule.check(change, changes)
                if result:
                    findings.append(result)
            except Exception as e:
                import sys
                print(f"[iacguard] WARNING: Rule {rule.rule_id} crashed on {change.address}: {e}", file=sys.stderr)
    findings.sort(key=lambda f: SEVERITY_ORDER.index(f.severity))
    return findings


def summarize(findings: list, changes: list) -> dict:
    counts = {s.value: 0 for s in Severity}
    for f in findings:
        counts[f.severity.value] += 1
    return {
        "critical":           counts["CRITICAL"],
        "high":               counts["HIGH"],
        "medium":             counts["MEDIUM"],
        "low":                counts["LOW"],
        "resources_analyzed": len(changes),
        "changes":            len(changes),
        "skipped":            0,
    }
