"""
This module contains the class to record data from a soundcard.
It uses PyAudio to do so.
Please check the PyAudio Documentation for more information.

Typical example of using the module:
>>>import myRecorder as mR
>>>recorder = mR.Recorder()
Channels: 1
Rate: 44100
Chunk size: 1024
Number of chunks: 4
You are using pyAudio for recording
Device not found, reverting to default
Selected device: Line (3- U24XL with SPDIF I/O)
>>>recorder.stream_init()
stream already started
Input latency: 2.322e-02
Output latency: 0.000e+00
Read Available: -9977
Write Available: -9976
True
>>>recorder.record_init()
Recording function is ready! Use record_start() to start
True
>>>recorder.record_start()
stream already started
Recording Start!
True
>>>Recording Done! Please flush the data with flush_record_data().
data = recorder.flush_record_data()
>>>recorder.close()
"""

from datalogger.acquisition.RecorderParent import RecorderParent
import sys,traceback

try:
    import pyaudio
except ImportError:
    # If pyaudio doesn't work, create mock version of it
    from mock import Mock
    class MockModule(Mock):
        @classmethod
        def __getattr__(cls, name):
                return Mock()

    sys.modules['pyaudio'] = MockModule()
    import pyaudio

import numpy as np
import pprint as pp

class Recorder(RecorderParent):
    """
     Sets up the recording stream through a SoundCard
    
     Attributes
     ----------
        In addtion to RecorderParent Attributes,
        device_index: int
            Index of the device to be used for recording
        device_name: str
            Name of the device to be used for recording
        max_value: float
            Maximum value of recorded data
    """
        
#---------------- INITIALISATION METHODS -----------------------------------
    def __init__(self,channels = 1,rate = 44100, chunk_size = 1024,
                 num_chunk = 4,device_name = None):
        """
         Re-implemented from RecorderParent
        """
        
        super().__init__(channels = channels,rate = rate, 
             chunk_size = chunk_size,num_chunk = num_chunk)
        
        print('You are using pyAudio for recording')
        self.p = None
        self.format = pyaudio.paInt16
        self.device_index = None;
        self.device_name = device_name
        
        self.open_recorder()
        self.set_device_by_name(str(device_name))
        
        self.trigger_init()
        
        self.max_value = 1;
        
    def open_recorder(self):
        """
         Re-implemented from RecorderParent. Prepare the PyAudio Object too.
        """
        super().open_recorder()
        if self.p == None:
            self.p = pyaudio.PyAudio()

#---------------- DESTRUCTOR METHODS -----------------------------------       
    def close(self):
        """
         Re-implemented from RecorderParent, but terminate the PyAudio Object too.
        """
        super().close()
        #self.stream_close()
        if not self.p:
            self.p.terminate()
            self.p = None
            
#---------------- DEVICE SETTING METHODS -----------------------------------            
    def set_device_by_name(self, name):
        """
        Set the recording audio device by name. 
        Revert to default if no such device found
                
        Parameters
        ----------
            name: str
                Name of the device
        """
        dev_name,dev_index = self.available_devices()
        if not dev_name:
            print("Seems like you don't have any input devices")
            return
        
        try:
            self._set_device_by_index(dev_index[dev_name.index(name)])
        except ValueError:
            try:
                print('Device not found, reverting to default')
                default = self.p.get_default_input_device_info()
                self._set_device_by_index(default['index'])
            except IOError:
                print('No default device!')
                try:
                    self._set_device_by_index(dev_index[0])
                except IOError:
                    print('No Device can be set')
        except IOError:
            print('Device chosen cannot be found!')
                    
    def available_devices(self):
        """
        Searches for any available input devices
        
        Returns
        ----------
            names: List
                Name of the devices
            index: List
                Index of the devices
        """
        names = [self.p.get_device_info_by_index(i)['name']
                  for i in range(self.p.get_device_count())
                  if self.p.get_device_info_by_index(i)['maxInputChannels']>0]
        
        index = [self.p.get_device_info_by_index(i)['index'] 
                for i in range(self.p.get_device_count())
                if self.p.get_device_info_by_index(i)['maxInputChannels']>0]
        
        return(names,index)
      
    def current_device_info(self):
        """
        Display the current selected device info
        """
        if self.device_index:
            pp.pprint(self.p.get_device_info_by_index(self.device_index))
        else:
            print('No index set')
     
    def _set_device_by_index(self,index):
        """
        Set the selected device by index
        
        Parameters
        ----------
            index: int
                Index of the device to be set
        """
        self.device_index = index;
        self.device_name = self.p.get_device_info_by_index(index)['name']
        print("Selected device: %s" % self.device_name)
        
#---------------- DATA METHODS -----------------------------------
    # Convert data obtained into a proper array
    def audiodata_to_array(self,data):
        """
        Re-implemented from RecorderParent
        """
        return np.frombuffer(data, dtype = np.int16).reshape((self.chunk_size,self.channels))/ 2**15
                           
#---------------- STREAMING METHODS -----------------------------------
    def stream_audio_callback(self,in_data, frame_count, time_info, status):
        """
        Callback function for audio streaming.
        First, it writes data to the circular buffer, 
        then record data if it is recording,
        finally check for any trigger.
        
        Inputs and Outputs are part of the callback format.
        More info can be found in PyAudio documentation
        """
        data_array = self.audiodata_to_array(in_data)
        self.write_buffer(data_array)
        #self.rEmitter.newdata.emit()
        
        if self.recording:
            self.record_data(data_array)
            
         # Trigger check
        if self.trigger:
            self._trigger_check_threshold(data_array)
            
        return(in_data,pyaudio.paContinue)
    
    # TODO: Check for valid device, channels and all that before initialisation
    def stream_init(self, playback = False):
        """
        Re-implemented from RecorderParent.
        """
        if (not self.device_index == None) and (self.audio_stream == None) :
            try:
                self.audio_stream = self.p.open(channels = self.channels,
                                 rate = self.rate,
                                 format = self.format,
                                 input = True,
                                 output = playback,
                                 frames_per_buffer = self.chunk_size,
                                 input_device_index = self.device_index,
                                 stream_callback = self.stream_audio_callback)
                
                self.stream_start()
                print('Input latency: %.3e' % self.audio_stream.get_input_latency())
                print('Output latency: %.3e' % self.audio_stream.get_output_latency())
                print('Read Available: %i' % self.audio_stream.get_read_available())
                print('Write Available: %i' % self.audio_stream.get_write_available())
                return True
            
            except:
                t,v,tb = sys.exc_info()
                print(t)
                print(v)
                print(traceback.format_tb(tb))
                self.audio_stream = None
                return False
        else:
            return False
            
    # Start the streaming
    def stream_start(self):
        """
        Re-implemented from RecorderParent.
        """
        if self.audio_stream:
            if self.audio_stream.is_stopped():
                self.audio_stream.start_stream()
            else:
                print('stream already started')
        else:
            print('No audio stream is set up')
            
    # Stop the streaming
    def stream_stop(self):
        """
        Re-implemented from RecorderParent.
        """
        if self.audio_stream: 
            if not self.audio_stream.is_stopped():
                self.audio_stream.stop_stream()
            else:
                print('stream already stopped')
        else:
            print('No audio stream is set up')
        
    # Close the stream, probably needed if any parameter of the stream is changed
    def stream_close(self):
        """
        Re-implemented from RecorderParent.
        """
        if self.audio_stream and self.audio_stream.is_active():
            self.stream_stop()
            self.audio_stream.close()
            self.audio_stream = None
            
    