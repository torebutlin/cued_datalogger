from setuptools import setup
import sys
import subprocess
from os.path import isfile

def version():
    """Get version number"""
    with open('datalogger/VERSION') as f:
        return f.read()

def readme():
    """Get text from the README.rst"""
    with open('README.rst') as f:
        return f.read()

# Check if the python installation is from Anaconda - if it is, we need to
# move the python3.dll into the Anaconda Library bin folder so that PyQt5.9 runs
print("Checking for Anaconda installation...")

if "Anaconda" in sys.version or "Continuum" in sys.version:
    print("Anaconda installation found.\n")

    if sys.platform.startswith("win"):
        print("Operating system: Windows.\n")
        print("Searching for python3.dll...")

        python_dll_found = False

        # Find where the python executables are
        python_path = subprocess.check_output(['where', 'python']).decode("utf-8")
        python_path = python_path.split()

        conda_paths = []

        # Process these to get just the anaconda paths
        for location in python_path:
            conda_path = location.split('python')[0]
            conda_path = conda_path.replace("\\", '/')
            conda_paths.append(conda_path)

        for location in conda_paths:
            if isfile(location + "Library/bin/python3.dll"):
                print("python3.dll found in " + location
                      + "Library/bin/python3.dll")
                python_dll_found = True
                break

        if python_dll_found:
            print("python3.dll file found, so DataLogger will work "
                  "with this Anaconda installation.")
            print("Continuing to setup...\n")
        else:
            print("Error: No python3.dll file found, so DataLogger will NOT "
                  "work with this Anaconda installation.")
            print("#########################################################\n"
                  "Please download a python3.dll file \n"
                  "(eg. from bitbucket.org/tab53/cued_datalogger/src)\n"
                  "and copy the python3.dll file to the Anaconda Library \n"
                  "binary folder (eg. C:\ProgramData\Anaconda3\Library\bin). \n"
                  "Then attempt to install cued-datalogger again. \n"
                  "#########################################################")
            exit(1)

else:
    print("Anaconda not found. [OK]")
    print("Continuing to setup...\n")


setup(name='cued-datalogger',
      version=version(),
      description='The CUED DataLogger for acquiring and analysing data',
      long_description=readme(),
      url='https://bitbucket.org/tab53/cued_datalogger/',
      author='Theo Brown, En Yi Tee',
      author_email='tab53@cam.ac.uk, eyt21@cam.ac.uk',
      license='BSD 3-Clause License',
      packages=['datalogger',
                'datalogger/acquisition',
                'datalogger/analysis',
                'datalogger/api'],
      # TODO
      # If you include this in the setup code, when it tries to install
      # itself in an Anaconda environment, a lot of things break. Fix this.
      # (currently the workaround is telling the user to install some stuff)
      install_requires=[
                      'PyQt5>=5.9',
                      'numpy>=1.11.3',
                      'scipy>=0.18.1',
                      'pyqtgraph>=0.9.10',
                      'matplotlib>=1.5.1',
                      'PyDAQmx>=1.3.2',
                      'pyaudio>=0.2.11'],
      entry_points={
        'console_scripts': ['DataLogger_dbg = datalogger.__main__:run_datalogger_full'],
        'gui_scripts': ['DataLogger = datalogger.__main__:run_datalogger_full']},
      zip_safe=True,
      include_package_data=True)
