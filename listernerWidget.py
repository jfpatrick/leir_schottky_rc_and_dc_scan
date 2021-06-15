from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QWidget
from comrad import CContextEnabledObject, CChannelData, Signal, CChannel, PyDMChannel, cast


class ListenerWidget(QWidget, CContextEnabledObject):
    value_acquired = Signal(CChannelData)

    def __init__(self, init_channel, parent=None):
        QWidget.__init__(self, parent)
        CContextEnabledObject.__init__(self, init_channel=init_channel)

    def on_value(self, arg):
        self.value_acquired.emit(arg)

    def create_channel(self, channel_address, context):
        ch = cast(CChannel, PyDMChannel(address=channel_address,
                                        connection_slot=None,
                                        value_slot=self.on_value,
                                        value_signal=None,
                                        write_access_slot=None))
        ch.context = context
        return ch

    def sizeHint(self):
        return QSize(0, 0)
