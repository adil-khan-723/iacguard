from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from abc import ABC, abstractmethod


class Action(Enum):
    CREATE  = "CREATE"
    UPDATE  = "UPDATE"
    DESTROY = "DESTROY"
    REPLACE = "REPLACE"
    NO_OP   = "NO_OP"
    READ    = "READ"


class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"
    LOW      = "LOW"

    def __lt__(self, other):
        order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]
        return order.index(self) < order.index(other)


@dataclass
class ResourceChange:
    address:       str
    module:        Optional[str]
    resource_type: str
    name:          str
    action:        Action
    before:        Optional[dict]
    after:         Optional[dict]
    after_unknown: dict
    replacing:     bool


@dataclass
class Finding:
    rule_id:          str
    severity:         Severity
    resource_address: str
    resource_type:    str
    resource_name:    str
    action:           Action
    message:          str
    recommendation:   str
    blast_radius:     list = field(default_factory=list)


class RuleBase(ABC):
    @abstractmethod
    def check(self, change: ResourceChange, all_changes: list) -> Optional[Finding]:
        """Return a Finding if the rule fires, None otherwise."""
        ...
