=================
Package structure
=================

.. code::

  cued_datalogger (repository)
  |
  |-- cued_datalogger (package)
  |    |
  |    |-- acquisition (subpackage)
  |    |   |
  |    |   |-- All modules unique to data acquisition and the AcquisitionWindow
  |    |
  |    |
  |    |-- analysis (subpackage)
  |    |   |
  |    |   |-- All modules unique to data analysis and the AnalysisWindow
  |    |
  |    |
  |    |-- api (subpackage)
  |    |   |
  |    |   |-- All modules that provide the general functionality of the DataLogger
  |    |
  |    |
  |    |
  |    |-- __main__ (module)
  |        |
  |        |-- Functions for running the DataLogger
  |
  |
  |-- docs (source code for documentation)
  |
  |-- lib (contains additional libraries installed during setup)
  |
  |-- tests
  |
  |-- setup.py (installation script)


