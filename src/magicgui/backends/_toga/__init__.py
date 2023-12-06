from .application import ApplicationBackend

__all__ = [
    "ApplicationBackend",
    "CheckBox",
    "ComboBox",
    "Container",
    "DateEdit",
    "DateTimeEdit",
    "Dialog",
    "EmptyWidget",
    "FloatRangeSlider",
    "FloatSlider",
    "FloatSpinBox",
    "get_text_width",
    "Image",
    "Label",
    "LineEdit",
    "LiteralEvalLineEdit",
    "MainWindow",
    "Password",
    "ProgressBar",
    "PushButton",
    "QuantityEdit",
    "RadioButton",
    "RadioButtons",
    "RangeSlider",
    "Select",
    "show_file_dialog",
    "Slider",
    "SpinBox",
    "Table",
    "TextEdit",
    "TimeEdit",
    "ToolBar",
]


def __getattr__(name):
    from . import widgets

    return getattr(widgets, name)
