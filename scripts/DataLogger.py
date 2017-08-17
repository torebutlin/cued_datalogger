#!/usr/bin/env python

import sys
from PyQt5.QtWidgets import QApplication

import datalogger.analysis_window_testing
import datalogger.bin.workspace

# Create the Qt application
app = 0
app = QApplication(sys.argv)

# Create the window
w = datalogger.analysis_window_testing.AnalysisWindow()

w.CurrentWorkspace = datalogger.bin.workspace.Workspace()
w.CurrentWorkspace.path = "/home/theo/Documents/cambridge/urop/cued_datalogger"
# Load the workspace
#CurrentWorkspace.load("//cued-fs/users/general/tab53/ts-home/Documents/urop/Logger 2017/cued_datalogger/tests/test_workspace.wsp")

w.addon_widget.discover_addons(w.CurrentWorkspace.path + "/datalogger/addons/")

# Run the program
w.show()
sys.exit(app.exec_())
