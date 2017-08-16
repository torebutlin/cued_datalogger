====================
Universal Components
====================

Workspaces
----------

Workspaces provide a way for the user to set up, save, and load customised configurations of the DataLogger. In this way, specific workspaces can be created (eg. for undergraduate teaching) to limit the functionality available.

The ``.wsp`` format
"""""""""""""""""""
Workspaces are saved in a unique format, ``.wsp``. WSP files are effectively a list of the settings for the DataLogger, allowing the user to enable add ons, set display options and suchlike. An example of a `.wsp` file can be found in ``tests/test_workspace.wsp``.

*Rules for a ``.wsp`` file*:

* Only settings defined in the ``Workspace`` class are permitted (see below)

* Settings that are strings (eg. workspace names, paths) must use single quotes `''`

* Either boolean (``False`` / ``True``) or integer (``0`` / ``1``) values may be used for flags. It is recommended to use integers, for clarity

* The only form of line that will be interpreted as a setting is ``variable_name=variable_value`` where ``variable_value`` can either be a string (``variable_name='example'``), integer ``variable_name=1``, or boolean (``variable_name=False``)

* Hence comments may be inserted into the ``.wsp`` file. It is recommended to use Python comment syntax (``#`` and ``""" """``)

The ``Workspace`` class
"""""""""""""""""""""""
The ``Workspace`` class stores the workspace attributes and has methods for saving, loading, configuring, and displaying the workspace settings. Normally, a ``CurrentWorkspace`` instance is initiated that will store the current settings and all the workspace functionality will be accessed through the ``CurrentWorkspace``.


Data storage and interaction
-----------------------------
ChannelSets, Channels and DataSets
""""""""""""""""""""""""""""""""""

The Datalogger uses a three-tier structure for storing data, comprising of ChannelSets, Channels and DataSets. See ``channel`` for further information.

![ChannelSet tree image](channel_structure.png)

*DataSets*: These are the lowest structure, effectively a vector of values with a name (``id_``) and units. 

*Channels*: Normally created from one stream of input data, Channels include the original DataSet, any derived DataSets (eg. frequency spectra, sonogram) and metadata about the channel. They also have methods for getting and setting the attributes of the DataSets.

*ChannelSets*: The main object to interface with, with methods for getting and setting channel and dataset attributes. Each ChannelSet will typically be derived from one set of results or one run of the experiment.

Variable names
""""""""""""""

For consistency, only the following names are permitted for DataSets and metadata. (\* indicates that the variable is auto-generated)

*DataSets*:

* ``time_series`` - The raw input time series data

* ``time``\*	- Calculated from the sample rate and number of samples

* ``frequency``\* - Calculated from the sample rate and number of samples (Hz)

* ``omega``\* - Angular frequency (rad), calculated from the sample rate and number of samples

* ``spectrum`` - The complex spectrum given by the Fourier Transform

* ``sonogram`` - The complex sonogram array, with shape (number of FFTs, frequencies)

* ``sonogram_frequency``\* - The frequency bins (Hz) used in plotting the sonogram. Not implemented yet, but will be calculated from the sonogram parameters.

* ``sonogram_omega``\* - The frequency bins (rad) used in plotting the sonogram. Not implemented yet, but will be calculated from the sonogram parameters.

*Metadata*:

* ``name`` - A human-readable string identifying this channel

* ``comments`` - A string for any additional comments

* ``tags`` - A list of tags for quick selection and sorting

* ``sample_rate`` - The rate (in Hz) that the data was sampled at

* ``calibration_factor`` - Not implemented yet

* ``transfer_function_type`` - either ``None``, ``'displacement'``, ``'velocity'``, or ``'acceleration'``, indicating what type of transfer function is stored


Graph interaction
-----------------

Pyqtgraph has built-in mouse interactions. 
These interactions are described in `pyqtgraph documentations <http://www.pyqtgraph.org/documentation/mouse_interaction.html>`_. 
Several methods are implemented in `PlotItem <http://www.pyqtgraph.org/documentation/graphicsItems/plotitem.html#pyqtgraph.PlotItem>`_ to modify the interaction behaviours, such as setting the panning limits, setting mouse mode, enabling auto-ranging, and more.
    
The interactions can be modified if so desired, especially the right-click context menu. 
This requires subclassing the `ViewBox <http://www.pyqtgraph.org/documentation/graphicsItems/viewbox.html>`_

To modify the context menu, reimplement the 'menu' variable and 'raiseContextMenu()' method. 
After that, initialise a `PlotItem <http://www.pyqtgraph.org/documentation/graphicsItems/plotitem.html#pyqtgraph.PlotItem>`_ with the custom ViewBox as its 'viewBox' keyword argument.
    
In addition to mouse interactions, pyqtgraph also included interactive data selection. 
The `documentation <http://www.pyqtgraph.org/documentation/region_of_interest.html>`_ includes a basic introduction. 
    
For our purposes, the `LinearRegionItem <http://www.pyqtgraph.org/documentation/graphicsItems/linearregionitem.html#pyqtgraph.LinearRegionItem>`_ and `InfiniteLine <http://www.pyqtgraph.org/documentation/graphicsItems/infiniteline.html#pyqtgraph.InfiniteLine>`_ from pyqtgraph are used. 
In general, the item is initialised and added to a PlotItem, Then, its Signal (usually emitted when its position has changed) is connected to a method which does something to the data in the selected region.
    
Examples by pyqtgraph on graph interaction can be accessed by inputting the line on command line after installing pyqtgraph::
    	
    python -m pyqtgraph.examples
		    
Import / export
-----------------
Not implemented yet.

There will be options for importing and exporting from:

* ``.mat`` files from the old Datalogger

* CSV, Excel, spreadsheet, text files etc

* Any custom file types (eg. George Stoppani)

* ``.wav``, ``.mp3`` and other audio filetypes.

History Tree
------------
Not implemented yet.

There will be some exciting and ideally simple way of undoing operations, perhaps using a PhotoShop/GIMP-style history tree that stores what operations have been performed and offers the ability to revert back to a specific point.

