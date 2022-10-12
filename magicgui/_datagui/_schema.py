import sys
import warnings
from copy import copy
from dataclasses import asdict, dataclass, field, fields
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Set,
    Union,
)

from typing_extensions import Literal, get_args

from magicgui.types import JsonStringFormats, Undefined, WidgetRef
from magicgui.widgets._bases.value_widget import ValueWidget

if TYPE_CHECKING:
    from annotated_types import BaseMetadata
    from pydantic.fields import FieldInfo as PydanticFieldInfo


@dataclass(frozen=True)
class ValueConstraints:
    """Constraints that can be put on any widget that holds a value."""

    default: Any = field(
        default=Undefined,
        metadata=dict(description="The default value of the field", aliases=["value"]),
    )
    default_factory: Optional[Callable[[], Any]] = field(
        default=None,
        metadata=dict(
            description="A callable that returns the default value of the field."
        ),
    )
    const: bool = field(
        default=False,
        metadata=dict(
            description="If True, this argument must be the same as the field's "
            "default value if present"
        ),
    )
    enum: Optional[List[Any]] = field(
        default=None,
        metadata=dict(
            description="A list of valid values for this field. Prefer a python enum.",
            aliases=["choices"],
        ),
    )

    # ### From magicgui ###
    bind: Union[Callable[[ValueWidget], Any], Any, None] = field(
        default=None,
        metadata=dict(
            description="A value or callable bind to the value of the field. If a "
            "callable, it will be called (with one argument, the ValueWidget), whenever"
            " the value of the field is requested."
        ),
    )
    # nullable: bool  # for stuff like combo boxes and value widgets

    # ### From JSON Schema ###
    # any_of

    # ### From Pydantic ###
    # allow_mutation


@dataclass(frozen=True)
class FieldInfo:
    """Dataclass-like info associated with a field."""

    title: Optional[str] = field(
        default=None,
        metadata=dict(
            description="The title of the field. (If not provided the name of the "
            "field variable is used.)",
            aliases=["label", "text"],
        ),
    )
    description: Optional[str] = field(
        default=None,
        metadata=dict(
            description="The description of the field",
            aliases=["tooltip"],
        ),
    )
    # TODO: can we remove this?
    button_text: Optional[str] = field(
        default=None,
        metadata=dict(description="The text of a button", aliases=["text"]),
    )
    # mode: str | FileDialogMode


@dataclass(frozen=True)
class NumericContraints:
    """Contraints that can be put on a numeric value."""

    multiple_of: Optional[float] = field(
        default=None,
        metadata=dict(
            description="Restrict number to a multiple of a given number. "
            "May be any positive number.",
            aliases=["multipleOf", "step"],
        ),
    )
    minimum: Optional[float] = field(
        default=None,
        metadata=dict(description="(Inclusive) Minimum value", aliases=["min", "ge"]),
    )
    maximum: Optional[float] = field(
        default=None,
        metadata=dict(description="(Inclusive) Maximum value", aliases=["max", "le"]),
    )
    # note, in JSON schema, these used to be bools, in which
    # case the implication is that the value for min/max should
    # be used here, and removed in min/max.
    exclusive_minimum: Optional[float] = field(
        default=None,
        metadata=dict(
            description="Exclusive minimum value",
            aliases=["exclusiveMinimum", "gt"],
        ),
    )
    exclusive_maximum: Optional[float] = field(
        default=None,
        metadata=dict(
            description="Exclusive maximum value",
            aliases=["exclusiveMaximum", "lt"],
        ),
    )

    # not in json schema, for Decimal types
    max_digits: Optional[int] = field(
        default=None,
        metadata=dict(
            description="Maximum number of digits within the decimal. It does not "
            "include a zero before the decimal point or trailing decimal zeroes."
        ),
    )
    decimal_places: Optional[int] = field(
        default=None,
        metadata=dict(
            descripion="Maximum number of decimal places within the decimal. It does "
            "not include trailing decimal zeroes."
        ),
    )

    # SLIDER WIDGET STUFF
    # readout
    # tracking


@dataclass(frozen=True)
class StringContraints:
    """Constraints that can be put on a string value."""

    min_length: Optional[int] = field(
        default=None,
        metadata=dict(
            description="Minimum string length. Must be a non-negative number",
            aliases=["minLength"],
        ),
    )
    max_length: Optional[int] = field(
        default=None,
        metadata=dict(
            description="Maximum string length. Must be a non-negative number",
            aliases=["maxLength"],
        ),
    )
    pattern: Optional[str] = field(
        default=None,
        metadata=dict(
            description="Regular expression pattern. For file dialogs, this is used "
            "to filter the files shown, and will be interpreted as a glob pattern. "
            "For other strings, it is a regex pattern.",
            aliases=["regex", "filter"],
        ),
    )
    format: Optional[JsonStringFormats] = field(
        default=None,
        metadata=dict(
            description="Allows for basic semantic identification of certain kinds of "
            "string values that are commonly used. This is primarily used for "
            "JSON Schema conversion; python types should be preferred when possible.",
        ),
    )


@dataclass(frozen=True)
class ArrayContraints:
    """Contraints that can be put on a list or array value."""

    min_items: Optional[int] = field(
        default=None,
        metadata=dict(
            description="Minimum length of the list. Must be a non-negative number.",
            aliases=["minItems", "min_inclusive"],
        ),
    )
    max_items: Optional[int] = field(
        default=None,
        metadata=dict(
            description="Maximum length of the list. Must be a non-negative number.",
            aliases=["maxItems", "max_inclusive"],
        ),
    )
    unique_items: Optional[bool] = field(
        default=None,
        metadata=dict(
            description="Declares that each of the items in an array must be unique. "
            "In python, this is best implemented as a set.",
            aliases=["uniqueItems"],
        ),
    )


@dataclass(frozen=True)
class WidgetConstraints:
    """Constraints on the widget itself."""

    widget_type: Optional[WidgetRef] = field(
        default=None,
        metadata=dict(
            description="(Override) the type of widget to use for this field.",
        ),
    )
    visible: bool = field(
        default=True,
        metadata=dict(description="Whether the widget is visible"),
    )
    enabled: bool = field(
        default=True,
        metadata=dict(description="Whether the widget is enabled"),
    )
    orientation: Optional[Literal["horizontal", "vertical"]] = field(
        default=None,
        metadata=dict(description="Orientation of the widget."),
    )
    # gui_only: bool
    # tooltip: str  # alias for FieldInfo.description?


@dataclass(frozen=True)
class ContainerOptions:
    """Options that pertain to a container or layout of widgets."""

    layout: str


@dataclass(frozen=True)
class UiFieldInfo(
    WidgetConstraints,
    ArrayContraints,
    StringContraints,
    NumericContraints,
    FieldInfo,
    ValueConstraints,
):
    """Information about a field that can be used to generate a widget."""

    extra: dict = field(
        default_factory=dict,
        metadata=dict(description="Extra info passed to the UiField constructor"),
    )

    @classmethod
    def from_dataclass_metadata(cls, metadata: Mapping, **kwargs) -> "UiFieldInfo":
        return UiField(**{**metadata, **kwargs})

    @classmethod
    def _from_annotated_types(cls, *types: "BaseMetadata") -> "UiFieldInfo":
        # https://github.com/annotated-types/annotated-types
        # possible keys from annotated_types (so far)
        # 'gt', 'ge', 'lt', 'le', 'multiple_of', 'min_inclusive', 'max_exclusive',
        # 'tz', and 'func'

        kwargs = {}
        for t in types:
            kwargs.update(asdict(t))

        if "func" in kwargs:
            warnings.warn(
                "annotated_types.Predicate is not yet implemented in `UiFieldInfo`"
            )
            del kwargs["func"]
        if "tz" in kwargs:
            del kwargs["tz"]
            kwargs["format"] = "date-time"
        return UiField(**kwargs)

    @classmethod
    def from_annotated(
        cls, annotation: Any, field_name: str = ""
    ) -> Optional["UiFieldInfo"]:
        return _get_field_info_from_annotated(annotation, field_name)

    @classmethod
    def from_pydantic_field_info(cls, field_info: "PydanticFieldInfo") -> "UiFieldInfo":
        """Create a UiFieldInfo from a pydantic Field."""
        from pydantic.fields import Undefined as _Undef

        extra: dict = field_info.extra
        for key in list(extra):
            if key.startswith("ui_"):
                extra[key[3:]] = extra.pop(key)

        return UiField(
            default=Undefined if field_info.default is _Undef else field_info.default,
            default_factory=field_info.default_factory,
            description=field_info.description,
            title=field_info.title,
            const=field_info.const or False,
            minimum=field_info.ge,
            maximum=field_info.le,
            exclusive_minimum=field_info.gt,
            exclusive_maximum=field_info.lt,
            multiple_of=field_info.multiple_of,
            min_length=field_info.min_length,
            max_length=field_info.max_length,
            pattern=field_info.regex,
            # format=...,
            min_items=field_info.min_items,
            max_items=field_info.max_items,
            unique_items=field_info.unique_items,
            **extra,
        )


FIELDS: Set[str] = set()
ALIASES: Dict[str, str] = {}

for field_info in fields(UiFieldInfo):
    FIELDS.add(field_info.name)
    for alias in field_info.metadata.get("aliases", []):
        ALIASES[alias] = field_info.name


def UiField(
    *,
    default: Any = Undefined,
    default_factory: Optional[Callable[[], Any]] = None,
    const: bool = False,
    enum: Optional[List[Any]] = None,
    bind: Union[Callable[[ValueWidget], Any], Any, None] = None,
    # FieldInfo
    title: Optional[str] = None,
    description: Optional[str] = None,
    button_text: Optional[str] = None,
    # NumericContraints
    multiple_of: Optional[float] = None,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
    exclusive_minimum: Optional[float] = None,
    exclusive_maximum: Optional[float] = None,
    max_digits: Optional[int] = None,
    decimal_places: Optional[int] = None,
    # StringContraints
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    pattern: Optional[str] = None,
    format: Optional[JsonStringFormats] = None,
    # ArrayContraints
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    unique_items: Optional[bool] = None,
    # WidgetConstraints
    widget_type: Optional[WidgetRef] = None,
    visible: bool = True,
    enabled: bool = True,
    orientation: Optional[Literal["horizontal", "vertical"]] = None,
    **extra,
) -> UiFieldInfo:
    """Create a UiFieldInfo object, used to hold info that can create a widget."""
    _extra = dict(extra)
    for key in list(_extra):
        if key not in FIELDS:
            if key in ALIASES:
                # if locals()[ALIASES[key]] is None:  # which takes precendence ?
                locals()[ALIASES[key]] = _extra.pop(key)
            elif key == "allow_multiple":
                _extra.pop(key)
                widget_type = "Select"
                # TODO: add a warning
            elif key in ("options", "readout", "tracking", "mode"):
                # TODO
                # _extra.pop(key)
                ...
            else:
                raise ValueError(f"{key} is not a valid field")

    return UiFieldInfo(
        default=default,
        default_factory=default_factory,
        const=const,
        enum=enum,
        bind=bind,
        #
        title=title,
        description=description,
        button_text=button_text,
        #
        multiple_of=multiple_of,
        minimum=minimum,
        maximum=maximum,
        exclusive_minimum=exclusive_minimum,
        exclusive_maximum=exclusive_maximum,
        max_digits=max_digits,
        decimal_places=decimal_places,
        #
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        format=format,
        #
        min_items=min_items,
        max_items=max_items,
        unique_items=unique_items,
        #
        widget_type=widget_type,
        visible=visible,
        enabled=enabled,
        orientation=orientation,
        extra=_extra,
    )


def _get_field_info_from_annotated(
    annotation, field_name: str = ""
) -> Optional[UiFieldInfo]:
    # this should only be called `if get_origin(annotation) is Annotated`:

    pydantic_fields = sys.modules.get("pydantic.fields")
    annotated_types = sys.modules.get("annotated_types")

    err_msg = f"cannot specify multiple `Annotated` items in {field_name!r}"

    _base_metas: List["BaseMetadata"] = []
    field_info: Optional[UiFieldInfo] = None
    for arg in get_args(annotation)[1:]:
        # see if it's our FieldInfo type
        if isinstance(arg, UiFieldInfo):
            if field_info is not None:
                raise ValueError(err_msg)
            field_info = copy(arg)
        # see if it's pydantic FieldInfo
        elif pydantic_fields and isinstance(arg, pydantic_fields.FieldInfo):
            if field_info is not None:
                raise ValueError(err_msg)
            field_info = UiFieldInfo.from_pydantic_field_info(arg)
        # see if it's annotated_types.BaseMetadata
        elif annotated_types is not None:
            if isinstance(arg, annotated_types.BaseMetadata):
                _base_metas.append(arg)
            elif isinstance(arg, annotated_types.GroupedMetadata):
                _base_metas.extend(arg)
            elif isinstance(arg, slice):
                start, stop = (arg.start or 0), arg.stop
                _base_metas.append(
                    annotated_types.Len(min_inclusive=start, max_inclusive=stop)
                )
            # TODO: re.Pattern?

    if field_info is None:
        field_info = UiFieldInfo._from_annotated_types(*_base_metas)
    elif annotated_types:
        raise ValueError(
            f"Cannot use both {type(field_info)} and annotated_types in {field_name!r}"
        )

    if field_info.default not in (Undefined, Ellipsis):
        raise ValueError(
            "`UiField` default cannot be set in `Annotated` " f"for {field_name!r}"
        )
    return field_info
