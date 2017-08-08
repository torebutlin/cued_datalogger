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
    
    4.1 Window layout
    
    4.2 Menus


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
* `calibration_factor` - Not implemented yet.
* `transfer_function_type` - either `'displacement'`, `'velocity'`, or `'acceleration'`, indicating what type of transfer function is stored



### 2.3 Graph interaction
    
### 2.4 Import / export


## 3. Datalogger: Acquisition module


## 4. Datalogger: Analysis module
    
### 4.1 Window layout
    
### 4.2 Menus
