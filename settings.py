from comrad import CDisplay

from widgetDelegate import MyWidgetDelegate


class Display(CDisplay):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.property_edit.widget_delegate = MyWidgetDelegate()

    def ui_filename(self):
        return 'settings.ui'

