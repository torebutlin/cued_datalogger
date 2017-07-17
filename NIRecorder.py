"""
Recorder class:
- Aim to be essentially identical to the pyaudio version
- May want to have a parent class to inherit common things
"""

# Add codes to install pyaudio if pyaudio is not installed
import PyDAQmx as pdaq
from PyDAQmx import Task
import numpy as np
import pprint as pp
import copy as cp


class Recorder():
#---------------- INITIALISATION METHODS -----------------------------------
    def __init__(self,channels = 1,rate = 30000.0, chunk_size = 1000,
                 num_chunk = 4,device_name = None):
        self.channels = channels
        self.rate = rate
        self.chunk_size = chunk_size
        self.num_chunk = num_chunk;
        self.audio_stream = None
        
        print('You are using National Instrument for recording')
        #self.format = pdaq.int16()
        
        # TODO: setup set device by index
        self.device_index = 0;
        self.device_name = self.set_device_by_name(device_name);
        self.channel_names = self.set_channels()
               
        self.open_recorder()
        self.allocate_buffer()
        
        
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
    def set_device_by_name(self, name):
        devices = self.available_devices()[0]
        selected_device = None
        if not devices:
            print('No NI devices found')
            return selected_device
        
        if not name in devices:
            print('Input device name not found, using the first device')
            selected_device = devices[0]
        else:
            selected_device = name
            
        print('Selected devices: %s' % selected_device)
        return selected_device
    
     # Get audio device names 
    def available_devices(self):
        numBytesneeded = pdaq.DAQmxGetSysDevNames(None,0)
        databuffer = pdaq.create_string_buffer(numBytesneeded)
        pdaq.DAQmxGetSysDevNames(databuffer,numBytesneeded)
        devices_name = pdaq.string_at(databuffer).decode('utf-8').split(',')
        device_list = []
        device_list.append(devices_name)
        return(device_list)
    
    # Display the current selected device info      
    def current_device_info(self):
        device_info = {}
        info = ('Category', 'Type','Product', 'Number',
                'Analog Trigger','Analog Input Channels (ai)', 'Analog Output Channels (ao)',
                'Minimum Rate(Hz)', 'Maximum Rate(Single)(Hz)', 'Maximum Rate(Multi)(Hz)')
        funcs = (pdaq.DAQmxGetDevProductCategory, pdaq.DAQmxGetDevProductType,
                 pdaq.DAQmxGetDevProductNum, pdaq.DAQmxGetDevSerialNum,
                 pdaq.DAQmxGetDevAnlgTrigSupported, pdaq.DAQmxGetDevAIPhysicalChans,
                 pdaq.DAQmxGetDevAOPhysicalChans, pdaq.DAQmxGetDevAIMinRate,
                 pdaq.DAQmxGetDevAIMaxSingleChanRate, pdaq.DAQmxGetDevAIMaxMultiChanRate)
        var_types = (pdaq.int32, str, pdaq.uInt32, pdaq.uInt32, pdaq.bool32,
                    str,str, pdaq.float64, pdaq.float64, pdaq.float64)
        
        for i,f,v in zip(info,funcs,var_types):
            if v == str:
                nBytes = f(self.device_name,None,0)
                string_ptr = pdaq.create_string_buffer(nBytes)
                f(self.device_name,string_ptr,nBytes)
                if 'Channels' in i:
                    device_info[i] = len(string_ptr.value.decode().split(','))
                else:
                    device_info[i] = string_ptr.value.decode()
            else:
                data = v()
                f(self.device_name,data)
                device_info[i] = data.value
                           
        pp.pprint(device_info)
        
   
        # Originally setting file name   
    def set_filename(self,filename):
        self.filename = filename
        
    # Return the channel names to be used when assigning task     
    def set_channels(self):
        if self.channels >1:
            channelname =  '%s/ai0:%i' % (self.device_name, self.channels-1)
        else:
            channelname = '%s/ai0' % self.device_name
            
        print('Channels Name: %s' % channelname)
        return channelname
            

#---------------- DATA METHODS -----------------------------------
    # Convert data obtained into a proper array
    def audiodata_to_array(self,data):
        return data.reshape((-1,self.channels))
    
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
            self.audio_stream.CreateAIVoltageChan(self.channel_names,"",
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

