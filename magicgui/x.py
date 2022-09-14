from typing import Iterator, Annotated
import attrs
import pydantic
from dataclasses import dataclass, field
from magicgui._schema import GUIField


@dataclass
class dFoo:
    a: int = field(
        default=1, metadata={"widget_type": "Slider", "multiple_of": 2, "minimum": 2}
    )
    b: str = "hiel"
    c: float = 1.2


@attrs.define
class aFoo:
    a: int = attrs.field(
        metadata={"widget_type": "Slider", "multiple_of": 2, "minimum": 2}
    )
    b: str = "hiel"
    c: float = 1.2


class pFoo(pydantic.BaseModel):
    a: int = pydantic.Field(ge=0, le=10, multiple_of=2)
    b: str = "hiel"
    c: float = 1.2


@pydantic.dataclasses.dataclass
class pdFoo:
    a: int
    b: str = "hiel"
    c: float = 1.2


def fields(obj) -> Iterator[GUIField]:
    # pydantic dataclass
    if hasattr(obj, "__pydantic_model__"):
        obj = obj.__pydantic_model__

    # attrs class
    if hasattr(obj, "__attrs_attrs__"):
        yield from map(GUIField.from_attrs_attribute, obj.__attrs_attrs__)
    # pydantic
    elif hasattr(obj, "__fields__") and hasattr(obj, "__validators__"):
        yield from map(GUIField.from_pydantic_field, obj.__fields__.values())
    # python dataclass
    elif hasattr(obj, "__dataclass_fields__"):
        yield from map(GUIField.from_dataclass_field, obj.__dataclass_fields__.values())
    elif isinstance(obj, dict):
        yield from map(GUIField.from_dict, obj.items())


def go():
    # for c in [dFoo, aFoo, pFoo, pdFoo, dFoo(a=1), aFoo(a=2), pFoo(a=2), pdFoo(a=2)]:
    for c in [aFoo]:
        from rich import print

        for f in fields(c):
            print(f)


# def being_used_as_decorator(context=6):
#     import inspect

#     calling_frame = inspect.currentframe().f_back
#     fname = calling_frame.f_code.co_name
#     info = inspect.getframeinfo(calling_frame.f_back, context=context)
#     return any(x.startswith(f"@{fname}") for x in info.code_context[: context // 2])


# def deco(f):
#     print(being_used_as_decorator())
#     return f
