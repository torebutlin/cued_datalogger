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
documentation can be found at `cued-datalogger.readthedocs.io <http://cued-datalogger.readthedocs.io>`_.

The ReadTheDocs project is currently set to track the ``docs`` branch of the Git repository.

To build a new version of the documentation:

  #. Navigate to `the ReadTheDocs project homepage <https://readthedocs.org/projects/cued_datalogger/>`_.

  #. Under **Build a version**, click *Build*. You can check the progress of the build in the *Builds*
     tab.

  #. Click *View Docs* to view the documentation. If lots of the documentation is missing, the
     ``autodoc`` directives have probably failed, suggesting that the build did not successfully install
     the ``cued_datalogger`` module. Check the *Builds* tab in the project homepage.

