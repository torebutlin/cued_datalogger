from datalogger.api.pyqtgraph_extensions import InteractivePlotWidget


class FrequencyDomainWidget(InteractivePlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)