"""
This module contains the class to record data from a National Instrument.
It uses PyDAQmx to do so, but requires NIDAQmx drivers to function.
Please check the PyDAQMx and NIDAQmx C API reference for more information.

Typical example of using the module:
>>>import myRecorder as NIR
>>>recorder = NIR.Recorder()
Channels: 1
Rate: 30000
Chunk size: 1000
Number of chunks: 4
You are using National Instrument for recording
Input device name not found, using the first device
Selected devices: Dev3
>>>recorder.stream_init()
Channels Name: Dev3/ai0
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
Data flushed
>>>recorder.close()
"""
from cued_datalogger.acquisition.RecorderParent import RecorderParent

import sys,traceback
import PyDAQmx as pdaq
from PyDAQmx import Task

import numpy as np
import pprint as pp

class Recorder(RecorderParent):
    """
     Sets up the recording stream through a National Instrument
    
     Attributes
     ----------
    device_name: str
        Name of the device to be used for recording
    max_value: float
        Maximum value of recorded data
    """
#---------------- INITIALISATION METHODS -----------------------------------
    def __init__(self,channels = 1,rate = 30000.0, chunk_size = 1000,
                 num_chunk = 4,device_name = None):
        """
        Re-implemented from RecorderParent
        """

        super().__init__(channels = channels,rate = rate, 
             chunk_size = chunk_size,num_chunk = num_chunk)
        print('You are using National Instrument for recording')
        
        self.device_name = None
        self.set_device_by_name(device_name);
               
        self.open_recorder()
        self.trigger_init()
        
        self.max_value = 10;
            
#---------------- DEVICE SETTING METHODS -----------------------------------
    def set_device_by_name(self, name):
        """
         Set the recording audio device by name.
         Uses the first device found if no such device found.
        """
        devices = self.available_devices()[0]
        selected_device = None
        if not devices:
            print('No NI devices found')
            return
        
        if not name in devices:
            print('Input device name not found, using the first device')
            selected_device = devices[0]
        else:
            selected_device = name
            
        print('Selected devices: %s' % selected_device)
        self.device_name = selected_device
    
     # Get audio device names 
    def available_devices(self):
        """
        Get all the available input National Instrument devices.
        
        Returns
        ----------
        devices_name: List of str
            Name of the device, e.g. Dev0
        device_type: List of str
            Type of device, e.g. USB-6003 
        """
        numBytesneeded = pdaq.DAQmxGetSysDevNames(None,0)
        databuffer = pdaq.create_string_buffer(numBytesneeded)
        pdaq.DAQmxGetSysDevNames(databuffer,numBytesneeded)
                
        #device_list = []
        devices_name = pdaq.string_at(databuffer).decode('utf-8').split(',')
        
        device_type = []
        for dev in devices_name:
            numBytesneeded = pdaq.DAQmxGetDevProductType(dev,None,0)
            databuffer = pdaq.create_string_buffer(numBytesneeded)
            pdaq.DAQmxGetDevProductType(dev,databuffer,numBytesneeded)
            device_type.append(pdaq.string_at(databuffer).decode('utf-8'))
            
        #device_list.append(devices_name)
        #device_list.append(device_type)
        
        return(devices_name,device_type)
    
    # Display the current selected device info      
    def current_device_info(self):
        """
        Prints information about the current device set
        """
        device_info = {}
        info = ('Category', 'Type','Product', 'Number',
                'Analog Trigger Support','Analog Input Trigger Types','Analog Input Channels (ai)', 'Analog Output Channels (ao)', 
                'ai Minimum Rate(Hz)', 'ai Maximum Rate(Single)(Hz)', 'ai Maximum Rate(Multi)(Hz)',
                'Digital Trigger Support','Digital Input Trigger Types','Digital Ports', 'Digital Lines', 'Terminals')
        funcs = (pdaq.DAQmxGetDevProductCategory, pdaq.DAQmxGetDevProductType,
                 pdaq.DAQmxGetDevProductNum, pdaq.DAQmxGetDevSerialNum,
                 pdaq.DAQmxGetDevAnlgTrigSupported,  pdaq.DAQmxGetDevAITrigUsage,
                 pdaq.DAQmxGetDevAIPhysicalChans,pdaq.DAQmxGetDevAOPhysicalChans, 
                 pdaq.DAQmxGetDevAIMinRate, pdaq.DAQmxGetDevAIMaxSingleChanRate, pdaq.DAQmxGetDevAIMaxMultiChanRate,
                 pdaq.DAQmxGetDevDigTrigSupported,pdaq.DAQmxGetDevDITrigUsage,
                 pdaq.DAQmxGetDevDIPorts,pdaq.DAQmxGetDevDILines,
                 pdaq.DAQmxGetDevTerminals)
        var_types = (pdaq.int32, str, pdaq.uint32, pdaq.uint32, 
                     pdaq.bool32,pdaq.int32,str,str, 
                     pdaq.float64, pdaq.float64, pdaq.float64,
                     pdaq.bool32,pdaq.int32,str,str,str)
        
        for i,f,v in zip(info,funcs,var_types):
            try:
                if v == str:
                    nBytes = f(self.device_name,None,0)
                    string_ptr = pdaq.create_string_buffer(nBytes)
                    f(self.device_name,string_ptr,nBytes)
                    if any( x in i for x in ('Channels','Ports')):
                        device_info[i] = len(string_ptr.value.decode().split(','))
                    else:
                        device_info[i] = string_ptr.value.decode()
                else:
                    data = v()
                    f(self.device_name,data)
                    if 'Types' in i:
                        device_info[i] = bin(data.value)[2:].zfill(6)
                    else:
                        device_info[i] = data.value
            except Exception as e:
                print(e)
                device_info[i] = '-'
                           
        pp.pprint(device_info)
        
    def set_channels(self):
        """
        Create the string to initiate the channels when assigning a Task 
        
        Returns
        ----------
        channelname: str
            The channel names to be used when assigning Task 
            e.g. Dev0/ai0:Dev0/ai1
        """
        if self.channels >1:
            channelname =  '%s/ai0:%s/ai%i' % (self.device_name, self.device_name,self.channels-1)
        elif self.channels == 1:
            channelname = '%s/ai0' % self.device_name
            
        print('Channels Name: %s' % channelname)
        return channelname
            
#---------------- STREAMING METHODS -----------------------------------
    # Convert data obtained into a proper array
    def audiodata_to_array(self,data):
        """
        Re-implemented from RecorderParent
        """
        return data.reshape((-1,self.channels))/(2**15) *10.0
    
    # Callback function for audio streaming
    def stream_audio_callback(self):
        """
        Callback function for audio streaming.
        First, it writes data to the circular buffer, 
        then record data if it is recording,
        finally check for any trigger.
        
        Returns 0 as part of the callback format.
        More info can be found in PyDAQmx documentation on Task class
        """
        in_data = np.zeros(self.chunk_size*self.channels,dtype = np.int16)
        read = pdaq.int32()
        self.audio_stream.ReadBinaryI16(self.chunk_size,10.0,pdaq.DAQmx_Val_GroupByScanNumber,
                           in_data,self.chunk_size*self.channels,pdaq.byref(read),None)
        
        data_array = self.audiodata_to_array(in_data)
        self.write_buffer(data_array)
        #self.rEmitter.newdata.emit()
       
        if self.recording:
            self.record_data(data_array)
         # Trigger check
        if self.trigger:
            self._trigger_check_threshold(data_array)
        
        return 0
    
    def stream_init(self, playback = False):
        """
        Re-implemented from RecorderParent.
        """
        if self.audio_stream == None:
            try:
                self.audio_stream = Task()
                self.audio_stream.stream_audio_callback = self.stream_audio_callback
                self.audio_stream.CreateAIVoltageChan(self.set_channels(),"",
                                         pdaq.DAQmx_Val_RSE,-10.0,10.0,    
                                         pdaq.DAQmx_Val_Volts,None)
                self.audio_stream.CfgSampClkTiming("",self.rate,
                                      pdaq.DAQmx_Val_Rising,pdaq.DAQmx_Val_ContSamps,
                                      self.chunk_size)
                self.audio_stream.AutoRegisterEveryNSamplesEvent(pdaq.DAQmx_Val_Acquired_into_Buffer,
                                                    1000,0,name = 'stream_audio_callback')
                
                self.stream_start()
                return True
            except:
                t,v,tb = sys.exc_info()
                print(t)
                print(v)
                print(traceback.format_tb(tb))
                self.audio_stream = None
                
                return False
        
    # Start the streaming
    def stream_start(self):
        """
        Re-implemented from RecorderParent.
        """
        if self.audio_stream: 
            task_done = pdaq.bool32()
            self.audio_stream.GetTaskComplete(task_done)
            if task_done.value:
                self.audio_stream.StartTask()
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
            task_done = pdaq.bool32()
            self.audio_stream.GetTaskComplete(task_done)
            if not task_done.value:
                self.audio_stream.StopTask()
            else:
                print('stream already stopped')
        else:
            print('No audio stream is set up')
        
    # Close the stream, probably needed if any parameter of the stream is changed
    def stream_close(self):
        """
        Re-implemented from RecorderParent.
        """
        if self.audio_stream:
            self.audio_stream.StopTask()
            self.audio_stream.ClearTask()
            self.audio_stream = None