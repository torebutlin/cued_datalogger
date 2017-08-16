==================
Acquisition Module
==================

Recorder Class
--------------

Two modules are created to handle data acquisition from different types of hardware: 
`myRecorder` to handle data from soundcards, and `NIRecorder` to handle data from National Instruments.
Both modules contain a class named **Recorder** derived from the abstract class **RecorderParent** from `RecorderParent` module which provides methods for storing data acquired.

The import convention of the module is **mR** for `myRecorder` and **NIR** for `NIRecorder`.

**RecorderParent** contains methods to initialise a circular buffer, 
initialise a recording array, and initialise a trigger. 
**Recorder** store data acquired from its stream using methods of **RecorderParent** 
as part of its callback routine, such as writing to buffer, writing to recording array, or checking for trigger.
 
The **Recorder** is written in such a way that it could be used in a python console. 
Thus, it is not restricted to be used in the GUI only, but can be used as part of a script.

The **Recorder** class will only output _**raw data**_. Any kind of data processing is done outside of the class.

Any new **Recorder** or equivalent class can be implemented by deriving from the **RecorderParent**, and re-implement the required functions.

Window Layout
------------

The acquisition window consists entirely of one main **QSplitter**, 
in which more **QSplitters**(namely left, middle, and right) are nested within in.
The main splitter is oriented horizontally, while the nested splitters are oriented vertically.
The _Widgets_ written separately as a class are then added to the nested **QSplitters**.

This produces a resizable 'panel' for each _Widget_. 
The good thing about this implementation is some _Widget_ can be hidden away from the user through the code.

Window Function
---------------

The window acts as a central hub to connect the widgets together. 
This is where most slots and signals are connected, meaning most callback functions are implemented here. 
The window also holds the variables for plotting the processed data from the Recorder classes
(i.e. time series data, DFT data, and channel levels). 
A window without any extra _Widget_ added to it would consist only the data plots within the QSplitters, 
and would technically function.

The window contains important variables such as:

* **Recorder**
    * _playing_ - indicate whether the stream is playing
    * _rec_		- Holds the recorder object

* **Plot Data**
    * _timedata_	- Time vector for plotting
    * _freqdata_	- Frequency vector for plotting

* **Plot Colourmaps**
    * _plot_colourmap_	- Colourmap for plotting different channel
    * _level_colourmap_ - Colourmap for indicating channel levels

* **Channel Set**
 	* _live_chanset_	- ChannelSet for holding metadata

* **Time + FFT Plots**
    * _plotlines_		- Holds the lines of time + FFT plots
    * _plot_xoffset_	- Indicate the x offsets of each plot line
    * _plot_yoffset_	- Indicate the y offsets of each plot line
    * _plot_colours_	- Indicate the colours of each plot line
    * _def_colours_		- Holds the default colours of each plot line
    * _sig_hold_		- Indicate whether to 'freeze' a signal plot
  
* **Channel Level Plots**
    * _peakplots_		- Holds all the peak plots of each channel
    * _peak_trace_		- Indicate the value of each trace of the peak of each channel 
    * _peak_decays_		- Indicate the level of decay of each trace
    * _trace_counter_	- Indicate counter of each trace before it decays
    * _trace_countlimit_- Maximum amount of count before the trace decays

Widgets
-------

All _Widgets_ except `PlotWidgets` from `pyqtgraph` are reimplemented as a class of its own. 
They are derived from the abstract class **BaseWidget**
which re-implement function for styling and provide a template for self-written _Widgets_. 
The construction of the UI components is implemented under `initUI()` method. 
No callback functions are done here, unless the callback only affect components within the _Widget_.

* **ChanToggleUI** 	- Toggling the plot of the channels
* **ChanConfigUI** 	- Configure the plot of the channels + metadata
* **DevConfigUI** 	- Configure the recorder
* **StatusUI** 		- Display status and some buttons 
* **RecUI**			- Record data
* **AdvUI**			- Advance channel toggling
