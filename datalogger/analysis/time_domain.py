from datalogger.api.pyqtgraph_extensions import InteractivePlotWidget


class TimeDomainWidget(InteractivePlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
