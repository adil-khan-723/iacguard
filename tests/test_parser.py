import pytest
from pathlib import Path
from iacguard.parser.plan_parser import load_plan, parse_changes
from iacguard.rules.base import Action

FIXTURES = Path(__file__).parent / "fixtures"

def test_empty_plan_returns_no_changes():
    data = load_plan(str(FIXTURES / "plan_empty.json"))
    changes = parse_changes(data)
    assert changes == []

def test_simple_create_parsed_correctly():
    data = load_plan(str(FIXTURES / "plan_simple_create.json"))
    changes = parse_changes(data)
    assert len(changes) == 1
    assert changes[0].action == Action.CREATE
    assert changes[0].resource_type == "aws_vpc"

def test_rds_replace_action_normalized():
    data = load_plan(str(FIXTURES / "plan_rds_replace.json"))
    changes = parse_changes(data)
    assert len(changes) == 1
    assert changes[0].action == Action.REPLACE
    assert changes[0].replacing is True

def test_module_resource_parsed():
    data = load_plan(str(FIXTURES / "plan_module_resources.json"))
    changes = parse_changes(data)
    assert len(changes) == 1
    assert changes[0].module == "vpc"
    assert changes[0].address == "module.vpc.aws_security_group.bastion"
