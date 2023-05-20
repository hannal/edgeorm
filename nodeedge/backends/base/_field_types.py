from dataclasses import dataclass
from typing import Callable, Union, Literal, TypeAlias


__all__ = ["FieldTypeMap"]


LinkIdFieldType: TypeAlias = Literal["uuid"]
MultiLinkIdFieldType: TypeAlias = Literal["array<uuid>"]


@dataclass(frozen=True, kw_only=True)
class FieldTypeMap:
    Bool: str
    Str: str
    Int16: str
    Int32: str
    Int64: str
    BigInt: str
    Float32: str
    Float64: str
    Decimal: str
    Link: Union[LinkIdFieldType, Callable]
    MultiLink: Union[MultiLinkIdFieldType, Callable]
    Date: str
    Time: str
    NaiveDateTime: str
    AwareDateTime: str
    Duration: str
    RelativeDuration: str
    DateDuration: str
    UUID1: str
    UUID3: str
    UUID4: str
    UUID5: str
    Bytes: str
    Array: str
    Set: str
    Tuple: str
    NamedTuple: str
    Json: str
