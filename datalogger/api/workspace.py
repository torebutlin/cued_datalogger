import pyqtgraph as pg
import re


class Workspace(object):
    """
    The ``Workspace`` class stores the workspace attributes and has methods for
    saving, loading, configuring, and displaying the workspace settings.
    
    Workspaces are designed so that specific configurations of the DataLogger
    can be created, eg. for undergraduate labs, with different features 
    enabled or disabled, and stored in a ``.wsp`` file that can be read using
    the :class:`Workspace` class. In the DataLogger, a ``CurrentWorkspace`` 
    instance is normally initiated that will store the current settings and all 
    the workspace functionality will be accessed through the
    ``CurrentWorkspace``. 
    
    Attributes
    ----------
    name : str
        A human-readable name for this workspace, eg. ``"Lab 4C6"``
    path : str
        The path to this workspace's directory. Addons will be loaded from the
        directory ``path/addons/``, and files will be saved to ``path`` (not 
        implemented yet). Default value is ``"./"``.
    add_ons_enabled : bool
        Flag that sets whether to addons are enabled (not implemented yet - 
        currently has no effect). Default value is ``True``
    pyqtgraph_inverted : bool
        Flag that sets whether pyqtgraph uses a white background and black
        lines (``False``), or black background and white lines (``True``).
        Default value is ``False``.
    default_pen : str
        The default colour of the pen, set by :attr:`pyqtgraph_inverted`.
        Cannot be set manually.
    pyqtgraph_antialias : bool
        Flag that sets whether pyqtgraph uses antialiasing for smoother lines.
        Default value is ``True``.
    """
    def __init__(self):
        # Set default values:
        self.name = "Default Workspace"
        self.path = "./"
        self.add_ons_enabled = 1
        self.pyqtgraph_inverted = 0
        self.pyqtgraph_antialias = 1
        self.default_pen = None

        self.configure()

    def settings(self):
        """A convenience method to access this workspace's configuration"""
        return vars(self)

    def save(self, destination):
        """Save this workspace to *destination* (of the form 
        ``"/path/to/workspace.wsp"``)."""

        print("Saving current workspace to {} ...".format(destination))
        print("\t Settings found:")
        # Open the destination file
        with open(destination, 'w') as wsp_file:
            for name, value in vars(self).items():
                print("\t {}: {}".format(name, value))
                # Write the settings to the file
                # Ensure that the strings are written in quotes
                if isinstance(value, str):
                    wsp_file.write("{}='{}'\n".format(name, value))
                else:
                    wsp_file.write("{}={}\n".format(name, value))

        print("Done.")

    def load(self, workspace):
        """Load the settings found in the .wsp file given by *workspace*`
        (of the form ``"/path/to/workspace.wsp"``)."""

        print("Loading workspace {} ...".format(workspace))
        print("\t Settings found:")
        # Open as a read-only file object
        with open(workspace, 'r') as wsp_file:
            for line in wsp_file:
                # Create a regex to match the correct form:
                # variable_name=(0 or 1) or variable_name="string/or/path.py"
                correct_form = re.compile("(\w*)=([0|1]|\'[\w\s./]*\'\n)")
                line_match = re.match(correct_form, line)

                # If this line matches
                if line_match:
                    # Split about the equals sign
                    variable_name, variable_value = line.split('=')

                    # Sort out types
                    # Strings will all start with '
                    if variable_value[0] == "'":
                        # Split the string with ' as delimiter
                        # giving ['', "string", ''] and extract the second
                        # argument
                        variable_value = variable_value.split("'")[1]
                    else:
                        # Otherwise, treat it as an int
                        variable_value = int(variable_value)

                    # Check if these are attributes of the Workspace
                    if hasattr(self, variable_name):
                        # If so, set the attribute
                        setattr(self, variable_name, variable_value)
                        print("\t {}: {}".format(variable_name, variable_value))

        print("Done.")

        self.configure()

    def configure(self):
        """Set the global configuration of the DataLogger
        to the settings in this workspace."""

        print("Configuring workspace...")

        # # Set other settings
        # <code>

        # # Set PyQtGraph settings
        if self.default_pen is None:
            if self.pyqtgraph_inverted:
                self.default_pen = pg.mkPen()
            else:
                self.default_pen = pg.mkPen('k')

        if not self.pyqtgraph_inverted:
            pg.setConfigOption('background', 'w')
            pg.setConfigOption('foreground', 'k')
        else:
            pg.setConfigOption('background', 'k')
            pg.setConfigOption('foreground', 'w')


        if self.pyqtgraph_antialias:
            pg.setConfigOption('antialias', True)
        else:
            pg.setConfigOption('antialias', False)

        print("Done.")
