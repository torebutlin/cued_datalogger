import sys
if __name__ == '__main__':
    sys.path.append('../')
    from analysis_window_testing import AnalysisWindow

from PyQt5.QtWidgets import (QWidget, QApplication, QVBoxLayout, QTreeWidget,
                             QTreeWidgetItem, QTextEdit, QLineEdit, QPushButton,
                             QLabel, QHBoxLayout, QFileDialog)



import pyqtgraph as pg

from bin.channel import ChannelSet

class AddonWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        search_hbox = QHBoxLayout()
        search_label = QLabel("Search:")
        search_hbox.addWidget(search_label)
        self.search = QLineEdit(self)
        search_hbox.addWidget(self.search)
        self.layout.addLayout(search_hbox)

        self.tree = QTreeWidget(self)
        self.layout.addWidget(self.tree)

        self.load_btn = QPushButton(self)
        self.load_btn.setText("Load Addon")
        self.load_btn.clicked.connect(self.load_new)
        self.layout.addWidget(self.load_btn)

        self.results = QTextEdit(self)
        self.results.setReadOnly(True)
        self.layout.addWidget(self.results)

    def load_new(self):
        url_list = QFileDialog.getOpenFileUrls(self, "Load new addon", None, "DataLogger Addons (*.py)")
        print(url_list)

if __name__ == '__main__':
    app = 0
    app = QApplication(sys.argv)

    w = AnalysisWindow()

    for i in range(w.toolbox.count()):
        w.toolbox.widget(i).addTab(AddonWidget(), "Addons")

    sys.exit(app.exec_())
