# Developer Notes #

These notes are intended to give a comprehensive breakdown of the Datalogger structure.

## Contents ##

1. Infrastructure

	1.1 GUI
	
    1.2 Computation & calculation
    
    1.3 Code style and formatting

2. Datalogger: Universal components

    2.1 Data storage and interaction

    2.2 Graph interaction
    
    2.3 Import / export


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

### 2.1 Data storage and interaction

### 2.2 Graph interaction
    
### 2.3 Import / export


## 3. Datalogger: Acquisition module


## 4. Datalogger: Analysis module
    
### 4.1 Window layout
    
### 4.2 Menus
