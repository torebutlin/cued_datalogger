import sys
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    sys.path.append('../')

import cued_datalogger
from cued_datalogger.api.workspace import Workspace
from cued_datalogger.analysis.analysis_window import AnalysisWindow
from cued_datalogger import __version__
import argparse

def run():
    parser = argparse.ArgumentParser(description="The CUED DataLogger (v{}) "
                                     "for acquiring and analysing data. \n"
                                     "See cued-datalogger.readthedocs.io for "
                                     "documentation.".format(__version__))
    parser.add_argument('-w', '--workspace', dest='workspace_path',
                        help="Run the datalogger with the configuration given "
                        "in the Workspace (.wsp) file found at WORKSPACE_PATH")

    args = parser.parse_args()

    print("CUED DataLogger {}".format(__version__))

    # Create the application instance
    app = 0
    app = QApplication(sys.argv)

    # Create the workspace instance
    CurrentWorkspace = Workspace()

    if args.workspace_path is not None:
        CurrentWorkspace.load(args.workspace_path)

    # Create the window
    w = AnalysisWindow()

    # Connect the window to the workspace
    CurrentWorkspace.set_parent_window(w)

    w.addon_widget.discover_addons(w.CurrentWorkspace.path + "/addons/")

    # Run the program
    w.show()
    sys.exit(app.exec_())
    #app.exec_()


if __name__ == '__main__':
    run()
