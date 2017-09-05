=================
Package structure
=================

.. code::

  cued_datalogger/ (repository)

      cued_datalogger/ (package)

           acquisition/ (subpackage)
               Contains all modules unique to data acquisition and the AcquisitionWindow

           analysis/ (subpackage)
               Contains all modules unique to data analysis and the AnalysisWindow

           api/ (subpackage)
               Contains all modules that provide the general functionality of the DataLogger

           __main__.py (module)
               Functions for running the DataLogger

      docs/
          Contains source code for documentation

      lib/
          Contains additional libraries installed during setup)

      tests/

      setup.py (installation script)
