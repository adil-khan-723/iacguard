from typing import Optional
from iacguard.rules.base import RuleBase, ResourceChange, Finding, Severity, Action

RDS_TYPES = {"aws_db_instance", "aws_rds_cluster"}

class RDS001(RuleBase):
    rule_id  = "RDS001"
    severity = Severity.CRITICAL

    def check(self, change: ResourceChange, all_changes: list) -> Optional[Finding]:
        if change.resource_type not in RDS_TYPES:
            return None
        if change.action != Action.REPLACE and not change.replacing:
            return None
        return Finding(
            rule_id=self.rule_id,
            severity=self.severity,
            resource_address=change.address,
            resource_type=change.resource_type,
            resource_name=change.name,
            action=change.action,
            message=f"RDS instance '{change.name}' will be replaced — potential data loss and downtime.",
            recommendation=(
                "Verify this replacement is intentional. Ensure a snapshot exists before applying. "
                "Consider adding lifecycle { prevent_destroy = true } to guard production databases."
            ),
        )
