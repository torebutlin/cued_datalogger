from setuptools import setup
from sys import version, platform
from subprocess import check_output
from os.path import isfile
from shutil import copyfile

def readme():
    """Get text from the README.rst"""
    with open('README.rst') as f:
        return f.read()

# Check if the python installation is from Anaconda - if it is, we need to
# move the python3.dll
print("Checking for Anaconda install...")
if "Anaconda" in version or "Continuum" in version:
    print("Anaconda install found.")
    print("Checking operating system...")
    if platform.startswith('linux'):
        print("Operating system: Linux")
        python_conda_path = check_output(['which', 'python']).decode("utf-8")
        print("Not implemented yet.")
        raise OSError("DataLogger not configured for this OS.")
    elif platform.startswith('darwin'):
        print("Operating system: Mac OS")
        python_conda_path = check_output(['which', 'python']).decode("utf-8") 
        raise OSError("DataLogger not configured for this OS.")
    elif platform.startswith('win'):
        print("Operating system: Windows")
        python_conda_path = check_output(['where', 'python']).decode("utf-8")
        path_for_dll = python_conda_path.split('python')[0]
        copyfile('./python3.dll', path_for_dll)
    else:
        print("Unknown operating system found. Aborting.")
        raise OSError("DataLogger not configured for this OS.")
else:
    print("Anaconda not found.")
    

setup(name='CUED_DataLogger',
      version='0.0.13',
      description='The CUED DataLogger for acquiring and analysing data',
      long_description=readme(),
      url='https://bitbucket.org/tab53/cued_datalogger/',
      author='Theo Brown, En Yi Tee',
      author_email='tab53@cam.ac.uk, eyt21@cam.ac.uk',
      license='BSD 3-Clause License',
      packages=['datalogger',
                'datalogger/acquisition',
                'datalogger/analysis',
                'datalogger/bin'],
      install_requires=[
              'PyQt5>=5.9',
              'numpy>=1.11.3',
              'scipy>=0.18.1',
              'pyqtgraph>=0.9.10',
              'matplotlib>=1.5.1',
              'PyDAQmx>=1.3.2',
              'pyaudio>=0.2.11'],
      entry_points={
        'console_scripts': ['DataLogger_cmd = datalogger.__main__:full'],
        'gui_scripts': ['DataLogger = datalogger.__main__:full']},  
      zip_safe=True,
      include_package_data=True)
