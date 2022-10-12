import contextlib
import types
import weakref
from collections import OrderedDict, defaultdict, deque
from dataclasses import replace
from typing import TYPE_CHECKING, Any, Callable, ForwardRef, Type, TypeVar

from typing_extensions import Annotated, get_origin

from magicgui._type_resolution import resolve_single_type
from magicgui.types import Undefined
from magicgui.widgets._bases.widget import Widget

from ._schema import UiFieldInfo

if TYPE_CHECKING:
    from typing import Optional, Set, Tuple


class GUIField:
    """Represents a field in a GUI, perhaps in a form.

    This class combines `UiFieldInfo` (which holds information about a widget field)
    with an actual parameter `name` and `type_`.  It will generally be created for each
    field in a model, or each parameter in a function, using the  the `infer`
    classmethod, during GUIModel construction.
    """

    __slots__ = (
        "name",
        "type_",
        # "default",
        # "default_factory",
        # "required",
        "field_info",
        "_widget_class",
        "_widget_kwargs",
    )

    def __init__(
        self,
        *,
        name: str,
        type_: Type[Any],
        default: Any = Undefined,
        default_factory: Optional[Callable[[], Any]] = None,
        field_info: Optional[UiFieldInfo] = None,
    ) -> None:
        self.name = name
        self.type_ = type_

        if field_info is None:
            field_info = UiFieldInfo(default=default, default_factory=default_factory)
        elif not isinstance(field_info, UiFieldInfo):
            raise TypeError(f"field_info must be a UiFieldInfo, not {type(field_info)}")

        if default is not Undefined:
            field_info = replace(field_info, default=default)
        if default_factory is not None:
            field_info = replace(field_info, default_factory=default_factory)
        self.field_info = field_info
        self._widget_class: Optional[Type[Widget]] = None
        self._widget_kwargs: Optional[dict] = None

    def __repr__(self) -> str:
        """Return string representation."""
        name = self.__class__.__name__
        args = ((k, getattr(self, k)) for k in self.__slots__)
        _args = ", ".join(f"{k}={v}" for k, v in args)
        return f"{name}({_args})>"

    def get_default(self) -> Any:
        """Return the default value for this field."""
        return (
            _smart_deepcopy(self.field_info.default)
            if self.field_info.default_factory is None
            else self.field_info.default_factory()
        )

    @property
    def required(self) -> bool:
        return (
            self.field_info.default is Undefined
            and self.field_info.default_factory is None
        )

    @classmethod
    def infer(cls, *, name: str, value: Any, annotation: Any) -> "GUIField":
        """Infer a `GUIField` from a variable name, annotation, and value.

        ...as would be provided in either a function signature or a class definition

            def foo(name: annotation = value): ...

            class Foo:
                name: annotation = value

            class Bar:
                name: int = UiField(default=42, description="the answer")

            class Baz:
                name: Annotated[int, UiField(description="the answer")] = 42

        Parameters
        ----------
        name : str
            name of the variable
        value : Any
            default value of the variable, (might be an instance of `UiFieldInfo`)
        annotation : Any
            type annotation of the variable, (might be an instance of `typing.Annotated`
            with a UiFieldInfo as the annotation)
        """
        field_info, value = cls._unify_field_info(name, annotation, value)
        if value is Ellipsis:
            value = Undefined

        if annotation in (Undefined, None) and value is not Undefined:
            type_ = type(value)
        elif isinstance(annotation, (str, ForwardRef)):
            try:
                type_ = resolve_single_type(annotation)
            except (NameError, ImportError) as e:
                raise type(e)(f"Magicgui could not resolve {annotation}: {e}") from e
        else:
            type_ = annotation

        return cls(
            name=name,
            type_=type_,
            default=value,
            default_factory=field_info.default_factory,
            field_info=field_info,
        )

    @staticmethod
    def _unify_field_info(
        field_name: str, annotation: Any, value: Any
    ) -> Tuple[UiFieldInfo, Any]:
        """Unify UiFieldInfo from a variety of sources.

        Parameters
        ----------
        field_name : str
            The name of the field
        annotation : Any
            The type annotation of the field.  May be an instance of `typing.Annotated`
            with any of the recognized field types as the annotation metadata.
        value : Any
            The default value of the field, could be many things, including:
            - a literal value
            - an instance of `UiFieldInfo`
            - an instance of `dataclasses.Field`
            - an instance of `attrs.Attribute`
            - an instance of `pydantic.fields.FieldInfo`

        Returns
        -------
        Tuple[UiFieldInfo, Any]
            A tuple of the `UiFieldInfo` and the default value of the field.

        Raises
        ------
        ValueError
            If the annotation is an instance of `typing.Annotated` and the metadata
            contains more than one `UiFieldInfo` instance.
        ValueError
            If the annotation is an instance of `typing.Annotated` and the metadata
            contains a `UiFieldInfo` instance with a default value.
        ValueError
            If both the annotation and the value are instances of `UiFieldInfo`.
        """
        field_info: Optional[UiFieldInfo] = None
        if get_origin(annotation) is Annotated:
            field_info = UiFieldInfo.from_annotated(annotation, field_name=field_name)
            if (
                field_info is not None
                and value is not Undefined
                and value is not Ellipsis
            ):
                # check also `Required` because of `validate_arguments`
                # that sets `...` as default value
                field_info = replace(field_info, default=value)

        err = (
            "cannot specify `UiField`s in both Annotated "
            f"and value for {field_name!r}"
        )
        if isinstance(value, UiFieldInfo):
            if field_info is not None:
                raise ValueError(err)
            field_info = value

        elif field_info is None:
            field_info = UiFieldInfo(default=value)

        value = None if field_info.default_factory is not None else field_info.default
        return field_info, value

    def _update_widget_class(self) -> None:
        """Set private widget class attributes."""
        from dataclasses import asdict

        from magicgui.type_map import get_widget_class

        options = {
            k: v
            for k, v in asdict(self.field_info).items()
            if k not in ("default", "default_factory", "const", "extra")
            and v not in (None, Undefined)
        }

        self._widget_class, self._widget_kwargs = get_widget_class(
            value=self.get_default(),
            annotation=self.type_,
            options=options,
            is_result=False,
        )

    @property
    def widget_class(self):
        """Return the widget type for this field."""
        if getattr(self, "_widget_class", None) is None:
            self._update_widget_class()
        return self._widget_class

    @property
    def widget_kwargs(self):
        """Return the widget kwargs for this field."""
        if getattr(self, "_widget_kwargs", None) is None:
            self._update_widget_class()
        return self._widget_kwargs

    def create(self, value=Undefined, **kwargs):
        """Create a new widget instance for this field.

        Parameters
        ----------
        value : Any, optional
            Optional override to the default value of the widget.
        kwargs : dict, optional
            Additional keyword arguments to pass to the widget constructor.
        """
        kwargs = {
            **self.widget_kwargs,
            "name": self.name,
            "annotation": self.type_,
            **kwargs,
        }
        value = self.get_default() if value is Undefined else value
        if value is not Undefined:
            kwargs["value"] = value
        return self.widget_class(**kwargs)

    def __eq__(self, __o: object) -> bool:
        # sourcery skip: assign-if-exp
        if not isinstance(__o, GUIField):
            return NotImplemented
        return all(getattr(self, k) == getattr(__o, k) for k in self.__slots__)


# these are types that are returned unchanged by deepcopy
IMMUTABLE_NON_COLLECTIONS_TYPES: Set[Type] = {
    int,
    float,
    complex,
    str,
    bool,
    bytes,
    type,
    type(None),
    types.FunctionType,
    types.BuiltinFunctionType,
    types.LambdaType,
    weakref.ref,
    types.CodeType,
    types.ModuleType,
    type(NotImplemented),
    type(Ellipsis),
}

# these are types that if empty,
# might be copied with simple copy() instead of deepcopy()
BUILTIN_COLLECTIONS: Set[Type] = {
    list,
    set,
    tuple,
    frozenset,
    dict,
    OrderedDict,
    defaultdict,
    deque,
}

T = TypeVar("T")


def _smart_deepcopy(obj: T) -> T:
    """Return type as is for immutable built-in types.

    Use obj.copy() for built-in empty collections
    Use copy.deepcopy() for non-empty collections and unknown objects
    """
    from copy import deepcopy

    obj_type = type(obj)
    if obj_type in IMMUTABLE_NON_COLLECTIONS_TYPES:
        return obj  # fastest case: obj is immutable
    with contextlib.suppress(TypeError, ValueError, RuntimeError):
        if obj_type in BUILTIN_COLLECTIONS and not obj:
            # faster way for empty collections, no need to copy its members
            return obj if isinstance(obj, tuple) else obj.copy()  # type: ignore
    return deepcopy(obj)  # slowest way when we actually might need a deepcopy
