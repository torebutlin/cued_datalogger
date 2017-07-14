"""
Recorder class:
- Allow recording and configurations of recording device
- Allow audio stream
- Store data as numpy arrays for both recording and audio stream
    which can be accessed for plotting
"""

# Add codes to install pyaudio if pyaudio is not installed
import PyDAQmx as pdaq
from PyDAQmx import Task
#import pyaudio
import numpy as np
#import pprint as pp
import copy as cp


class Recorder():#Task
#---------------- INITIALISATION METHODS -----------------------------------
    def __init__(self,channels = 1,rate = 30000.0, chunk_size = 1000,
                 num_chunk = 4,device_name = None):
        #super().__init__()
        self.channels = channels
        self.channelnames = self.list_channels()
        self.rate = rate
        self.chunk_size = chunk_size
        #self.format = pdaq.int16()
        #self.device_index = 0;
        self.audio_stream = None
        self.num_chunk = num_chunk;        
        
        self.open_recorder()
        self.allocate_buffer()
        print('You are using National Instrument for recording')
        
    def __del__(self):
        self.close()
        
    def open_recorder(self):
        self.recording = False
        self.recorded_data = []
        
                     
    # Set up the buffer         
    def allocate_buffer(self):
        self.buffer = np.zeros(shape = (self.num_chunk,
                                        self.chunk_size,
                                        self.channels))
        self.next_chunk = 0;
            
#---------------- DEVICE SETTING METHODS -----------------------------------
    # Get audio device names 
    def available_devices(self):
        numBytesneeded = pdaq.DAQmxGetSysDevNames(None,0)
        databuffer = pdaq.create_string_buffer(numBytesneeded)
        pdaq.DAQmxGetSysDevNames(databuffer,numBytesneeded)
        devices_name = pdaq.string_at(databuffer).decode('utf-8')#.split(',')
        return(devices_name)
        
    # Return the channel names to be used when assigning task     
    def list_channels(self):
        if self.channels >1:
            return 'Dev1/ai0:%i' % (self.channels-1)
        else:
            return 'Dev1/ai0'
#---------------- DATA METHODS -----------------------------------
    # Convert data obtained into a proper array
    def audiodata_to_array(self,data):
        return data.reshape((-1,self.channels))
        #return np.frombuffer(data, dtype = np.int16).reshape((-1,self.channels))
    
#---------------- BUFFER METHODS -----------------------------------
    # Write the data obtained into buffer and move to the next chunk   
    def write_buffer(self,data):
        self.buffer[self.next_chunk,:,:] = self.audiodata_to_array(data)
        self.next_chunk = (self.next_chunk + 1) % self.num_chunk
    
    # Return the buffer data as a 2D array by stitching the chunks together  
    def get_buffer(self):
        return np.concatenate((self.buffer[self.next_chunk:],self.buffer[:self.next_chunk]),axis = 0) \
                 .reshape((self.buffer.shape[0] * self.buffer.shape[1],
                           self.buffer.shape[2])) / 2**7

#---------------- RECORDING METHODS -----------------------------------
    # Append the current chunk(which is before next_chunk) to recorded data            
    def record_data(self):
        data = cp.copy(self.buffer[self.next_chunk-1])
        self.recorded_data.append(data)
        
    # Return the recorded data as 2D numpy array (similar to get_buffer)    
    def flush_record_data(self):
        flushed_data = np.array(self.recorded_data)
        self.recorded_data = []
        return flushed_data.reshape((flushed_data.shape[0] * flushed_data.shape[1],
                           flushed_data.shape[2])) / 2**7
                           
#---------------- STREAMING METHODS -----------------------------------
    # Callback function for audio streaming
    def stream_audio_callback(self):
        in_data = np.zeros(self.chunk_size,dtype = np.int16)
        read = pdaq.int32()
        self.audio_stream.ReadBinaryI16(self.chunk_size,10.0,pdaq.DAQmx_Val_GroupByScanNumber,
                           in_data,self.chunk_size,pdaq.byref(read),None)
        self.write_buffer(self.audiodata_to_array(in_data))
        if self.recording:
            self.record_data()
        return 0
    
    # TODO: Check for valid device, channels and all that before initialisation
    def stream_init(self, playback = False):
        if self.audio_stream == None:
            self.audio_stream = Task()
            self.audio_stream.stream_audio_callback = self.stream_audio_callback
            self.audio_stream.CreateAIVoltageChan(self.channelnames,"",
                                     pdaq.DAQmx_Val_RSE,-10.0,10.0,
                                     pdaq.DAQmx_Val_Volts,None)
            self.audio_stream.CfgSampClkTiming("",self.rate,
                                  pdaq.DAQmx_Val_Rising,pdaq.DAQmx_Val_ContSamps,
                                  self.chunk_size)
            self.audio_stream.AutoRegisterEveryNSamplesEvent(pdaq.DAQmx_Val_Acquired_Into_Buffer,
                                                1000,0,name = 'stream_audio_callback')
            
            self.stream_start()
    # Start the streaming
    def stream_start(self):
        self.audio_stream.StartTask()
    # Stop the streaming
    def stream_stop(self):
        self.audio_stream.StopTask()
        
    # Close the stream, probably needed if any parameter of the stream is changed
    def stream_close(self):
        if self.audio_stream:
            self.audio_stream.ClearTask()
            self.audio_stream = None
        
#----------------- DECORATOR METHODS --------------------------------------
            
#---------------- DESTRUCTOR??? METHODS -----------------------------------
    # Close the audio object, to be called if streaming is no longer needed        
    def close(self):
        self.stream_close()

