import enum
from typing import Any


class JsonableEnum:
    def as_jsonable_value(self) -> Any:
        return self.__getattribute__("name")


class FindableEnum:
    @classmethod
    def find_member(cls, member: Any) -> enum.Enum:
        assert issubclass(cls, enum.Enum)
        members = cls.__members__

        if isinstance(member, enum.Enum):
            member = member.name
        if isinstance(member, str):
            return cls[member]
        elif isinstance(member, int):
            for _member in members.values():
                if _member.value == member:
                    return _member
            raise KeyError(member)

        raise TypeError(f"invalid member type: {type(member)}")
