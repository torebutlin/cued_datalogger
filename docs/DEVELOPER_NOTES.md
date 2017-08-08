# Developer Notes #

These notes are intended to give a comprehensive breakdown of the Datalogger structure.

## Contents ##

1. Infrastructure

	1.1 GUI
	
    1.2 Computation & calculation
    
    1.3 Code style and formatting

2. Datalogger: Universal components

    2.1 Projects
    
    2.2 Data storage and interaction

    2.3 Graph interaction
    
    2.4 Import / export


3. Datalogger: Acquisition module

4. Datalogger: Analysis module

    4.1 Module structure
    
    4.2 Window layout
    
    4.3 Menus


## 1. Infrastructure ##

### 1.1 GUI

#### PyQt5: 

PyQt5 is used as the main engine for the GUI. Each item to display should be created as its own widget.

See the [PyQt5 Reference Guide](http://pyqt.sourceforge.net/Docs/PyQt5/) and the [Qt5 Reference Pages](http://doc.qt.io/qt-5/reference-overview.html) for more.

#### PyQtGraph:

PyQtGraph is used for all graph plotting. Use the built-in `PlotWidget` for creating plots.

See the [PyQtGraph Documentation](http://www.pyqtgraph.org/documentation/).

### 1.2 Computation & calculation
    
#### Numpy:

Numpy is used as the core backend for all of the computation.

See the [NumPy Reference](https://docs.scipy.org/doc/numpy/reference/index.html).

#### SciPy:

Functions to perform common tasks (eg. signal processing, curve fitting) are often found in the SciPy library, and are much easier to use than creating your own.

See the [SciPy Reference](https://docs.scipy.org/doc/scipy-0.19.1/reference/).

### 1.3 Code style and formatting

Please adhere to the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) as closely as possible.


## 2. Datalogger: Universal components

### 2.1 Projects

Not implemented yet.

### 2.2 Data storage and interaction

#### ChannelSets, Channels and DataSets:
The Datalogger uses a three-tier structure for storing data, comprising of ChannelSets, Channels and DataSets. See `channel.py` for further information.

                                               ChannelSet
               _____________________________________|_________________________________...
              /                         |                         |
          Channel 0                  Channel 1                 Channel 2              ...
         /         \                /         \               /         \      
     MetaData    DataSets       MetaData    DataSets       MetaData    DataSets       ...
        |        | | | |           |        | | | |           |        | | | |
       ...         ...            ...         ...            ...         ...          ...

*DataSets*: These are the lowest structure, effectively a vector of values with a name (id\_) and units. 

*Channels*: Normally created from one stream of input data, Channels include the original DataSet, any derived DataSets (eg. frequency spectra, sonogram) and metadata about the channel. They also have methods for getting and setting the attributes of the DataSets.

*ChannelSets*: The main object to interface with, with methods for getting and setting channel and dataset attributes. Each ChannelSet will typically be derived from one set of results or one run of the experiment.

#### Variable names:

For consistency, only the following names are permitted for DataSets and metadata. (\* indicates that the variable is auto-generated)

*DataSets*:
* `time_series` - The raw input time series data
* `time`\*	- Calculated from the sample rate and number of samples
* `frequency`\* - Calculated from the sample rate and number of samples (Hz)
* `omega`\* - Angular frequency (rad), calculated from the sample rate and number of samples
* `spectrum` - The spectral amplitudes given by the Fourier Transform
* `sonogram` - The sonogram array, shape (number of FFTs, frequencies)
* `sonogram_phase` - Phase data associated with the sonogram (rad)

*Metadata*:
* `name` - A human-readable string identifying this channel
* `comments` - A string for any additional comments
* `tags` - A list of tags for quick selection and sorting
* `sample_rate` - The rate (in Hz) that the data was sampled at
* `calibration_factor` - Not implemented yet
* `transfer_function_type` - either `'displacement'`, `'velocity'`, or `'acceleration'`, indicating what type of transfer function is stored


### 2.3 Graph interaction

Pyqtgraph has built-in mouse interactions. 
These interactions are described in [pyqtgraph documentations](http://www.pyqtgraph.org/documentation/mouse_interaction.html). 
Several methods are implemented in [`PlotItem`](http://www.pyqtgraph.org/documentation/graphicsItems/plotitem.html#pyqtgraph.PlotItem) to modify the interaction behaviours, such as setting the panning limits, setting mouse mode, enabling auto-ranging, and more.
    
The interactions can be modified if so desired, especially the right-click context menu. 
This requires subclassing the [`ViewBox`](http://www.pyqtgraph.org/documentation/graphicsItems/viewbox.html) [[source]](http://www.pyqtgraph.org/documentation/_modules/pyqtgraph/graphicsItems/ViewBox/ViewBox.html#ViewBox). 
To modify the context menu, reimplement the 'menu' variable and 'raiseContextMenu()' method. 
After that, initialise a [`PlotItem`](http://www.pyqtgraph.org/documentation/graphicsItems/plotitem.html#pyqtgraph.PlotItem) with the custom ViewBox as its 'viewBox' keyword argument.
    
In addition to mouse interaction, pyqtgraph also included interactive data selection. 
The [documentation](http://www.pyqtgraph.org/documentation/region_of_interest.html) includes a basic introduction. 
    
For our purposes, the [`LinearRegionItem`](http://www.pyqtgraph.org/documentation/graphicsItems/linearregionitem.html#pyqtgraph.LinearRegionItem) 
and [`InfiniteLine`](http://www.pyqtgraph.org/documentation/graphicsItems/infiniteline.html#pyqtgraph.InfiniteLine) from pyqtgraph are used. 
In general, the item is first initialised and added to a PlotItem, Then, its Signal (usually emitted when its position has changed) is connected a method which does something to the data in selected region.
    
Examples by pyqtgraph on graph interaction can be accessed by inputting the line on command line after installing pyqtgraph:
    	
    python -m pyqtgraph.examples
	    
### 2.4 Import / export


## 3. Datalogger: Acquisition module

### 3.1 Recorder Classes

Two classes are created to handle data acquisition from different types of hardware: 
`myRecorder` to handle data from soundcards, and `NIRecorder` to handle data from National Instruments. 
These two classes are derived from the base class `RecorderParent` which provides methods for storing data acquired.

`RecorderParent` contains methods to initialise a circular buffer, 
initialise a recording array, and initialise a trigger. 
`myRecorder` and `NIRecorder` process data acquired from its stream using methods of `RecorderParent` 
as part of its callback routine, such as writing to buffer, writing to recording array, or checking for trigger.
 
The Recorder classes are written in such a way that they could be used in a python console. 
Thus, the classes are not restricted to be used in the GUI only, but can be used as part of a script.

Any new Recorder class can be implemented by deriving from the RecorderParent, and implement the required functions.

### 3.2 Window Layout


## 4. Datalogger: Analysis module

The `analysis` module contains all of the tools used for processing data and modal analysis.

### 4.1 Module structure

Each tool in the `analysis` module is designed so that it could be run independently of the master analysis window, as is its own PyQt widget. This makes it easy to add new tools and slot them into the master window as new tabs.
    
### 4.2 Window layout

Not implemented yet.

The master analysis window has:
* A menubar (see 4.3)
* A set of always-accessible widgets for performing tasks common to all (or most) tools - eg. channel selection
* A TabWidget containing the tools used for analysis

### 4.3 Menus

Not implemented yet.

In the menubar, there are the following menus:
* Project
* Data
* View
* Addons

#### Project menu

Not implemented yet.

This menu contains project-wide options, such as setting project preferences and saving the whole project.

#### Data menu

Not implemented yet.

This menu contains options for importing and exporting data.

#### Addons menu

Not implemented yet.

This menu contains any additional addons that are installed.