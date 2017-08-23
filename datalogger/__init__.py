import api
import analysis
import acquisition
import analysis_window, acquisition_window
#from datalogger.api import workspace as workspace
from api import workspace as workspace

import os.path as _path

_PKG_ROOT = _path.abspath(_path.dirname(__file__))

with open(_path.join(_PKG_ROOT, 'VERSION')) as _version_file:
#with open('VERSION') as _version_file:
    __version__ = _version_file.read()


    