==================
Package management
==================

The ``cued_datalogger`` package is installable from PyPI (the Python Package Index) via ``pip``
(see :doc:`quickstart` for more information).

This section of documentation attempts to describe how the package was set up.


Compiling the package
---------------------
Python provides a package for creating packages, ``setuptools``. The ``setup.py`` script uses
``setuptools`` to compile the code into a Python package.

.. note:: There are two versions of ``setup.py`` - one for use when compiling the documentation
  (``docs_setup.py``), which does not install any dependencies, and one for use when compiling the
  package (``package_setup.py``), which installs dependencies and performs various checks (eg. that
  Anaconda has the Python 3 ``.dll`` file in Windows). Before trying to compile, check that the
  contents of ``setup.py`` are the same as the appropriate setup script.

To compile the package and upload the new version to PyPI, run::

  python setup.py sdist upload

This runs the setup script to create a source code distribution (tarball) and uploads the distribution to PyPI.

.. warning:: Do not attempt to create a Python wheel for the package.
  There are some issues with using the ``install_requires`` parameter
  from ``setuptools``. ``install_requires`` installs dependencies using the PyPI source
  distribution. For some packages (PyQt5) there is no source distribution available.
  To get round this, the current ``setup.py`` script installs Python wheels (binaries)
  manually for all the dependencies. As there are no packages in ``install_requires``,
  compiling a binary wheel from the setup script will not result in an distribution with the
  necessary dependencies.


Installing a local developer's version
--------------------------------------
If you have downloaded the Git repository and made changes to files, you need to locally install your
changed version so that all of the module imports work correctly.

Navigate to the Git repository and run ``pip install -e .`` to get a developer's version of the
package installed locally.
