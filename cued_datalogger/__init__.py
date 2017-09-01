from cued_datalogger import api
from cued_datalogger import analysis
from cued_datalogger import acquisition
from cued_datalogger import analysis_window, acquisition_window
from cued_datalogger.api import workspace as workspace

import os.path as _path

_PKG_ROOT = _path.abspath(_path.dirname(__file__))

if _path.isfile(_path.join(_PKG_ROOT, 'VERSION')):
    with open(_path.join(_PKG_ROOT, 'VERSION')) as _version_file:
    #with open('VERSION') as _version_file:
        __version__ = _version_file.read()
else:
    __version__ = None
