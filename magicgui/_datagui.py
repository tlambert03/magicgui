from __future__ import annotations

import dataclasses
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    Optional,
    Tuple,
    Type,
    TypeVar,
    cast,
)

from typing_extensions import TypeGuard

from ._schema import GUIField, UiFieldInfo
from .types import Undefined

if TYPE_CHECKING:
    from typing import Protocol

    import attrs
    import pydantic
    import pydantic.fields

    class HasAttrs(Protocol):
        __attrs_attrs__: Tuple[attrs.Attribute, ...]


_T = TypeVar("_T")


def datagui(cls: _T) -> _T:
    return cls


def create_widget(obj):
    ...


def is_dataclass(cls: type) -> bool:
    return dataclasses.is_dataclass(cls)


def get_pydantic_model(cls: type) -> Optional[pydantic.BaseModel]:
    try:
        import pydantic.fields
    except ImportError:
        return None

    fields = getattr(cls, "__fields__", None)
    if isinstance(fields, dict) and all(
        isinstance(f, pydantic.fields.ModelField) for f in fields.values()
    ):
        return cast("pydantic.BaseModel", cls)
    if hasattr(cls, "__pydantic_model__"):
        return get_pydantic_model(cls.__pydantic_model__)
    return None


def is_attrs_model(cls: type) -> TypeGuard[HasAttrs]:
    return getattr(cls, "__attrs_attrs__", None) is not None


def guifield_from_attrs(attr: attrs.Attribute) -> GUIField:
    import attrs

    default: Any = Undefined
    default_factory = None
    if isinstance(attr.default, attrs.Factory):  # type: ignore
        default_factory = attr.default.factory  # type: ignore
    elif attr.default is not attrs.NOTHING:
        default = attr.default

    return GUIField(
        name=attr.name,
        type_=attr.type,
        field_info=UiFieldInfo.from_dataclass_metadata(
            attr.metadata, default=default, default_factory=default_factory
        ),
    )


def guifield_from_dataclass(field: dataclasses.Field) -> GUIField:

    default = field.default if field.default is not dataclasses.MISSING else Undefined
    default_factory = (
        field.default_factory
        if field.default_factory is not dataclasses.MISSING
        else None
    )

    return GUIField(
        name=field.name,
        type_=field.type,
        field_info=UiFieldInfo.from_dataclass_metadata(
            field.metadata, default=default, default_factory=default_factory
        ),
    )


def guifield_from_pydantic(field: pydantic.fields.ModelField) -> GUIField:

    return GUIField(
        name=field.name,
        type_=field.outer_type_,
        field_info=UiFieldInfo.from_pydantic_field(field),
    )


def is_typed_named_tuple(cls: type) -> bool:
    return hasattr(cls, "__annotations__") and hasattr(cls, "_fields")


def guifield_from_pydantic(field: pydantic.fields.ModelField) -> GUIField:

    return GUIField(
        name=field.name,
        type_=field.outer_type_,
        field_info=UiFieldInfo.from_pydantic_field(field),
    )


def gui_fields_from_annotations(cls):
    # fallback for typed dict, named tuple, etc...

    annotations = getattr(cls, "__annotations__", None)
    if annotations is None:
        raise TypeError(
            f"Cannot create a GUI from object {type(cls)} without `__annotations__`"
        )

    # named tuples have _fields and _field_defaults
    field_defaults = getattr(cls, "_field_defaults", {})
    field_names = set(cls._fields) if hasattr(cls, "_fields") else set(annotations)

    return {
        name: GUIField(
            name=name,
            type_=annotations[name],
            default=field_defaults.get(name, Undefined),
        )
        for name in field_names
    }


def build_gui_model(cls: type) -> Dict[str, GUIField]:
    # TODO: cast instances to type?

    if is_attrs_model(cls):
        return {attr.name: guifield_from_attrs(attr) for attr in cls.__attrs_attrs__}
    if is_dataclass(cls):
        return {
            field.name: guifield_from_dataclass(field)
            for field in dataclasses.fields(cls)
        }
    if m := get_pydantic_model(cls):
        return {
            field.name: guifield_from_pydantic(field) for field in m.__fields__.values()
        }
    return gui_fields_from_annotations(cls)


class DataGuiMetaclass(type):
    def __new__(cls, name, bases, dct):
        return super().__new__(cls, name, bases, dct)


class DataGui(metaclass=DataGuiMetaclass):
    __slots__ = ()

    def gui(self):
        return self


from magicgui.widgets import Container


class DataContainer(Container, Generic[_T]):
    ...


class GuiBuilder:
    def __init__(self) -> None:
        self._gui_model = None
        self._name = ""

    def __set_name__(self, owner: type, name: str):
        self._name = name

    def __get__(self, instance: _T, owner: Type[_T]) -> Callable[[], DataContainer[_T]]:
        def _build():
            x = instance
            o = owner
            s = self
            return DataContainer()

        return _build
