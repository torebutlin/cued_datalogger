======
README
======

See the `documentation <http://datalogger-docs.readthedocs.io/en/latest/>`_
for more information.

Installation
------------


Installing on Windows
^^^^^^^^^^^^^^^^^^^^^
#. Download and install `Anaconda / Miniconda <https://www.continuum.io/downloads>`_.  
  
#. Visit the `Bitbucket repository <https://bitbucket.org/tab53/cued_datalogger/src>`_ and download the ``python3.dll`` file.   

#. Place the file in ``/path/to/your/Anaconda/Library/bin/``. This is so that PyQt5.9 works with your Anaconda install.  

#. Follow the steps for "Installing on Anaconda" below.  


Installing on OS X
^^^^^^^^^^^^^^^^^^ 
#. Install ``portaudio`` with ``brew`` \*::

    brew install portaudio

#. If you are using Anaconda, follow the steps for "Installing on Anaconda" below. Otherwise, install ``cued-datalogger`` using ``pip``::

    pip install cued-datalogger
    
\* If you do not have brew installed, install `Homebrew <https://brew.sh/>`_ then permit it to run with ``xcode-select --install``


Installing on Anaconda
^^^^^^^^^^^^^^^^^^^^^^
#. Install dependecies::

    conda install numpy scipy
    pip install matplotlib pyaudio pydaqmx pyqt5 pyqtgraph

#. Install ``cued-datalogger`` using ``pip``::

    pip install cued-datalogger --no-deps


*Explanation*:

*Packages that are installed in both* ``conda`` *and* ``pip`` *can cause problems, 
so everything that can be is installed with* ``conda``. *This means that* ``pip`` 
*must be told not to install any of the* ``cued-datalogger`` *dependencies 
with the* ``--no-deps`` *flag.*


Installing on Linux (without Anaconda)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#. Install the ``portaudio`` development headers using your package manager.

    **Debian / Ubuntu**::

        sudo apt install libportaudio2 portaudio19-dev


    **CentOS**::

        yum install portaudio portaudio-devel


#. Install ``cued-datalogger`` using ``pip``::

    pip install cued-datalogger

 