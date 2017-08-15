#datalogger_addon

#------------------------------------------------------------------------------
# Put metadata about this addon here
#------------------------------------------------------------------------------
addon_metadata = {
        "name": "Example Addon",
        "author": "John Smith",
        "description": "This example draws a sine curve in matplotlib, \
prints to the console, and draws a sine curve in the time domain window.",
        "category": "Plotting"}

#------------------------------------------------------------------------------
# Master run function - put your code in this function
#------------------------------------------------------------------------------
def run(parent_window):
    #------------------------------------------------------------------------------
    # Your addon functions
    #------------------------------------------------------------------------------
    def plot_sine(plot_item, pen):
        plot_item.plot(np.sin(np.arange(100)), pen=pen)
    #--------------------------------------------------------------------------
    # Your addon code:
    #--------------------------------------------------------------------------
    # Addons allow imports
    import matplotlib.pyplot as plt
    import numpy as np
    plt.plot(np.sin(np.arange(100)))

    # Addons allow printing to stdout
    print("Hello World!")

    # Addons can access things in the analysis window
    default_pen = parent_window.CurrentWorkspace.default_pen
    time_domain = parent_window.display_tabwidget.widget(0)
    plot_item = time_domain.time_domain_plot.getPlotItem()
    # And can interact with them
    plot_sine(plot_item, default_pen)