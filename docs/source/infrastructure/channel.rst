============
Data Storage
============

The Datalogger uses a three-tier structure for storing data, comprising of ChannelSets, Channels and DataSets.

image

*DataSets*: These are the lowest structure, effectively a vector of values with a name (``id_``) and units. 

*Channels*: Normally created from one stream of input data, Channels include the original DataSet, any derived DataSets (eg. frequency spectra, sonogram) and metadata about the channel. They also have methods for getting and setting the attributes of the DataSets.

*ChannelSets*: The main object to interface with, with methods for getting and setting channel and dataset attributes. Each ChannelSet will typically be derived from one set of results or one run of the experiment.

ChannelSet
----------
.. autoclass:: bin.channel.ChannelSet
  :members:

Channel
-------

.. autoclass:: bin.channel.Channel
  :members:

* ``name`` - A human-readable string identifying this channel

* ``comments`` - A string for any additional comments

* ``tags`` - A list of tags for quick selection and sorting

* ``sample_rate`` - The rate (in Hz) that the data was sampled at

* ``calibration_factor`` - Not implemented yet

* ``transfer_function_type`` - either ``None``, ``'displacement'``, ``'velocity'``, or ``'acceleration'``, indicating what type of transfer function is stored


DataSet
-------

.. autoclass:: bin.channel.DataSet
  :members:

* ``time_series`` - The raw input time series data

* ``time``\*	- Calculated from the sample rate and number of samples

* ``frequency``\* - Calculated from the sample rate and number of samples (Hz)

* ``omega``\* - Angular frequency (rad), calculated from the sample rate and number of samples

* ``spectrum`` - The complex spectrum given by the Fourier Transform

* ``sonogram`` - The complex sonogram array, with shape (number of FFTs, frequencies)

* ``sonogram_frequency``\* - The frequency bins (Hz) used in plotting the sonogram. Not implemented yet, but will be calculated from the sonogram parameters.

* ``sonogram_omega``\* - The frequency bins (rad) used in plotting the sonogram. Not implemented yet, but will be calculated from the sonogram parameters.


