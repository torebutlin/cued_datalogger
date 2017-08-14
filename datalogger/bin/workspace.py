import pyqtgraph as pg
import re


class Workspace():
    """The Workspace class, containing all the attributes and functions of a
    Workspace (configuration of the DataLogger)"""

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
        """A quick method of accessing this workspace's configuration"""

        return vars(self)

    def save(self, destination):
        """Save this workspace to the `destination` (/path/to/workspace.wsp)"""

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
        """Load the settings found in the .wsp file given by `workspace`
        (/path/to/workspace.wsp)"""

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
        """Set the global configuration to be the configuration of this
        workspace"""

        print("Configuring workspace...", end=' ')

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
