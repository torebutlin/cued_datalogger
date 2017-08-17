# Creating an installable package

## `setup.py`
Create a `setup.py` file (see [here](https://python-packaging.readthedocs.io) and [here](https://packaging.python.org/tutorials/distributing-packages/#packaging-your-project)

To upload the file to pypi, first make sure that your version doesn't already exist on PyPI.

Then run:

    python3 setup.py sdist bdist_wheel upload

It might be possible to build a universal wheel, not sure.

### Possible errors:

#### `error: Upload failed (403): Invalid or non-existent authentication information.`
For some weird reason, PyPI only asks for your password and not your username - if you don't have one configured, it assumes your username is blank.

To set a username, create a `.pypirc` file in `~/` with the following:

    [distutils]
    index-servers =
        pypi

    [pypi]
    repository: https://upload.pypi.org/legacy/
    username: <your-username-here>


#### `error: invalid command 'bdist_wheel'`
The `wheel` package is installed in somewhere that's not on the path. Why, no idea.

To fix:

First, try and install `wheel` again:

    pip3 install wheel

This should tell you where wheel is installed, eg:

    Requirement already satisfied: wheel in /usr/local/lib/python3.5/dist-packages

Then add the location of wheel to your `PYTHONPATH`:

    export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3.5/dist-packages/wheel

You could try adding just the `/usr/local/lib/python3.5` instead - haven't tested this.

Now building a wheel should work fine.

    python3 setup.py bdist_wheel


## Requirements
Use `pipreqs . --force` to create a requirements.txt file.


