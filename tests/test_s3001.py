import pytest
from pathlib import Path
from iacguard.parser.plan_parser import load_plan, parse_changes
from iacguard.rules.s3001 import S3001

FIXTURES = Path(__file__).parent / "fixtures"
rule = S3001()

def test_s3001_fires_when_no_public_access_block():
    data = load_plan(str(FIXTURES / "plan_s3_no_block.json"))
    changes = parse_changes(data)
    findings = [rule.check(c, changes) for c in changes]
    findings = [f for f in findings if f]
    assert len(findings) == 1
    assert findings[0].rule_id == "S3001"
    assert findings[0].severity.value == "MEDIUM"

def test_s3001_does_not_fire_when_block_present():
    data = load_plan(str(FIXTURES / "plan_s3_with_block.json"))
    changes = parse_changes(data)
    findings = [rule.check(c, changes) for c in changes]
    findings = [f for f in findings if f]
    assert len(findings) == 0

def test_s3001_does_not_fire_on_rds():
    data = load_plan(str(FIXTURES / "plan_rds_replace.json"))
    changes = parse_changes(data)
    findings = [rule.check(c, changes) for c in changes]
    findings = [f for f in findings if f]
    assert len(findings) == 0
