import json
from iacguard.rules.base import Finding
from iacguard import __version__


def build_json(findings: list, summary: dict, skipped: list, plan_file: str, no_changes: bool = False) -> str:
    return json.dumps({
        "iacguard_version": __version__,
        "plan_file":        plan_file,
        "no_changes":       no_changes,
        "summary":          summary,
        "findings": [
            {
                "rule_id":          f.rule_id,
                "severity":         f.severity.value,
                "resource_address": f.resource_address,
                "resource_type":    f.resource_type,
                "resource_name":    f.resource_name,
                "action":           f.action.value,
                "message":          f.message,
                "recommendation":   f.recommendation,
                "blast_radius":     f.blast_radius,
            }
            for f in findings
        ],
        "errors":           [],
        "skipped_sections": skipped,
    }, indent=2)
