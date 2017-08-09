import scipy.io as sio
from .channel import Channel, DataSet, ChannelSet
import numpy as np


def import_from_mat(file, channel_set):
    # Load the matlab file as a dict
    file = sio.loadmat(file)

    # Work out how many channels to create
    num_time_series_datasets = file["dt2"][0][0]
    num_spectrum_datasets = file["dt2"][0][1]
    num_sonogram_datasets = file["dt2"][0][2]

    num_channels = np.amax(np.asarray([num_time_series_datasets,
                                       num_spectrum_datasets,
                                       num_sonogram_datasets]))

    # # Extract metadata
    sample_rate = file["freq"][0][0]

    if "tsmax" in file.keys():
        time_series_scale_factor = file["tsmax"]
    else:
        time_series_scale_factor = None

    if "npts" in file.keys():
        fft_num_samples = file["npts"]
    else:
        fft_num_samples = None

    if "tfun" in file.keys():
        is_transfer_function = bool(file["tfun"])
    else:
        is_transfer_function = False

    if "step" in file.keys():
        sonogram_fft_step = file["step"]
    else:
        sonogram_fft_step = None

    # # Extract data
    # Transpose the data so it's easier to work with:
    # In the matlab file it is in the form
    # (num_samples_per_channel, num_channels) - each channel is a column
    # Numpy works more easily if it is in the form
    # (num_channels, num_samples_per_channel) - each channel is a row
    if "indata" in file.keys():
        time_series = file["indata"].transpose()
    if "yspec" in file.keys():
        spectrum = file["yspec"].transpose()
    if "yson" in file.keys():
        sonogram_amplitude = file["yson"].transpose()
    if "yphase" in file.keys():
        sonogram_phase = file["yphase"].transpose()

    # # Save everything
    for i in np.arange(num_channels):
        # Create a new channel
        channel_set.add_channels()

        # Set channel metadata
        channel_set.set_channel_metadata(i, {"name": "Imported {}".format(i),
                                             "sample_rate": sample_rate,
                                             "calibration_factor":
                                                 time_series_scale_factor})

        # Set channel data
        if i < num_time_series_datasets:
            channel_set.add_channel_dataset(i,
                                            "time_series",
                                            time_series)

        if i < num_spectrum_datasets:
            channel_set.add_channel_dataset(i,
                                            "spectrum",
                                             spectrum[i],
                                             'Hz')

        if i < num_sonogram_datasets:
            channel_set.add_channel_dataset(i,
                                            "sonogram",
                                            sonogram_amplitude[i])
            channel_set.add_channel_dataset(i,
                                            "sonogram_phase",
                                            sonogram_phase[i],
                                            'rad')

