==========
Workspaces
==========

Workspaces provide a way for the user to set up, save, and load customised configurations of the DataLogger. In this way, specific workspaces can be created (eg. for undergraduate teaching) to limit the functionality available.

The ``.wsp`` format
-------------------

Workspaces are saved in a unique format, ``.wsp``. WSP files are effectively a list of the settings for the DataLogger, allowing the user to enable add ons, set display options and suchlike.
An example of a `.wsp` file can be found in ``tests/test_workspace.wsp``.

*Rules for a ``.wsp`` file*:

* Only settings defined in the ``Workspace`` class are permitted (see below)

* Settings that are strings (eg. workspace names, paths) must use single quotes `''`

* Either boolean (``False`` / ``True``) or integer (``0`` / ``1``) values may be used for flags. It is recommended to use integers, for clarity

* The only form of line that will be interpreted as a setting is ``variable_name=variable_value`` where ``variable_value`` can either be a string (``variable_name='example'``), integer ``variable_name=1``, or boolean (``variable_name=False``)

* Hence comments may be inserted into the ``.wsp`` file. It is recommended to use Python comment syntax (``#`` and ``""" """``)


Running the DataLogger with a Workspace
---------------------------------------

To specify a Workspace when running the DataLogger, use::

    cued_datalogger -w /path/to/workspace.wsp


The ``Workspace`` class
-----------------------

.. autoclass:: cued_datalogger.api.workspace.Workspace
  :members:

Widgets
-------
Not implemented yet.
