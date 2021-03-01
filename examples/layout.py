from magicgui import widgets
from magicgui.widgets._bases.layout import GridLayout, HBoxLayout


class Container(widgets.EmptyWidget):
    def __init__(self, widgets=(), layout="vertical"):
        super().__init__()
        self._widgets = dict.fromkeys(widgets)
        self.layout = layout

    def __hash__(self):
        return id(self)

    @property
    def layout(self):
        ...

    @layout.setter
    def layout(self, layout):
        existing = self.native.layout()
        if existing:
            from qtpy.QtWidgets import QWidget

            while True:
                i = existing.takeAt(0)
                if not i:
                    break
                w = i.widget()
                if w:
                    w.setParent(None)
            QWidget().setLayout(existing)
        layout.assert_alive()
        self.native.setLayout(layout.native)


sb1 = widgets.SpinBox(value=1)
sb2 = widgets.SpinBox(value=2)
sb3 = widgets.SpinBox(value=3)
sb4 = widgets.SpinBox(value=4)
sb5 = widgets.SpinBox(value=5)

layouta = HBoxLayout([sb1, sb2, sb3, sb4, sb5])

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
c = Container([sb1, sb2, sb3, sb4, sb5], layout)
c.show(run=True)
