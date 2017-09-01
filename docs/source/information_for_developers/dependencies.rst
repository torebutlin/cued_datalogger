============
Dependencies
============

GUI
---
PyQt5
"""""
PyQt5 is used as the main engine for the GUI. Each item to display should be created as its own widget.

See the `PyQt5 Reference Guide <http://pyqt.sourceforge.net/Docs/PyQt5/>`_ and the `Qt5 Reference Pages <http://doc.qt.io/qt-5/reference-overview.html>`_ for more.

PyQtGraph
"""""""""
PyQtGraph is used for all graph plotting. However, in general plots should be created using the DataLogger's
:class:`~cued_datalogger.api.pyqtgraph_extensions.InteractivePlotWidget`, which provides some additional 
functionality.

See the `PyQtGraph Documentation <http://www.pyqtgraph.org/documentation/>`_.

Matplotlib
""""""""""
Some parts of the DataLogger use Matplotlib for displaying or exporting additional plots.
It should be used as a last resort only when finer control is needed over how the data is displayed 
(for example in contour maps), as Matplotlib is much slower than PyQtGraph, less well integrated into PyQt, and 
does not fit with the styling of the DataLogger.

See the `Matplotlib Documentation <http://matplotlib.org/contents.html>`_.

Computation & calculation
-------------------------    
Numpy
"""""
Numpy is used as the core backend for all of the computation.

See the `NumPy Reference <https://docs.scipy.org/doc/numpy/reference/index.html>`_.


SciPy
"""""
Functions to perform common tasks (eg. signal processing, curve fitting) are often found in the SciPy library, and are much easier to use than creating your own.

See the `SciPy Reference <https://docs.scipy.org/doc/scipy-0.19.1/reference/>`_.

