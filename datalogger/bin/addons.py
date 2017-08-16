import sys
import os
from queue import Queue

from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QApplication, QVBoxLayout, QTreeWidget,
                             QTreeWidgetItem, QTextEdit, QLineEdit, QPushButton,
                             QLabel, QHBoxLayout, QFileDialog)


class AddonManager(QWidget):
    """A widget for loading and running addons.
    
    The :class:`AddonManager` consists of a QTreeWidget (:attr:`tree`) for selecting and 
    viewing addons, QPushButtons for running and loading addons, and a 
    QTextEdit (:attr:`output`) which is used to display the output from the addon."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.addon_functions = {}

        self.addon_local_vars = {}
        self.addon_global_vars = {}

        self.init_ui()

        # # Addon Execution Initialisation
        # When the addon is run, stdout must be redirected
        # Create a buffer for redirecting stdout
        self.stdout_buffer = Queue()
        # Create a writestream - this is a wrapper for the buffer, that behaves
        # like stdout (ie it has a write function)
        self.writestream = WriteStream(self.stdout_buffer)
        # Create the object that writes to the textedit
        self.text_receiver = TextReceiver(self.stdout_buffer)
        self.text_receiver.sig_text_received.connect(self.output.append)

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabels(["Name", "Author", "Description"])
        self.import_export = QTreeWidgetItem(self.tree)
        self.import_export.setText(0, "Import/Export")
        self.analysis = QTreeWidgetItem(self.tree)
        self.analysis.setText(0, "Analysis")
        self.plotting = QTreeWidgetItem(self.tree)
        self.plotting.setText(0, "Plotting")
        self.tree.itemDoubleClicked.connect(self.run_selected)
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
        """Find any addons contained in **path** (*str*) and load them."""
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
        """Load new addon(s) from file (opens a file explorer)."""
        # Get a list of URLs from a QFileDialog
        url_list = QFileDialog.getOpenFileNames(self, "Load new addon", "addons",
                                               "DataLogger Addons (*.py)")[0]

        # For each url, add it to the tree
        for url in url_list:
            self.add_addon(url)

    def add_addon(self, addon_url):
        """Add an addon to the :attr:`tree`.
        
        **Arguments**:
            **addon_url** (*str*): The path to the addon ``.py`` file."""
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
        """Run the addon that is currently selected in the :attr:`tree`, routing its
        output to the :attr:`output` TextEdit."""
        # Get the addon metadata from the tree
        name = self.tree.currentItem().data(0, Qt.DisplayRole)
        author = self.tree.currentItem().data(1, Qt.DisplayRole)
        description = self.tree.currentItem().data(2, Qt.DisplayRole)

        # # Run the addon function, but redirect the stdout
        # Redirect stdout to the writestream
        stdout_old = sys.stdout
        sys.stdout = self.writestream

        # Start the receiver
        self.start_receiver_thread()

        # Print some info about the addon
        print("###\n {} by {}\n {}\n###".format(name, author, description))
        # Execute the addon
        try:
            self.addon_functions[name](self.parent)
        finally:
            # Tidy up
            self.receiver_thread.terminate()
            sys.stdout = stdout_old

    def start_receiver_thread(self):
        """Open a new :class:`QThread` and move the :attr:`text_receiver`
        to that thread."""
        # Create a thread for the receiver
        self.receiver_thread = QThread()
        # Move the receiver to the thread
        self.text_receiver.moveToThread(self.receiver_thread)
        # Run the receiver
        self.receiver_thread.started.connect(self.text_receiver.run)
        self.receiver_thread.start()


class WriteStream(object):
    """A simple object that writes to a queue.
    
    A :class:`WriteStream` object is used to replace stdout so that text 
    sent to stdout with :func:`print` or any other write function is
    placed in the queue.
    
    **Attributes**:
        queue (*Queue*): The queue which is written to."""
    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        """Put text in the queue
        Args:
            text (*str*): Text to put in queue"""
        self.queue.put(text)


class TextReceiver(QObject):
    """A :class:`QObject` that blocks until there is something to read from a 
    buffer (*Queue*), which it emits as a signal. 
    
    Run in a :class:`QThread` to send text from a :class:`WriteStream` to a 
    :class:`TextEdit` when an addon is run."""
    sig_text_received = pyqtSignal(str)

    def __init__(self, buffer):
        super().__init__()
        self.buffer = buffer

    def run(self):
        while True:
            # Get text from the buffer (block until there's something to get)
            text = self.buffer.get()
            # If we got something, send the text received signal
            self.sig_text_received.emit(text)


if __name__ == '__main__':
    sys.path.append('../')
    
    import pyqtgraph as pg   
    from analysis_window_testing import AnalysisWindow
    from bin.channel import ChannelSet

    app = 0
    app = QApplication(sys.argv)

    w = AnalysisWindow()

    w.addon_widget.discover_addons("../addons/")

    w.show()

    sys.exit(app.exec_())
