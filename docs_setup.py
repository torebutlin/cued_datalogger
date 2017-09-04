from setuptools import setup

def version():
    """Get version number"""
    with open('cued_datalogger/VERSION') as f:
        return f.read()

def readme():
    """Get text from the README.rst"""
    with open('README.rst') as f:
        return f.read()

setup(name='cued_datalogger',
      version=version(),
      description='The CUED DataLogger for acquiring and analysing data',
      long_description=readme(),
      url='https://bitbucket.org/tab53/cued_datalogger/',
      author='Theo Brown, En Yi Tee',
      author_email='tab53@cam.ac.uk, eyt21@cam.ac.uk',
      license='BSD 3-Clause License',
      packages=['cued_datalogger',
                'cued_datalogger/acquisition',
                'cued_datalogger/analysis',
                'cued_datalogger/api'],
      install_requires=['numpy',
                      'scipy',
                      'pyqtgraph',
                      'matplotlib',
                      'PyDAQmx'],
      zip_safe=True,
      include_package_data=True)

