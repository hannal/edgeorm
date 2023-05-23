from __future__ import annotations


from nodeedge.types import enum


__all__ = ["EnumLookupExpression", "EnumOperand"]


class EnumLookupExpression(enum.Flag):
    NOT = enum.auto()
    EQUAL = enum.auto()
    IN = enum.auto()
    GE = enum.auto()
    GT = enum.auto()
    LE = enum.auto()
    LT = enum.auto()
    EXISTS = enum.auto()
    LIKE = enum.auto()
    ILIKE = enum.auto()

    @classmethod
    def allowed_negate_expr(cls):
        return (
            EnumLookupExpression.EQUAL,
            EnumLookupExpression.IN,
            EnumLookupExpression.EXISTS,
            EnumLookupExpression.LIKE,
            EnumLookupExpression.ILIKE,
        )

    @property
    def is_negate_expr(self):
        return self & self.NOT == self.NOT

    @property
    def is_func_lookup(self):
        return self & self.EXISTS == self.EXISTS

    @property
    def is_in_lookup(self):
        return self & self.IN == self.IN

    @property
    def is_equal_lookup(self):
        return self & self.EQUAL == self.EQUAL

    def can_jsonable_as_value(self) -> bool:
        return self.is_equal_lookup or self.is_in_lookup

    @property
    def can_subquery_as_value(self):
        return self.is_equal_lookup or self.is_in_lookup


class EnumOperand(enum.Enum):
    AND = "and"
    OR = "or"
