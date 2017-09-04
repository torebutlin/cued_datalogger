======
Addons
======

Addons (extra extension scripts) may be written to extend the functionality of the DataLogger.

Addon structure
---------------

See :mod:`cued_datalogger/addons/example_addon.py` and :mod:`cued_datalogger/addons/addon_template.py` for examples of addons.

Addons must all be structured according to the ``addon_template.py``. That is::

    #cued_datalogger_addon

    #------------------------------------------------------------------------------
    # Put metadata about this addon here
    #------------------------------------------------------------------------------
    addon_metadata = {
            "name": "<name>",
            "author": "<author>",
            "description": "<description>",
            "category": "<category>"}

    #------------------------------------------------------------------------------
    # Master run function - put your code in this function
    #------------------------------------------------------------------------------
    def run(parent_window):
        #--------------------------------------------------------------------------
        # Your addon functions
        #--------------------------------------------------------------------------
        <any user defined functions>
        #--------------------------------------------------------------------------
        # Your addon code:
        #--------------------------------------------------------------------------
        <code goes here>

**Header** (``#cued_datalogger_addon``): This informs the cued_datalogger that this is an addon file.

**Metadata** (:data:`addon_metadata`): Contains information about the addon. Displayed in the Addon Manager. Addons are sorted according to their ``"category"``.

**Main code** (:func:`run`): The actual addon code is all kept under the :func:`run` function. This is the function that is called when the addon is run. Only variables, functions, classes etc defined within :func:`run` will be accessible by the addon, so don't put any code outside of :func:`run`.

In an addon, it is possible to:

* Import modules

* Define functions, classes and variables

* Access widgets, attributes, and methods of the :attr:`parent_window` (eg. to plot data in the Analysis Window, or to do calculations with the current data)

* Display popups and Qt dialog boxes

And probably a lot of other things as well.

Addon Manager
-------------

Addons are normally run through the :class:`~cued_datalogger.api.addons.AddonManager`.

