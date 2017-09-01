import sys
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    sys.path.append('../')


from cued_datalogger.api.workspace import Workspace
from cued_datalogger.analysis_window import AnalysisWindow
from cued_datalogger import __version__

def run_full():
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

"""
def run_4c6():
    pass
"""

if __name__ == '__main__':
    run_full()
