===========
Development
===========

GUI
---
PyQt5
"""""

PyQt5 is used as the main engine for the GUI. Each item to display should be created as its own widget.

See the `PyQt5 Reference Guide <http://pyqt.sourceforge.net/Docs/PyQt5/>`_ and the `Qt5 Reference Pages <http://doc.qt.io/qt-5/reference-overview.html>`_ for more.

PyQtGraph
"""""""""

PyQtGraph is used for all graph plotting. Use the built-in :class:`PlotWidget` for creating plots.

See the `PyQtGraph Documentation <http://www.pyqtgraph.org/documentation/>`_.


Computation & calculation
-----------------------------    
Numpy
"""""

Numpy is used as the core backend for all of the computation.

See the `NumPy Reference <https://docs.scipy.org/doc/numpy/reference/index.html>`_.


SciPy
"""""

Functions to perform common tasks (eg. signal processing, curve fitting) are often found in the SciPy library, and are much easier to use than creating your own.

See the `SciPy Reference <https://docs.scipy.org/doc/scipy-0.19.1/reference/>`_.


Code style and formatting
-------------------------
Please adhere to the `Google Python Style Guide <https://google.github.io/styleguide/pyguide.html>`_ as closely as possible. 
