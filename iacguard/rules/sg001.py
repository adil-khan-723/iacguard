from typing import Optional
from iacguard.rules.base import RuleBase, ResourceChange, Finding, Severity, Action

SG_TYPES = {
    "aws_security_group",
    "aws_security_group_rule",
    "aws_vpc_security_group_ingress_rule",  # newer AWS provider resource type
}

OPEN_CIDRS_V4 = {"0.0.0.0/0"}
OPEN_CIDRS_V6 = {"::/0"}


def _port_in_range(port: int, from_port, to_port) -> bool:
    try:
        fp = int(from_port) if from_port is not None else 0
        tp = int(to_port)   if to_port   is not None else 65535
        return fp <= port <= tp
    except (ValueError, TypeError):
        return False


class SG001(RuleBase):
    rule_id  = "SG001"
    severity = Severity.CRITICAL

    def check(self, change: ResourceChange, all_changes: list) -> Optional[Finding]:
        if change.resource_type not in SG_TYPES:
            return None
        if change.action == Action.DESTROY:
            return None
        after = change.after
        if not after:
            return None

        # ── Type 1: aws_vpc_security_group_ingress_rule ──────────────────
        # Fields are top-level: from_port, to_port, cidr_ipv4, cidr_ipv6
        if change.resource_type == "aws_vpc_security_group_ingress_rule":
            from_port = after.get("from_port")
            to_port   = after.get("to_port")
            cidr_v4   = after.get("cidr_ipv4", "") or ""
            cidr_v6   = after.get("cidr_ipv6", "") or ""

            if _port_in_range(22, from_port, to_port):
                if cidr_v4 in OPEN_CIDRS_V4 or cidr_v6 in OPEN_CIDRS_V6:
                    return Finding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        resource_address=change.address,
                        resource_type=change.resource_type,
                        resource_name=change.name,
                        action=change.action,
                        message=f"Security group ingress rule '{change.name}' allows SSH (port 22) from the entire internet (0.0.0.0/0 or ::/0).",
                        recommendation=(
                            "Restrict SSH access to known internal CIDR ranges only. "
                            "Never expose port 22 to 0.0.0.0/0 in production."
                        ),
                    )
            return None

        # ── Type 2: aws_security_group_rule with type=ingress ────────────
        if change.resource_type == "aws_security_group_rule":
            if after.get("type") != "ingress":
                return None
            from_port = after.get("from_port")
            to_port   = after.get("to_port")
            cidrs     = set(after.get("cidr_blocks",      []) or [])
            ipv6cidrs = set(after.get("ipv6_cidr_blocks", []) or [])
            if _port_in_range(22, from_port, to_port):
                if cidrs & OPEN_CIDRS_V4 or ipv6cidrs & OPEN_CIDRS_V6:
                    return Finding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        resource_address=change.address,
                        resource_type=change.resource_type,
                        resource_name=change.name,
                        action=change.action,
                        message=f"Security group rule '{change.name}' allows SSH (port 22) from the entire internet (0.0.0.0/0 or ::/0).",
                        recommendation=(
                            "Restrict SSH access to known internal CIDR ranges only. "
                            "Never expose port 22 to 0.0.0.0/0 in production."
                        ),
                    )
            return None

        # ── Type 3: aws_security_group with inline ingress blocks ─────────
        ingress_rules = after.get("ingress", []) or []
        for rule in ingress_rules:
            if not isinstance(rule, dict):
                continue
            from_port = rule.get("from_port", 0)
            to_port   = rule.get("to_port",   0)
            cidrs     = set(rule.get("cidr_blocks",      []) or [])
            ipv6cidrs = set(rule.get("ipv6_cidr_blocks", []) or [])
            if _port_in_range(22, from_port, to_port):
                if cidrs & OPEN_CIDRS_V4 or ipv6cidrs & OPEN_CIDRS_V6:
                    return Finding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        resource_address=change.address,
                        resource_type=change.resource_type,
                        resource_name=change.name,
                        action=change.action,
                        message=f"Security group '{change.name}' allows SSH (port 22) from the entire internet (0.0.0.0/0 or ::/0).",
                        recommendation=(
                            "Restrict SSH access to known internal CIDR ranges only. "
                            "Never expose port 22 to 0.0.0.0/0 in production."
                        ),
                    )
        return None
