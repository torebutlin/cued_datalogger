from datalogger import api
from datalogger import analysis
from datalogger import acquisition
from datalogger import analysis_window, acquisition_window
#from datalogger.api import workspace as workspace
from datalogger.api import workspace as workspace

import os.path as _path

_PKG_ROOT = _path.abspath(_path.dirname(__file__))

if _path.isfile(_path.join(_PKG_ROOT, 'VERSION')):
    with open(_path.join(_PKG_ROOT, 'VERSION')) as _version_file:
    #with open('VERSION') as _version_file:
        __version__ = _version_file.read()
else:
    __version__ = None