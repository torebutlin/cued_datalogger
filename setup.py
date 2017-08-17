from setuptools import setup

def readme():
    """Get text from the README.rst"""
    with open('README.rst') as f:
        return f.read()

setup(name='CUED_DataLogger',
      version='0.0.4',
      description='The CUED DataLogger for acquiring and analysing data',
      long_description=readme(),
      url='https://bitbucket.org/tab53/cued_datalogger/',
      author='Theo Brown, En Yi Tee',
      author_email='tab53@cam.ac.uk, eyt21@cam.ac.uk',
      license='BSD 3-Clause License',
      packages=['datalogger'],
      install_requires=[
              'numpy>=1.11.3',
              'pyqtgraph>=0.9.10',
              'matplotlib>=1.5.1',
              'scipy>=0.18.1',
              'PyDAQmx>=1.3.2',
              'PyQt5>=5.9',
              'pyaudio>=0.2.11'],
      scripts=['scripts/DataLogger'],  
      zip_safe=True,
      include_package_data=True)
