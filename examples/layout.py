from magicgui import widgets
from magicgui.widgets._bases.layout import GridLayout, HBoxLayout
from magicgui.backends._qtpy.widgets import GridLayout as QGridLayout


class C(widgets.EmptyWidget):
    def __init__(self, widgets=(), layout="horizontal"):
        super().__init__()
        self._widgets = dict.fromkeys(widgets)
        self.set_layout(layout)

    def __hash__(self):
        return id(self)

    def set_layout(self, layout):
        qgl = QGridLayout()
        for widget, args in layout:
            qgl._mgui_add_widget(widget, *args)
        self.native.setLayout(qgl._mgui_get_native_layout())


sb1 = widgets.SpinBox(value=1)
sb2 = widgets.SpinBox(value=2)
sb3 = widgets.SpinBox(value=3)
sb4 = widgets.SpinBox(value=4)
sb5 = widgets.SpinBox(value=5)

layout = HBoxLayout([sb1, sb2, sb3, sb4, sb5])

layout = GridLayout(
    3,
    2,
    {
        sb1: (0, 0),
        sb2: (0, 1),
        sb3: (1, 0),
        sb4: (1, 1),
        sb5: (2, slice(None)),
    },
)

c = C([sb1, sb2, sb3, sb4, sb5], layout)
c.show(run=True)
