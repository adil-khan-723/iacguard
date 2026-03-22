import pytest
from pathlib import Path
from iacguard.parser.plan_parser import load_plan, parse_changes
from iacguard.rules.rds001 import RDS001

FIXTURES = Path(__file__).parent / "fixtures"
rule = RDS001()

def test_rds001_fires_on_replace():
    data = load_plan(str(FIXTURES / "plan_rds_replace.json"))
    changes = parse_changes(data)
    findings = [rule.check(c, changes) for c in changes]
    findings = [f for f in findings if f]
    assert len(findings) == 1
    assert findings[0].rule_id == "RDS001"
    assert findings[0].severity.value == "CRITICAL"

def test_rds001_does_not_fire_on_update():
    data = load_plan(str(FIXTURES / "plan_rds_update.json"))
    changes = parse_changes(data)
    findings = [rule.check(c, changes) for c in changes]
    findings = [f for f in findings if f]
    assert len(findings) == 0

def test_rds001_does_not_fire_on_vpc():
    data = load_plan(str(FIXTURES / "plan_simple_create.json"))
    changes = parse_changes(data)
    findings = [rule.check(c, changes) for c in changes]
    findings = [f for f in findings if f]
    assert len(findings) == 0
