import sys
from PyQt5.QtWidgets import QApplication

from datalogger.api.workspace import Workspace
from datalogger.analysis_window import AnalysisWindow
from datalogger import __version__

def run_datalogger_full():
    print("CUED DataLogger {}".format(__version__))

    app = 0
    app = QApplication(sys.argv)

    # Create the window
    w = AnalysisWindow()

    w.CurrentWorkspace = Workspace()
    #w.CurrentWorkspace.path = "//cued-fs/users/general/tab53/ts-home/Documents/urop/Logger 2017/cued_datalogger/"
    # Load the workspace
    #CurrentWorkspace.load("//cued-fs/users/general/tab53/ts-home/Documents/urop/Logger 2017/cued_datalogger/tests/test_workspace.wsp")

    #w.addon_widget.discover_addons(w.CurrentWorkspace.path + "addons/")

    # Run the program
    w.show()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    run_datalogger_full()
    