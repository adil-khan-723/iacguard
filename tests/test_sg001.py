import pytest
from pathlib import Path
from iacguard.parser.plan_parser import load_plan, parse_changes
from iacguard.rules.sg001 import SG001

FIXTURES = Path(__file__).parent / "fixtures"
rule = SG001()

def test_sg001_fires_on_open_ssh():
    data = load_plan(str(FIXTURES / "plan_sg_open.json"))
    changes = parse_changes(data)
    findings = [rule.check(c, changes) for c in changes]
    findings = [f for f in findings if f]
    assert len(findings) == 1
    assert findings[0].rule_id == "SG001"
    assert findings[0].severity.value == "CRITICAL"

def test_sg001_does_not_fire_on_restricted_sg():
    data = load_plan(str(FIXTURES / "plan_sg_restricted.json"))
    changes = parse_changes(data)
    findings = [rule.check(c, changes) for c in changes]
    findings = [f for f in findings if f]
    assert len(findings) == 0

def test_sg001_fires_on_module_resource():
    data = load_plan(str(FIXTURES / "plan_module_resources.json"))
    changes = parse_changes(data)
    findings = [rule.check(c, changes) for c in changes]
    findings = [f for f in findings if f]
    assert len(findings) == 1
    assert "module.vpc" in findings[0].resource_address

def test_sg001_fires_on_vpc_ingress_rule_type():
    data = load_plan(str(FIXTURES / "plan_sg_vpc_ingress_rule.json"))
    changes = parse_changes(data)
    findings = [rule.check(c, changes) for c in changes]
    findings = [f for f in findings if f]
    assert len(findings) == 1
    assert findings[0].rule_id == "SG001"
    assert findings[0].severity.value == "CRITICAL"
    assert findings[0].resource_name == "sg_inbound_ssh"

def test_sg001_does_not_fire_on_http_vpc_ingress_rule():
    data = load_plan(str(FIXTURES / "plan_sg_vpc_ingress_rule.json"))
    changes = parse_changes(data)
    http_changes = [c for c in changes if c.name == "sg_inbound_http"]
    findings = [rule.check(c, changes) for c in http_changes]
    findings = [f for f in findings if f]
    assert len(findings) == 0
