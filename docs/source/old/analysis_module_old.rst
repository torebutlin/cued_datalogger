===============
Analysis Module
===============
The `analysis` module contains all of the tools used for processing data and modal analysis.

Module structure
----------------

Each tool in the `analysis` module is designed so that it could be run independently of the master analysis window, as is its own PyQt widget. This makes it easy to add new tools and slot them into the master window as new tabs.
    
Window layout
-------------

Not implemented yet.

The master analysis window has:

* A menubar (see 4.3)
* A widget containing the tools used for analysis on the left ('Toolbox')
* A TabWidget to display the results of the different tools in the middle for different type of analysis
* A set of always-accessible widgets for performing tasks common to all (or most) tools - eg. channel selection, on the right ('Global Toolbox')

Both the left and right widgets are custom tabwidget, written to be collapsible tabs. The idea of this is to hide away the tools to allow maximum view of the results in the middle, while having the tabs visible to the user, allowing them to open up the tools.

Read on 4.4 for the implementation

Menus
-----
A simple menu is implemented by subclassing **QMenu** and adding **QActions** or another **QMenu** to the **QMenu**. Then, the subclassed **QMenu** can be added to the Main Window's _menubar_. 
In the menubar, there are the following menus:

* Project - _ProjectMenu_ class

* Data - _DataMenu_ Class

* View - _ViewMenu_ Class


Project menu
""""""""""""

Not implemented yet.

This menu contains project-wide options, such as setting project preferences and saving the whole project.

Data menu
"""""""""

Not implemented yet.

This menu contains options for importing and exporting data.


Collapsible Tabs
----------------
The collapsible left and right widgets mentioned in 4.2 is a custom class **CollapsingSideTabWidget** that subclasses **QSplitter**. 

The widget is then mainly made up of two widgets: **QStackedWidget** and **QTabBar**. **QStackedWidget** is to contain all the analysis tools but showing one tool at a time, while **QTabBar** shows all the tools available and switch the respective tool when clicked on.

Animation is implemented to take advantage of the **QSplitter** resizing capabilities, which involves a third empty widget.

Tools
-----
Currently, the idea is each type of analysis has its own set of tools, _e.g. time series analysis and frequency series analysis has distinct set of tools_. Thus, when switching tabs for different analysis in the middle widget, the left tool widget will switch to the relevant tools.

An _abstract_ class **BaseTools** is written to streamline the process of addi ng and display tools in the collapsible tabs. This merely contains the tools and the label to the respective analysis.

To properly utilise this class, it must be derived and redefine the `initTools` method. Under here, a tool can be written as a **QWidget**, and then added using the method `add_tool`, supplying a name for that tool.

A variable  named _parent_ is provided to allow any signal and slots to be made to the main window. 

Four **Tools** are created:
* __TimeTools__: Tools for time series analysis
* __FreqTools__: Tools for frequency series analysis
* __ModalTools__: Tools for modal analysis
* __GlobalTools__: Tools that is common for all analysis, this is added to the right widget mentioned before

A new **Tools** class can be derived if the tool does not belong to any of the above categories, but that new class must be added to the `prepare_tools` method in the Main Window, and check that it opens for the correct analysis.
