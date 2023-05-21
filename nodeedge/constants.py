from __future__ import annotations

import enum

from pydantic.fields import Undefined

__all__ = ["Undefined", "EnumOperand"]


class EnumOperand(enum.Enum):
    AND = "and"
    OR = "or"
