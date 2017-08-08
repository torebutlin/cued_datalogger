from PyQt5.QtWidgets import QWidget, QGridLayout

import pyqtgraph as pg

class FrequencyDomainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()

        layout = QGridLayout(self)

        self.frequency_domain_plot = pg.PlotWidget(self)

        layout.addWidget(self.frequency_domain_plot)
