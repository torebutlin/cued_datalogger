============
Data Storage
============

The Datalogger uses a three-tier structure for storing data, comprising of ChannelSets, Channels and DataSets.

::

                                               ChannelSet 
                 ___________________________________|_________________________... 
                /                       |                       | 
            Channel 0                Channel 1               Channel 2        ... 
           /         \              /         \             /         \
       MetaData    DataSets     MetaData    DataSets     MetaData    DataSets ... 
          |        | | | |         |        | | | |         |        | | | | 
         ...         ...          ...         ...          ...         ...    ... 

*DataSets*: These are the lowest structure, effectively a vector of values with a name (``id_``) and units. 

*Channels*: Normally created from one stream of input data, Channels include the original DataSet, any derived DataSets (eg. frequency spectra, sonogram) and metadata about the channel. They also have methods for getting and setting the attributes of the DataSets.

*ChannelSets*: The main object to interface with, with methods for getting and setting channel and dataset attributes. Each ChannelSet will typically be derived from one set of results or one run of the experiment.

ChannelSet
----------
.. autoclass:: datalogger.api.channel.ChannelSet
  :members:

  .. automethod:: datalogger.api.channel.ChannelSet.__init__

  .. automethod:: datalogger.api.channel.ChannelSet.__len__


Channel
-------

.. autoclass:: datalogger.api.channel.Channel
  :members:

  .. automethod:: datalogger.api.channel.Channel.__init__


DataSet
-------

.. autoclass:: datalogger.api.channel.DataSet
  :members:

  .. automethod:: datalogger.api.channel.DataSet.__init__

Widgets
-------
See :class:`~datalogger.api.channel.ChannelSelectWidget` and :class:`~datalogger.api.channel.ChannelMetadataWidget` for
widgets to interact with ChannelSets.

