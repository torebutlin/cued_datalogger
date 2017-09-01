==================
Acquisition Module
==================

==================
Acquisition Module
==================

Recorder Class
--------------
Two modules are created to handle data acquisition from different types of hardware: 
`myRecorder` to handle data from soundcards, and `NIRecorder` to handle data from National Instruments.
Both modules contain a class named **Recorder** derived from the abstract class **RecorderParent** from `RecorderParent` module which provides methods for storing data acquired.

The idea is that **RecorderParent** performs functions that are common across any recorder, while the derived class is responsible to set up the aquisition device and acquire data for **RecorderParent**, as there may be differences in these methods, as demonstrated by `myRecorder` and `NIRecorder`.

The import convention of the module is **mR** for `myRecorder` and **NIR** for `NIRecorder`.

**RecorderParent** contains methods to initialise a circular buffer, 
initialise a recording array, and initialise a trigger. 
**Recorder** store data acquired from its stream using methods of **RecorderParent** 
as part of its callback routine, such as writing to buffer, writing to recording array, or checking for trigger.
 
The **Recorder** is written in such a way that it could be used in a python console. 
Thus, it is not restricted to be used in the GUI only, but can be used as part of a script.

The **Recorder** class will only output _**raw data**_ in binary16, scaled to some value. Any kind of data processing is done outside of the class.

Any new **Recorder** or equivalent class can be implemented by deriving from the **RecorderParent**, and re-implement the required functions.

Interaction Between Acquisition and Analysis Windows
----------------------------------------------------
The acquisition window designed to be self-contained, meaning most of the time changes stay within acquisition window, and ditto for analysis window.
The only time acquisition window interacts with the analysis window is when a recorded data has finished processing. The acquisition window merely makes a copy of its own **ChannelSet** and replace the one in analysis window with this.
Analysis window does not interact with the acquisition window in any way, except opening up the window.

Window Function
---------------
The window acts as a central hub to connect the widgets and the live graphs together. 
This is where all slots and signals are connected. So, callback functions are self-contained in the respective Widget classes, emitting signals when needed. This is make the code much more readible, and make the process of adding extra widgets easier.  

Widgets
-------
All _Widgets_  are reimplemented as a class of its own. 
They are derived from the abstract class **BaseWidget** which re-implement function for styling and provide a template for self-written _Widgets_. 
The construction of the UI components is implemented under `initUI()` method. 
Most callback functions are done here, emitting signals to interact with other widgets, if need be.

* **ChanToggleUI** 	- Toggling the plot of the channels
* **ChanConfigUI** 	- Configure the plot of the channels + metadata
* **DevConfigUI** 	- Configure the recorder
* **StatusUI** 		- Display status and some buttons 
* **RecUI**			- Record data

Live Graphs
-------
All _Live Graphs_  are reimplemented as a class of its own. 
They are derived from the abstract class **LiveGraph** which re-implements `pyqtgraph` **PlotWidget**, along with implement functions to set the plot appearances. 
The construction of the graph is implemented under `__init__` method. 
Similar to the widgets, most callback functions are done here, emitting signals to interact with other widgets, if need be.

* **TimeLiveGraph** 	- Plot the data in time domain
* **FreqLiveGraph** 	- Plot the data in frequenct domain
* **LevelsLiveGraph** 	- Plot the peaks of the data

Updating the graph is done through a **QTimer**, instead of signal and slot method, although the method for the latter still exist within the code commented out. This is because QTimer has a better performance in live updating at higher amount of data, even though there is a very small chance of discontinuity in the plot due to the mismatch in the time to acquire data in the buffer and time to plot those data. This, however, does not affect the recording process as data acquired is immediately store in an array within the **Recorder** class