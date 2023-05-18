from nodeedge.backends.base import FieldTypeMap

__all__ = ["type_map"]


type_map = FieldTypeMap(
    Str="str",
    Int16="int16",
    Int32="int32",
    Int64="int64",
    BigInt="bigint",
    Float32="float32",
    Float64="float64",
    Decimal="decimal",
    Date="cal::local_date",
    Time="cal::local_time",
    NaiveDateTime="cal::local_datetime",
    AwareDateTime="datetime",
    Duration="duration",
    RelativeDuration="cal::relative_duration",
    DateDuration="cal::date_duration",
    UUID1="uuid",
    UUID3="uuid",
    UUID4="uuid",
    UUID5="uuid",
    Bool="bool",
    Bytes="bytes",
    Array="array",
    Set="set",
    Tuple="tuple",
    NamedTuple="tuple",
    Link="uuid",
    MultiLink="array<uuid>",
    Json="json",
)
