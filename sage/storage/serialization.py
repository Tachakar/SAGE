import operator
from decimal import Decimal
from typing import Callable, Literal, TypedDict

from sage.domain.conditions import Amount, And, Condition, Contains, Not, Or

OPERATOR_TO_NAME: dict[Callable[[Decimal, Decimal], bool], str] = {
    operator.gt: "gt",
    operator.lt: "lt",
    operator.eq: "eq",
    operator.ge: "ge",
    operator.le: "le",
    operator.ne: "ne",
}
NAME_TO_OPERATOR: dict[str, Callable[[Decimal, Decimal], bool]] = {
    name: op for op, name in OPERATOR_TO_NAME.items()
}


class ContainsDict(TypedDict):
    type: Literal["contains"]
    text: str


from typing import Callable, Literal, TypedDict, NotRequired

class AmountDict(TypedDict):
    type: Literal["amount"]
    op: str
    threshold: str
    absolute: NotRequired[bool]


class AndDict(TypedDict):
    type: Literal["and"]
    left: ConditionDict
    right: ConditionDict


class OrDict(TypedDict):
    type: Literal["or"]
    left: ConditionDict
    right: ConditionDict


class NotDict(TypedDict):
    type: Literal["not"]
    condition: ConditionDict


ConditionDict = ContainsDict | AmountDict | AndDict | OrDict | NotDict


def to_dict(condition: Condition) -> ConditionDict:
    match condition:
        case Contains(text=text):
            return {"type": "contains", "text": text}
        case Amount(op=op, threshold=threshold, absolute=abs_val):
            op_name = OPERATOR_TO_NAME.get(op)
            if op_name is None:
                raise ValueError(f"unsupported operator: {op!r}")
            return {
                "type": "amount",
                "op": op_name,
                "threshold": str(threshold),
                "absolute": abs_val,
            }
        case And(left=left, right=right):
            return {"type": "and", "left": to_dict(left), "right": to_dict(right)}
        case Or(left=left, right=right):
            return {"type": "or", "left": to_dict(left), "right": to_dict(right)}
        case Not(condition=inner):
            return {"type": "not", "condition": to_dict(inner)}
        case _:
            raise ValueError(f"unknown condition type: {type(condition)!r}")


def from_dict(data: ConditionDict) -> Condition:
    match data:
        case {"type": "contains", "text": text}:
            return Contains(text=text)

        case {"type": "amount", "op": op_name, "threshold": threshold, **kwargs}:
            op = NAME_TO_OPERATOR.get(op_name)
            if op is None:
                raise ValueError(f"unknown operator: {op_name!r}")
            return Amount(op=op, threshold=Decimal(threshold), absolute=kwargs.get("absolute", False))

        case {"type": "and", "left": left, "right": right}:
            return And(from_dict(left), from_dict(right))

        case {"type": "or", "left": left, "right": right}:
            return Or(from_dict(left), from_dict(right))

        case {"type": "not", "condition": inner}:
            return Not(from_dict(inner))

        case _:
            raise ValueError(f"unknown condition dict: {data!r}")
