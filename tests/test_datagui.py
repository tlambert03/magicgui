from typing import TYPE_CHECKING, Protocol

import attrs
import pydantic

from magicgui._datagui import GuiBuilder, build_gui_model
from magicgui._schema import GUIField, UiFieldInfo

if TYPE_CHECKING:

    class Foo(Protocol):
        a: int
        gui: GuiBuilder

        def __init__(self, **kwargs) -> None:
            ...


EXPECTED = {
    "a": GUIField(name="a", type_=int),
    "b": GUIField(name="b", type_=str, field_info=UiFieldInfo(description="the b")),
    "c": GUIField(
        name="c",
        type_=float,
        default=0.0,
        field_info=UiFieldInfo(default=0.0, widget_type="FloatSlider"),
    ),
}


def test_attrs_descriptor():
    @attrs.define
    class Foo:
        a: int
        b: str = attrs.field(metadata={"description": "the b"})
        c: float = attrs.field(default=0.0, metadata={"widget_type": "FloatSlider"})

    model = build_gui_model(Foo)
    assert model == EXPECTED
    for k, v in model.items():
        v.create()


def test_dataclass():
    from dataclasses import dataclass, field

    @dataclass
    class Foo:
        a: int
        b: str = field(metadata={"description": "the b"})
        c: float = field(default=0.0, metadata={"widget_type": "FloatSlider"})

    model = build_gui_model(Foo)
    assert model == EXPECTED
    for k, v in model.items():
        v.create()


def test_pydantic():
    class Foo(pydantic.BaseModel):
        a: int
        b: str = pydantic.Field(description="the b")
        c: float = pydantic.Field(0, ui_widget_type="FloatSlider")

    model = build_gui_model(Foo)
    assert model == EXPECTED
    for k, v in model.items():
        v.create()


def test_named_tuple():
    from typing import NamedTuple

    class Foo(NamedTuple):
        a: int
        b: str
        c: float = 0.0

    assert build_gui_model(Foo) == {
        "a": GUIField(name="a", type_=int),
        "b": GUIField(name="b", type_=str),
        "c": GUIField(name="c", type_=float, default=0.0),
    }


def test_typed_dict():
    from typing import TypedDict

    class Foo(TypedDict):
        a: int
        b: str
        c: float

    assert build_gui_model(Foo) == {
        "a": GUIField(name="a", type_=int),
        "b": GUIField(name="b", type_=str),
        "c": GUIField(name="c", type_=float),
    }


def test_function():
    def foo(a: int, b: str, c: float = 0.0):
        ...

    assert build_gui_model(foo) == {
        "a": GUIField(name="a", type_=int),
        "b": GUIField(name="b", type_=str),
        "c": GUIField(name="c", type_=float, default=0.0),
    }
