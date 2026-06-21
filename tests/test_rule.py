import dataclasses

import pytest

from sage.domain.conditions import Contains
from sage.domain.rule import Rule


def test_rule_sorts_by_priority_ascending() -> None:
    low = Rule("low", Contains("a"), "A", priority=10)
    high = Rule("high", Contains("a"), "A", priority=1)
    assert sorted([low, high], key=lambda r: r.priority) == [high, low]


def test_rule_handles_negative_priority() -> None:
    normal = Rule("normal", Contains("a"), "A", priority=0)
    urgent = Rule("urgent", Contains("a"), "A", priority=-5)
    assert sorted([normal, urgent], key=lambda r: r.priority) == [urgent, normal]


def test_rule_equality_is_by_value() -> None:
    a = Rule("name", Contains("a"), "Category", priority=1)
    b = Rule("name", Contains("a"), "Category", priority=1)
    assert a == b


def test_rule_is_immutable() -> None:
    rule = Rule("name", Contains("a"), "Category", priority=1)
    with __import__("pytest").raises(dataclasses.FrozenInstanceError):
        rule.priority = 5
