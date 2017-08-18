from . import api
from .api import workspace as workspace
from . import analysis
from . import acquisition

import os.path

_PKG_ROOT = os.path.abspath(os.path.dirname(__file__))


with open(os.path.join(_PKG_ROOT, 'VERSION')) as version_file:
    __version__ = version_file.read()

# Conceal modules that we don't want the user to see by deleting the 
# local references
del os
del version_file

    