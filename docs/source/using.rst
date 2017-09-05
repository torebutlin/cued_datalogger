====================
Using the DataLogger
====================

The DataLogger is designed for the following directory structure::

  ..
  name_of_lab/

      addons/
          lab_addon1.py
          lab_addon2.py

      lab_workspace_file.wsp

In normal use, you would navigate to the ``name_of_lab/`` folder and then run::

    cued_datalogger -w lab_workspace_file.wsp

This launches the DataLogger and loads the ``lab_workspace_file``. The DataLogger
will then automatically find and include all the addons found in the ``addons/``
folder.

It may be useful to read the documentation on :doc:`/api_reference/infrastructure/workspace`
and :doc:`/api_reference/infrastructure/channel` to familiarise yourself with how
the DataLogger works.

