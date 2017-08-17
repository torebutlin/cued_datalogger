======
README
======

See the `documentation <http://datalogger-docs.readthedocs.io/en/latest/>`_
for more information.

Installation
------------

Installing on Anaconda
^^^^^^^^^^^^^^^^^^^^^^

1. Visit the `Bitbucket repository <https://bitbucket.org/tab53/cued_datalogger/src>`_
and download the ``python3.dll`` file. Place the file in
``/path/to/your/Anaconda/Library/bin/``. (This is so that PyQt works with your
Anaconda install)

2. Install dependecies::

    conda install numpy scipy
    pip install matplotlib pyaudio pydaqmx pyqt5 pyqtgraph

3. Install package (from source)::

    pip install cued-datalogger --no-binary :all:


Installing anywhere else
^^^^^^^^^^^^^^^^^^^^^^^^

1. Install dependencies::

    pip install numpy matplotlib pyaudio pydaqmx pyqt5 pyqtgraph scipy

2. Install package (from wheel)::

    pip install cued-datalogger
