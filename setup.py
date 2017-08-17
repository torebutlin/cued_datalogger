from setuptools import setup
import sys
import subprocess
from os.path import isfile
from shutil import copyfile

def readme():
    """Get text from the README.rst"""
    with open('README.rst') as f:
        return f.read()

# Check if the python installation is from Anaconda - if it is, we need to
# move the python3.dll
print("Checking for Anaconda install...")

if "Anaconda" in sys.version or "Continuum" in sys.version:
    print("Anaconda install found.\n")
    
    if sys.version.startswith("win"):
        print("Operating system: Windows.")
        
        python_dll_found = False
        
        for location in sys.path:
            if isfile(location + "\Anaconda3\Library\bin\python3.dll"):
                python_dll_found = True
                break
        """
        default linux path: /home/<user>/anaconda3/ ?
        default max path /home/<user>/anaconda3/ ?
        default windows path: C:\ProgramData\Anaconda3\Library\bin
        """
        """
        print("Checking operating system...")
        if platform.startswith('linux'):
            print("Operating system: Linux")
        elif platform.startswith('darwin'):
            print("Operating system: Mac OS")
        elif platform.startswith('win'):
            print("Operating system: Windows")
            print("Unknown operating system found. Aborting.")
            raise OSError("DataLogger not configured for this OS.")
        """
    if python_dll_found:
        print("python3.dll file found, so DataLogger will work"
              "with this Anaconda.")
        print("Continuing to setup...\n")
        exit(1)
    else:
        print("Error: No python3.dll file found, so DataLogger will NOT work" 
              "with this Anaconda.")
        print("#############################################################\n"
              " Please copy the python3.dll file to the Anaconda Library \n"
              " binary folder (eg. C:\ProgramData\Anaconda3\Library\bin) \n"
              " and rerun setup.py \n"
              "#############################################################")
else:
    print("Anaconda not found. [OK]")
    print("Continuing to setup...\n")


setup(name='CUED_DataLogger',
      version='0.0.14',
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
