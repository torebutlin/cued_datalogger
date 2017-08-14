import sys
if __name__ == '__main__':
    sys.path.append('../')
    from analysis_window_testing import AnalysisWindow

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QApplication, QVBoxLayout, QTreeWidget,
                             QTreeWidgetItem, QTextEdit, QLineEdit, QPushButton,
                             QLabel, QHBoxLayout, QFileDialog)

from io import StringIO
from contextlib import redirect_stdout
import os
import pyqtgraph as pg

from bin.channel import ChannelSet

class AddonWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.addon_functions = {}

        self.addon_local_vars = {}
        self.addon_global_vars = {}

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
        self.tree.setHeaderLabels(["Name", "Author", "Description"])
        self.import_export = QTreeWidgetItem(self.tree)
        self.import_export.setText(0, "Import/Export")
        self.analysis = QTreeWidgetItem(self.tree)
        self.analysis.setText(0, "Analysis")
        self.plotting = QTreeWidgetItem(self.tree)
        self.plotting.setText(0, "Plotting")
        self.layout.addWidget(self.tree)

        self.load_btn = QPushButton(self)
        self.load_btn.setText("Load Addon")
        self.load_btn.clicked.connect(self.load_new)
        self.layout.addWidget(self.load_btn)

        self.run_btn = QPushButton(self)
        self.run_btn.setText("Run selected")
        self.run_btn.clicked.connect(self.run_selected)
        self.layout.addWidget(self.run_btn)

        output_label = QLabel("Output:")
        self.layout.addWidget(output_label)
        self.output = QTextEdit(self)
        self.output.setReadOnly(True)
        self.layout.addWidget(self.output)

    def discover_addons(self, path):
        """Find any addons contained in path and load them"""
        print("Discovering addons...")
        print("\t Found:")
        for file in os.listdir(path):
            if file.endswith(".py"):
                with open(path + file, 'r') as f:
                    line1 = f.readline()
                if line1 == "#datalogger_addon\n":
                    print("\t {}".format(path+file))
                    self.add_addon(path + file)

    def load_new(self):
        # Get a list of URLs from a QFileDialog
        url_list = QFileDialog.getOpenFileNames(self, "Load new addon", "addons",
                                               "DataLogger Addons (*.py)")[0]

        # For each url, add it to the tree
        for url in url_list:
            self.add_addon(url)

    def add_addon(self, addon_url):
        # Read the file
        with open(addon_url) as a:
            # Execute the file
            # WARNING: THIS IS RATHER DANGEROUS - there could be anything
            # in there!
            exec(a.read(), self.addon_local_vars, self.addon_global_vars)

        # Extract the metadata
        metadata = self.addon_global_vars["addon_metadata"]

        # Add the addon to the tree
        if metadata["category"] == "Import/Export":
            parent = self.import_export
        if metadata["category"] == "Analysis":
            parent = self.analysis
        if metadata["category"] == "Plotting":
            parent = self.plotting
        else:
            parent = self.tree

        addon_item = QTreeWidgetItem(parent, [metadata["name"],
                                              metadata["author"],
                                              metadata["description"]])
        # Save the addon function
        self.addon_functions[metadata["name"]] = self.addon_global_vars["run"]

    def run_selected(self):
        # Get the addon name from the tree
        addon_name = self.tree.currentItem().data(0, Qt.DisplayRole)

        # Run the addon function, but redirect the stdout to a buffer
        string_buffer = StringIO()
        with redirect_stdout(string_buffer):
            self.addon_functions[addon_name]()

        # Extract the text from the buffer and write it to the text edit
        self.output.append(string_buffer.getvalue())

if __name__ == '__main__':
    app = 0
    app = QApplication(sys.argv)

    w = AnalysisWindow()

    for i in range(w.toolbox.count()):
        w.toolbox.widget(i).addTab(AddonWidget(), "Addons")

    sys.exit(app.exec_())
