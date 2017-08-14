import sys
from PyQt5.QtWidgets import QApplication

from bin.workspace import Workspace
from analysis_window import AnalysisWindow


if __name__ == '__main__':
    app = 0
    app = QApplication(sys.argv)

    CurrentWorkspace = Workspace()
    # Load the workspace
    #CurrentWorkspace.load("//cued-fs/users/general/tab53/ts-home/Documents/urop/Logger 2017/cued_datalogger/tests/test_workspace.wsp")

    # Create the window
    w = AnalysisWindow()

    # Run the program
    sys.exit(app.exec_())
