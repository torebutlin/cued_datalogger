import sys
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    sys.path.append('../')


from datalogger.api.workspace import Workspace
from datalogger.analysis_window import AnalysisWindow
from datalogger import __version__

def run_datalogger_full():
    print("CUED DataLogger {}".format(__version__))

    app = 0
    app = QApplication(sys.argv)

    CurrentWorkspace = Workspace()

    # Create the window
    w = AnalysisWindow()

    w.CurrentWorkspace = CurrentWorkspace

    #w.addon_widget.discover_addons(w.CurrentWorkspace.path + "addons/")

    # Run the program
    w.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run_datalogger_full()
