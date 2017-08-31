================
Window Structure
================

The AnalysisWindow is comprised of three main widgets and a menu bar.

.. figure:: analysis_window_labeled.png
   :width: 100%


Menu bar
--------
Currently the menu bar is only a placeholder, it has no functionality.

The menu bar will be the place for functions that are not tools for interacting with or affecting
data and tools that will not be used regularly during normal DataLogger operation. For example,  
workspaces will be loaded, configured and saved from the menu bar, as this operation will normally
only be performed once per session.


Local toolbox
-------------
Instance of: :class:`~datalogger.api.toolbox.MasterToolbox`

The local toolbox contains all the operations and conversions that are associated with the widget
that is currently showing in the display TabWidget. If something changes the channel data, or
changes the way that the data is viewed, then it goes in the local toolbox.

Functions in the local toolbox should be grouped into tabs (eg. 'Conversion', 'Peaks')
and then into grouped boxes within a tab (eg. 'Transfer function conversion options', 'Sonogram
conversion options').


Display TabWidget
-----------------
Instance of: :class:`datalogger.analysis_window.AnalysisDisplayTabWidget`, which
inherits :class:`PyQt5.QtWidgets.QTabWidget`

This is the central widget for the AnalysisWindow, where graphs, data, and results are displayed.
For each section of the analysis window (time domain, sonogram, etc) there is one
:class:`~PyQt5.QtWidgets.QWidget` that is created for display, which is the focal point of that
section.

In general it is simply an :class:`~datalogger.api.pyqtgraph_extensions.InteractivePlotWidget`, 
but it can contain other widgets (eg. :class:`~datalogger.analysis.circle_fit.CircleFitWidget`)
if they are absolutely necessary to smooth operation (such as the results tree in the CircleFitWidget).

The user should not have to jump around between the toolboxes and the display TabWidget to view
their results. Operations are kept in the toolboxes; the display TabWidget is for data interaction
and visualisation.

.. note:: Currently no decision has been made about how future modal analysis tools will be added
  to the DataLogger. Will the Circle Fit tab remain solely for circle fitting or will it become 
  a Modal Analysis tab containing options for circle fitting, RFP fitting, etc?


Global toolbox
--------------
Instance of: :class:`~datalogger.api.toolbox.MasterToolbox`

The global toolbox contains operations that have a universal effect, and are not limited to one
specific analysis widget. Examples include interacting with channel selection and metadata, or running
addons.
