======
Addons
======

Addons (extra extension scripts)  may be written to extend the functionality of the DataLogger.

Addon structure
^^^^^^^^^^^^^^^
File structure
""""""""""""""
See ``cued_datalogger/addons/example_addon.py`` and ``cued_datalogger/addons/addon_template.py`` for examples of addons.

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
        #------------------------------------------------------------------------------
        # Your addon functions
        #------------------------------------------------------------------------------
		<any user defined functions>
        #--------------------------------------------------------------------------
        # Your addon code:
        #--------------------------------------------------------------------------
        <code goes here>

*Header* (``#cued_datalogger_addon``): This informs the cued_datalogger that this is an addon file.

*Metadata* (``addon_metadata``): Contains information about the addon. Displayed in the Addon Manager. Addons are sorted according to their ``"category"``.

*Main code* (``run``): The actual addon code is all kept under the `run` function. This is the function that is called when the addon is run. Only variables, functions, classes etc defined within the ``run`` function will be accessible by the addon, so don't put any code outside of `run`.

What addons can do
""""""""""""""""""
In an addon, it is possible to:

* Import modules

* Define functions, classes and variables

* Access widgets, attributes, and methods of the ``parent_window`` (eg. to plot data in the Analysis Window, or to do calculations with the current data)

* Display popups and Qt dialog boxes

And probably a lot of other things as well.

Addon Manager
^^^^^^^^^^^^^
The Addon Manager provides a widget for loading, selecting, and running addons. It also has a console for displaying the addon output.

The Addon Manager is included in the Global Toolbox of the Analysis Window.

Creating addons
"""""""""""""""
Not implemented yet. It would be nice to have some way of creating addons from within the manager.

Loading addons
""""""""""""""
Addons located in ``CurrentWorkspace.path/addons/`` will be automatically discovered and added to the AddonManager. Other addons may be loaded from within the addon manager, using the ``Load Addon`` button, which opens up a file explorer. Multiple addons can be added simultaneously in this way.

Running addons
""""""""""""""
Addons are run using the `Run Selected` button in the addon manager, or by double clicking them in the tree. When the addon is run, a new ``QThread`` is created that routes ``stdout`` to the ``QTextEdit`` console widget in the manager. This means that anything the addon prints to ``stdout`` will be displayed in the console, so `print` calls can be used in the addon as normal to display results in the console widget.

Note that the thread will route everything that goes to ``stdout`` to the console widget, including things printed from the main window.
