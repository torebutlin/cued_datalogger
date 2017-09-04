=================
Quick start guide
=================

Install the DataLogger by following the relevant instructions below.

Then run the DataLogger from a command line using any of::

    cued_datalogger_run

    cued_datalogger_dbg

    python -m cued_datalogger


See the `documentation <http://cued-datalogger.readthedocs.io/en/latest/>`_
for more information.


Installation
------------

Installing on Windows
^^^^^^^^^^^^^^^^^^^^^
#. Download and install `Anaconda / Miniconda <https://www.continuum.io/downloads>`_.

#. Check that your Anaconda is using the latest version of ``pip``. In an Anaconda Prompt, type::

    conda install pip

#. Install ``cued_datalogger`` using ``pip``::

    pip install cued_datalogger


Installing on OS X
^^^^^^^^^^^^^^^^^^
#. Install ``portaudio`` with ``brew`` \*::

    brew install portaudio

#. Install ``cued_datalogger`` using ``pip`` (from Terminal or from Anaconda Prompt or wherever)::

    pip install cued_datalogger

\* If you do not have brew installed, install `Homebrew <https://brew.sh/>`_ then permit it to run with ``xcode-select --install``


Installing on Linux
^^^^^^^^^^^^^^^^^^^

#. Install the ``portaudio`` development headers using your package manager.

    **Debian / Ubuntu**::

        sudo apt install libportaudio2 portaudio19-dev


    **CentOS**::

        yum install portaudio portaudio-devel


#. Install ``cued_datalogger`` using ``pip``::

    pip install cued_datalogger


