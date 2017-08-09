from PyQt5.QtWidgets import QWidget, QGridLayout

import pyqtgraph as pg

class TimeDomainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()

        layout = QGridLayout(self)

        self.time_domain_plot = pg.PlotWidget(self)

        layout.addWidget(self.time_domain_plot)
