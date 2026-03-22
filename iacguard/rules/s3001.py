from typing import Optional
from iacguard.rules.base import RuleBase, ResourceChange, Finding, Severity, Action

class S3001(RuleBase):
    rule_id  = "S3001"
    severity = Severity.MEDIUM

    def check(self, change: ResourceChange, all_changes: list) -> Optional[Finding]:
        if change.resource_type != "aws_s3_bucket":
            return None
        if change.action != Action.CREATE:
            return None

        bucket_name = change.name

        # check if there is an aws_s3_bucket_public_access_block in the plan for this bucket
        for c in all_changes:
            if c.resource_type != "aws_s3_bucket_public_access_block":
                continue
            if c.action == Action.DESTROY:
                continue
            after = c.after or {}
            # matches if bucket field references this bucket name or address
            bucket_ref = after.get("bucket", "") or ""
            if bucket_name in bucket_ref or bucket_name == c.name:
                return None

        return Finding(
            rule_id=self.rule_id,
            severity=self.severity,
            resource_address=change.address,
            resource_type=change.resource_type,
            resource_name=change.name,
            action=change.action,
            message=f"S3 bucket '{change.name}' has no explicit block_public_access configuration.",
            recommendation=(
                "Add an aws_s3_bucket_public_access_block resource for this bucket. "
                "Note: account-level Block Public Access settings may still protect this bucket, "
                "but explicit configuration is always recommended."
            ),
        )
