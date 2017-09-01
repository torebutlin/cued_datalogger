from setuptools import setup
import sys
import subprocess
from os.path import isfile
import urllib.request
import traceback
import pip

def version():
    """Get version number"""
    with open('datalogger/VERSION') as f:
        return f.read()

def readme():
    """Get text from the README.rst"""
    with open('README.rst') as f:
        return f.read()


# Check for Anaconda
print("Checking for Anaconda installation...")
if "Anaconda" in sys.version or "Continuum" in sys.version:
    print("Anaconda installation found.\n")
    use_anaconda = True
else:
    print("Anaconda not found. [OK]")
    use_anaconda = False


# Check OS
if sys.platform.startswith("win"):
    operating_system = "windows"
elif sys.platform.startswith("linux"):
    operating_system = "linux"
elif sys.platform == "darwin":
    operating_system = "os x"
else:
    operating_system = "unable to detect operating system"

print("Operating system: {}.\n".format(operating_system))

if operating_system == "unable to detect operating system" and use_anaconda:
    print("[WARNING] The DataLogger has not been configured for this operating"
          " system. \n The installation may not work correctly.")


# Do some OS / Anaconda specific config
if use_anaconda and operating_system != "windows":
    # Find conda
    conda_executable = subprocess.check_output(['which', 'conda']).decode("utf-8").split()[0]
    print("Conda executable found at {}".format(conda_executable))

if use_anaconda and operating_system == "windows":
    # Find conda
    conda_executable = subprocess.check_output(['where', 'conda.exe']).decode("utf-8").split()[0]
    if isinstance(conda_executable, list):
        conda_executable = conda_executable[0]
    print("Conda executable found at {}".format(conda_executable))

    # Check for python3.dll
    print("Searching for python3.dll...")
    print("(In Anaconda on Windows, this dll is required for the DataLogger"
          " UI)")

    python_dll_found = False

    # Find where the python executables are (returns a list)
    python_path = subprocess.check_output(['where', 'python']).decode("utf-8")
    python_path = python_path.split()

    anaconda_paths = []

    # Process these to get just the anaconda paths
    for location in python_path:
        # Get the first part of the path
        # eg. \home\Anaconda\python3\ becomes \home\Anaconda
        anaconda_path = location.split('python')[0]
        # Swap the \ for /
        anaconda_path = anaconda_path.replace("\\", '/')
        anaconda_paths.append(anaconda_path)

    # Look in all the conda paths for the .dll
    for location in anaconda_paths:
        if isfile(location + "Library/bin/python3.dll"):
            print("python3.dll found in " + location
                  + "Library/bin/python3.dll")
            python_dll_found = True
            break

    if python_dll_found:
        print("python3.dll file found, so DataLogger will work "
              "with this Anaconda installation.\n")
    else:
        user_input = input("No python3.dll file found. "
                           "Do you want to download it? [y]/n: ")
        if user_input is '' or 'y':
            dll_url = ("https://github.com/torebutlin/cued_datalogger/tree/"
                       "master/lib/python3.dll")
            print("Downloading from {}...".format(dll_url))
            for location in anaconda_paths:
                # Download the dll
                try:
                    urllib.request.urlretrieve(dll_url,
                                               location + 'Library/bin/python3.dll')
                except:
                    print("Error downloading python3.dll.")
                    traceback.print_exc()
                    sys.exit(1)
                print("python3.dll downloaded to {}.\n".format(location))
        elif user_input is 'n':
            print("Not downloading python3.dll. Aborting install.\n")
            sys.exit(1)
        else:
            print("Please enter 'y' or 'n'.")


print("Configuring dependency list...")
if use_anaconda:
    conda_dependency_list = ['numpy', 'scipy']
    dependency_list = ['matplotlib',
                       'pydaqmx',
                       'pyqtgraph']
else:
    dependency_list = ['numpy',
                       'scipy',
                       'pyqtgraph',
                       'matplotlib',
                       'PyDAQmx',
                       'pyaudio']
print("Dependencies: ")
for package in dependency_list:
    print(package)
print("PyQt5 (cannot be installed using install_requires)")
print("pyaudio (cannot be installed using install_requires)")
if use_anaconda:
    for item in conda_dependency_list:
        print(item + (" (conda version)"))


print("Installing dependencies...")

if use_anaconda:
    # Install anaconda dependencies
    print("Installing conda dependencies... ")
    for dependency in conda_dependency_list:
        print("Installing " + dependency + " using conda:")
        install_command = [conda_executable, 'install', '-y', dependency]
        conda_install_process = subprocess.Popen(install_command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
        #while conda_install_process.stdout:
        for line in conda_install_process.stdout:
            print(line.decode(), end='')

# PyQt5 does not have a source distribution currently (09/2017) so it cannot
# be installed using setuptools. The wheel must be installed manually.
# see https://stackoverflow.com/questions/4628519/is-it-possible-to-require-pyqt-from-setuptools-setup-py/45598092#45598092
print("Installing PyQt5 from wheel...")
pip.main(['install', 'PyQt5'])

# PyAudio has some strange dependency on a C++ library
print("Installing pyaudio from wheel...")
pip.main(['install', 'pyaudio'])

for package in dependency_list:
    pip.main(['install', package])


print("Continuing to setup...\n")

setup(name='cued-datalogger',
      version=version(),
      description='The CUED DataLogger for acquiring and analysing data',
      long_description=readme(),
      url='https://github.com/torebutlin/cued_datalogger',
      author='Theo Brown, En Yi Tee',
      author_email='tab53@cam.ac.uk, eyt21@cam.ac.uk',
      license='BSD 3-Clause License',
      packages=['datalogger',
                'datalogger/acquisition',
                'datalogger/analysis',
                'datalogger/api'],
      install_requires=None,#dependency_list,
      entry_points={
        'console_scripts': ['datalogger_dbg ='
                            ' datalogger.__main__:run_datalogger_full'],
        'gui_scripts': ['datalogger = '
                        'datalogger.__main__:run_datalogger_full']},
      zip_safe=True,
      include_package_data=True)
