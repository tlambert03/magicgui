from __future__ import annotations

from abc import ABC, abstractmethod
from itertools import product
from typing import (
    TYPE_CHECKING,
    Any,
    Collection,
    Dict,
    List,
    MutableSequence,
    Optional,
    Sequence,
    Tuple,
    Union,
    overload,
)

from magicgui.application import use_app
from magicgui.widgets import Widget

from .._bases import ButtonWidget, ValueWidget

if TYPE_CHECKING:
    from magicgui.widgets import _protocols

Index = Union[int, slice]
Key = Tuple[Index, Index]


class Layout(MutableSequence[Widget], ABC):
    _layout: _protocols.BoxLayoutProtocol
    _initialized = False

    def __init__(
        self,
        widgets: Sequence[Widget] = (),
        labels=True,
        **kwargs,
    ):
        app = use_app()
        assert app.native
        self._layout = self._create_layout()
        self._list: List[Widget] = []
        self._labels = labels
        self._initialized = True
        self.extend(widgets)
        self._unify_label_widths()

    @property
    def labels(self) -> bool:
        """Whether widgets are presented with labels."""
        return self._labels

    @labels.setter
    def labels(self, value: bool):
        if value == self._labels:
            return
        self._labels = value

        for index, _ in enumerate(self):
            widget = self.pop(index)
            self.insert(index, widget)

    @abstractmethod
    def _create_layout(self):
        raise NotImplementedError

    @property
    def native(self):
        return self._layout._mgui_get_native_layout()

    def __getattr__(self, name: str):
        """Return attribute ``name``.  Will return a widget if present."""
        for widget in self:
            if name == widget.name:
                return widget
        return object.__getattribute__(self, name)

    def __setattr__(self, name: str, value: Any):
        """Set attribute ``name``.  Prevents changing widget if present, (use del)."""
        if self._initialized:
            for widget in self:
                if name == widget.name:
                    raise AttributeError(
                        "Cannot set attribute with same name as a widget\n"
                        "If you are trying to change the value of a widget, use: "
                        f"`{self.__class__.__name__}.{name}.value = {value}`",
                    )
        object.__setattr__(self, name, value)

    @overload
    def __getitem__(self, key: Union[int, str]) -> Widget:  # noqa: D105
        ...

    @overload
    def __getitem__(self, key: slice) -> MutableSequence[Widget]:  # noqa: F811, D105
        ...

    def __getitem__(self, key):  # noqa: F811
        """Get item by integer, str, or slice."""
        if isinstance(key, str):
            return self.__getattr__(key)
        if isinstance(key, slice):
            return [getattr(item, "_inner_widget", item) for item in self._list[key]]
        elif isinstance(key, int):
            item = self._list[key]
            return getattr(item, "_inner_widget", item)
        raise TypeError(f"list indices must be integers or slices, not {type(key)}")

    def __delitem__(self, key: Union[int, slice]):
        """Delete a widget by integer or slice index."""
        if isinstance(key, slice):
            for item in self._list[key]:
                self._layout._mgui_remove_widget(item)
        elif isinstance(key, int):
            self._layout._mgui_remove_widget(self._list[key])
        else:
            raise TypeError(f"list indices must be integers or slices, not {type(key)}")
        del self._list[key]

    def __len__(self) -> int:
        """Return the count of widgets."""
        return len(self._list)

    def __setitem__(self, key, value):
        """Prevent assignment by index."""
        raise NotImplementedError("magicgui.Layout does not support item setting.")

    def insert(self, key: int, widget: Widget):
        """Insert widget at ``key``."""
        if isinstance(widget, ValueWidget):
            widget.changed.connect(lambda x: self.changed(value=self))
        _widget = widget

        if self.labels:
            from magicgui.widgets._concrete import _LabeledWidget

            # no labels for button widgets (push buttons, checkboxes, have their own)
            if not isinstance(widget, (_LabeledWidget, ButtonWidget)):
                _widget = _LabeledWidget(widget)
                # TODO: if we can move this logic to _LabeledWidget, we can keep
                # _unify_label_widths only on VBoxLayout
                widget.label_changed.connect(self._unify_label_widths)

        self._list.insert(key, widget)
        if key < 0:
            key += len(self)

        # NOTE: if someone has manually mucked around with self.native.layout()
        # it's possible that indices will be off.
        self._layout._mgui_insert_widget(key, _widget)
        self._unify_label_widths()

    def _unify_label_widths(self):
        pass


class HBoxLayout(Layout):
    def _create_layout(self):
        layout = use_app().get_obj("HBoxLayout")
        return layout()


class VBoxLayout(Layout):
    def _create_layout(self):
        layout = use_app().get_obj("VBoxLayout")
        return layout()

    def _unify_label_widths(self, event=None):
        if not (self._initialized and self.labels and len(self)):
            return

        measure = use_app().get_obj("get_text_width")
        widest_label = max(
            measure(w.label) for w in self if not isinstance(w, ButtonWidget)
        )
        for w in self:
            labeled_widget = w._labeled_widget()
            if labeled_widget:
                labeled_widget.label_width = widest_label


class GridLayout:
    """Defines a NxM grid layout of Widgets.

    Parameters
    ----------
    n_rows : int
        number of rows in the grid
    n_columns : int
        number of columns in the grid
    widgets : dict, optional
        mapping of ``{widget: (rows, cols)}`` to populate the grid.  Where ``rows`` and
        ``cols`` can be ``int`` or ``slice``. For example, to assign a ``Label`` widget
        to the first 3 rows in the first column: ``{PushButton(): (slice(3), 0)}``

    Examples
    --------
    >>> from magicgui.widgets._bases.layout import GridLayout
    >>> from magicgui.widgets import PushButton, Label
    >>> layout = GridLayout(n_rows=4, n_columns=2)
    >>> layout[:3, 0] = PushButton(name='1')
    >>> layout[1:, 1] = Label(name='2')
    >>> layout[-1, 0] = PushButton(name='3')
    >>> layout[0, 1] = PushButton(name='4')
    >>> layout
    GridLayout (4, 2)
    ╔═══════════════════════════════╦═══════════════════════════════╗
    ║  PushButton::140305881803984  ║  PushButton::140306118155568  ║
    ║  PushButton::140305881803984  ║  Label::140306118028784       ║
    ║  PushButton::140305881803984  ║  Label::140306118028784       ║
    ║  PushButton::140305872917216  ║  Label::140306118028784       ║
    ╚═══════════════════════════════╩═══════════════════════════════╝

    >>> GridLayout(3,2,{PushButton(): (slice(2), 0), Label(): (2, 1)})
    GridLayout (3, 2)
    ╔═══════════════════════════════╦═══════════════════════════════╗
    ║  PushButton::140502885644848  ║  -                            ║
    ║  PushButton::140502885644848  ║  -                            ║
    ║  -                            ║  Label::140502905362416       ║
    ╚═══════════════════════════════╩═══════════════════════════════╝
    """

    _EMPTY = "-"
    _grid: List[List[str]]  # 2D list of widget ids

    def __init__(self, n_rows: int, n_columns: int, widgets: Dict[Widget, Key] = {}):
        if not all(isinstance(x, int) and x > 0 for x in (n_rows, n_columns)):
            raise TypeError("n_rows and n_columns must be positive integers")
        self._n_rows = n_rows
        self._n_columns = n_columns
        self._children: Dict[str, Tuple[Widget, Tuple[Collection, Collection]]] = {}
        self.clear()
        if widgets:
            for widget, key in widgets.items():
                self.__setitem__(key, widget)

    def clear(self):
        """Clear the grid and remove all widgets."""
        self._children.clear()
        self._grid = [[self._EMPTY] * self._n_columns for i in range(self._n_rows)]

    @property
    def shape(self) -> Tuple[int, int]:
        """Return shape of grid in (rows, columns)."""
        return self._n_rows, self._n_columns

    def _widget_key(self, value: Widget):
        return f"{type(value).__name__}::{id(value)}"

    def _remove_widget_key(self, key: str):
        widget, index = self._children.pop(key)
        for r, c in product(*index):
            self._grid[r][c] = self._EMPTY

    def remove_widget(self, value: Widget):
        """Remove widget wherever present in the layout.

        Raises
        ------
        KeyError
            If the widget is not in the layout.
        """
        try:
            self._remove_widget_key(self._widget_key(value))
        except KeyError:
            raise KeyError(f"Widge {value!r} not found in {type(self).__name__}.")

    def _indices_from_slice(
        self, row: Index, column: Index
    ) -> Tuple[Collection[int], Collection[int]]:
        """Convert a two-dimensional slice to a list of rows and column indices."""
        rows: Collection[int]
        columns: Collection[int]

        if isinstance(row, slice):
            start, stop, stride = row.indices(self._n_rows)
            rows = range(start, stop, stride)
        elif isinstance(row, int):
            if row < 0:
                row += self._n_rows
            rows = [row]
        else:
            raise TypeError("`row` must either be an int or a slice")

        if isinstance(column, slice):
            start, stop, stride = column.indices(self._n_columns)
            columns = range(start, stop, stride)
        elif isinstance(column, int):
            if column < 0:
                column += self._n_columns
            columns = [column]
        else:
            raise TypeError("`column` must either be an int or a slice")

        return rows, columns

    def __setitem__(self, key, value: Union[Widget, Collection[Widget]]):
        if isinstance(key, (int, slice)):
            key = (key, slice(None))

        rows, columns = self._indices_from_slice(*key)

        if isinstance(value, Collection):
            if len(rows) == len(value):
                assert len(columns) == 1
                for k, val in zip(product(rows, columns), value):
                    self.__setitem__(k, val)
            elif len(columns) == len(value):
                assert len(rows) == 1
                for k, val in zip(product(rows, columns), value):
                    self.__setitem__(k, val)
            else:
                raise ValueError(
                    "When setting a slice to a collection of widgets, "
                    "the length of the collection must match either the number of rows "
                    "or columns in the key."
                )
            return

        obj_id = self._widget_key(value) if value is not None else self._EMPTY
        for row in rows:
            for column in columns:
                try:
                    current_wkey = self._grid[row][column]
                except IndexError:
                    raise IndexError(
                        f"index [{row}, {column}] is out of range for "
                        f"{type(self).__name__} with shape {self.shape}"
                    )
                if current_wkey != self._EMPTY and current_wkey in self._children:
                    self._remove_widget_key(current_wkey)
                self._grid[row][column] = obj_id

        self._children[obj_id] = (value, (rows, columns))

    def __getitem__(self, key) -> Optional[Widget]:
        if isinstance(key, (int, slice)):
            key = (key, slice(None))

        rows, columns = self._indices_from_slice(*key)

        obj_id = None
        for row in rows:
            for column in columns:
                try:
                    new_obj_id = self._grid[row][column]
                except IndexError:
                    raise IndexError(
                        f"index [{row}, {column}] is out of range for "
                        f"{type(self).__name__} with shape {self.shape}"
                    )
                obj_id = obj_id or new_obj_id
                if obj_id != new_obj_id:
                    raise ValueError(
                        "The slice spans several widgets, but "
                        "only a single widget can be retrieved "
                        "at a time"
                    )
        if obj_id is None:
            raise IndexError

        if obj_id == self._EMPTY:
            return None

        return self._children[obj_id][0]

    def __delitem__(self, key):
        if isinstance(key, (int, slice)):
            key = (key, slice(None))

        rows, columns = self._indices_from_slice(*key)

        for row in rows:
            for column in columns:
                try:
                    current_wkey = self._grid[row][column]
                except IndexError:
                    raise IndexError(
                        f"index [{row}, {column}] is out of range for "
                        f"{type(self).__name__} with shape {self.shape}"
                    )
                if current_wkey != self._EMPTY and current_wkey in self._children:
                    self._remove_widget_key(current_wkey)

    def __repr__(self):
        return f"GridLayout {self.shape}\n" + str(self)

    def __str__(self):
        cw = max(map(len, self._children))
        return _table_repr(self._grid, ncols=self._n_columns, cell_width=cw)

    def __iter__(self):
        for id, (widget, (rows, cols)) in self._children.items():
            r_start = rows.start if isinstance(rows, range) else rows[0]  # type: ignore
            c_start = cols.start if isinstance(cols, range) else cols[0]  # type: ignore
            yield widget, (r_start, c_start, len(rows), len(cols))


def _table_repr(
    data: Collection[Collection],
    padding=2,
    ncols=None,
    cell_width=None,
    divide_rows=False,
):
    """Pretty string repr of a 2D table."""
    nrows = len(data)
    ncols = ncols or len(data[0])  # type: ignore
    cell_width = cell_width or max(len(str(item)) for row in data for item in row)

    TOP = ("╔", "╤", "╗", "═")
    MID = ("╟", "┼", "╢", "─")
    BOT = ("╚", "╧", "╝", "═")
    V = ("║", "│")

    pad = " " * padding
    cell_template = (pad + "{{:{0}}}" + pad).format(cell_width)
    row_template = V[0] + V[1].join([cell_template] * ncols) + V[0]

    def _border(left, sep, right, line):
        _cell = len(cell_template.format("")) * line
        return left + sep.join([_cell] * ncols) + right

    body = [_border(*TOP)]

    for i, row in enumerate(data):
        body.append(row_template.format(*row))
        if divide_rows and i < nrows - 1:
            body.append(_border(*MID))

    body.append(_border(*BOT))
    return "\n".join(body)
