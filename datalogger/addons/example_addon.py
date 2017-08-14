#datalogger_addon
addon_metadata = {"name": "Example Addon",
                  "author": "John Smith",
                  "description": "An example addon",
                  "category": "Import/Export"}

def run():
    # Addons allow imports
    import matplotlib.pyplot as plt
    import numpy as np

    # Addons allow popups
    plt.plot(np.sin(np.arange(100)))

    # Addons allow printing to stdout
    print("Hello World!")