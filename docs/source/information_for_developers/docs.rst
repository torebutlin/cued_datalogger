=============
Documentation
=============

The documentation for the DataLogger is stored in the ``docs`` directory in the git repository.
It is built using `Sphinx <http://www.sphinx-doc.org/en/stable/>`_.
For tutorials on writing documentation using Sphinx, see 
`here <http://restructuredtext.readthedocs.io/en/latest/sphinx_tutorial.html>`_
and 
`here <https://pythonhosted.org/an_example_pypi_project/sphinx.html>`_.


Writing documentation
---------------------
For the majority of the documentation, use Sphinx's `autodoc functionality <http://www.sphinx-doc.org/en/stable/ext/autodoc.html>`_.


Compiling documentation
-----------------------

Local version
"""""""""""""
To create a local version of the documentation (eg. for checking that the documentation compiles)
navigate to the top-level ``docs/`` directory and run::

  make html

The built version should appear in ``docs/build/html``.

ReadTheDocs version
"""""""""""""""""""
`ReadTheDocs <https://readthedocs.org/>`_ is a documentation hosting website. The DataLogger
documentation can be found at `cued_datalogger.readthedocs.io <http://cued-cued_datalogger.readthedocs.io>`_.

Currently the process for uploading the DataLogger documentation to ReadTheDocs is quite complex
and messy, due to issues with package dependencies. In an attempt to simplify things, there is an
alternative ``setup.py`` script (``docs_setup.py``) for use when compiling a new version of the 
documentation. This is not a particularly robust way of doing things, but it seems to work.

.. note:: There are two versions of ``setup.py`` - one for use when compiling the documentation  
  (``docs_setup.py``), which does not install any dependencies, and one for use when compiling the 
  package (``package_setup.py``), which installs dependencies and performs various checks (eg. that 
  Anaconda has the Python 3 ``.dll`` file in Windows. Before trying to compile, check that the
  contents of ``setup.py`` are the same as the appropriate setup script.

The ReadTheDocs project for the DataLogger is currently set up to install the package in a conda
environment (see `ReadTheDocs Conda Support <http://docs.readthedocs.io/en/latest/conda.html>`_),
which helps to eliminate some of the dependency problems.

.. warning:: This feature of ReadTheDocs is in Beta, so there will probably be some issues.

The ReadTheDocs project is currently set to track the ``docs`` branch of the Git repository.

To build a new version of the documentation:

  #. Check that the ``setup.py`` file in the repository is identical to ``docs_setup.py``.

  #. Navigate to `the ReadTheDocs project homepage <https://readthedocs.org/projects/cued_datalogger/>`_.

  #. Under **Build a version**, click *Build*. You can check the progress of the build in the *Builds*
     tab.

  #. Click *View Docs* to view the documentation. If lots of the documentation is missing, the
     ``autodoc`` directives have probably failed, suggesting that the build did not successfully install
     the ``cued_datalogger`` module. Check the *Builds* tab in the project homepage.

