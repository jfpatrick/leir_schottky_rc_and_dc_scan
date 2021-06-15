from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QWidget
from comrad import CContextEnabledObject, Signal, CChannel, PyDMChannel, cast


class UpdaterWidget(QWidget, CContextEnabledObject):
    update_signal = Signal(dict)

    def __init__(self, parent=None, init_channel=None):
        QWidget.__init__(self, parent)
        CContextEnabledObject.__init__(self, init_channel=init_channel)

    def create_channel(self, channel_address, context):
        ch = cast(CChannel, PyDMChannel(address=channel_address,
                                        connection_slot=None,
                                        value_slot=None,
                                        value_signal=self.update_signal,
                                        write_access_slot=None))
        ch.context = context
        return ch

    def sizeHint(self):
        return QSize(0, 0)
