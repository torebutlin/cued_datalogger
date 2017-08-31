# -*- coding: utf-8 -*-
#Created on Sat Jul 15 20:01:58 2017
#@author: En Yi
"""
This module contains the abstract class to implement a proper    
Recorder Class. To do so, subclass RecorderParent when creating
a new Recorder class.

Example:
    from RecorderParent import RecorderParent
    
    class newRecorder(RecorderParent):
        ...
        ...
        
If you have PyQt, it will import RecEmitter for emitting Signals.

Attributes
----------
    QT_EMITTER : Indicates whether you can use qt Signals

"""
from abc import ABCMeta, abstractmethod
import numpy as np
import copy as cp

try:
    from datalogger.acquisition.RecEmitter import RecEmitter
    QT_EMITTER = True
except Exception as e:
    print(e)
    QT_EMITTER = False
    


class RecorderParent(object):
    """
     Recorder abstract class. Sets up the buffer and skeleton for audio streaming
    
     Attributes
     ----------
        channels: int
                Number of Channels
        rate: int
            Sampling rate
        chunk_size: int
            Number of samples to get from each channel in one chunk
        num_chunk: int
            Number of chunks to store in circular buffer
        recording: Bool
            Indicate whether to record
    """
    __metaclass__ = ABCMeta
    
#---------------- INITIALISATION METHODS -----------------------------------    
    def __init__(self,channels = 1,rate = 44100, chunk_size = 1024,
                 num_chunk = 4):
        """
        Initialise a ciruclar buffer, array and trigger for recording
        
        Parameters
        ----------
        channels: int
                Number of Channels
        rate: int
            Sampling rate
        chunk_size: int
            Number of samples to get from each channel in one chunk
        num_chunk: int
            Number of chunks to store in circular buffer
        """
        self.channels = channels
        self.rate = rate
        self.chunk_size = chunk_size
        self.num_chunk = num_chunk;
        self.audio_stream = None #: The audio object
        
        self.allocate_buffer()
        self.show_stream_settings()
        
        self.trigger_init()
        
        if QT_EMITTER:
            self.rEmitter = RecEmitter()
        else:
            self.rEmitter = None
                 
    def allocate_buffer(self):
        """
        Set up the circular buffer
        """
        self.buffer = np.zeros(shape = (self.num_chunk,
                                        self.chunk_size,
                                        self.channels))
        self.next_chunk = 0;

#---------------- DESTRUCTOR METHODS -----------------------------------     
    def __del__(self):
        self.close()
           
    def close(self):
        """
        Close the audio object, to be called if streaming is no longer needed 
        """
        self.stream_close()
 
#---------------- DEVICE SETTINGS METHODS -----------------------------------     
    def show_stream_settings(self):
        """
        Show the settings of the recorder
        """
        print('Channels: %i' % self.channels)
        print('Rate: %i' % self.rate)
        print('Chunk size: %i' % self.chunk_size)
        print('Number of chunks: %i' % self.num_chunk)
        
    def set_filename(self,filename):
        self.filename = filename
        
    @abstractmethod
    def set_device_by_name(self, name):
        """
        Set the device to be used for audio streaming
        """
        pass
    
    @abstractmethod    
    def available_devices(self):
        """
        Displays all available device for streaming
        """
        pass
    
    @abstractmethod
    def current_device_info(self):
        """
        Displays information about available the current device set
        """
        pass
    
#---------------- DATA METHODS -----------------------------------
    def audiodata_to_array(self,data):
        """
        Convert audio data obtained into a proper array
        
        Paramters
        ----------
            data: Numpy Array
                Audio data 
        """
        return data.reshape((-1,self.channels))/ 2**15
    
#---------------- BUFFER METHODS -----------------------------------
    def write_buffer(self,data):
        """
        Write the data obtained into buffer and move to the next chunk
        
        Paramters
        ----------
            data: Numpy Array
                Audio data 
        """
        self.buffer[self.next_chunk,:,:] = data
        self.next_chunk = (self.next_chunk + 1) % self.num_chunk
     
    def get_buffer(self):
        """
        Convert the buffer data as a 2D array by stitching the chunks together
        
        Returns
        ----------
            Buffer data: Numpy Array
                with dimension of(chunk_size * num_chunk) x channels
                The newest data on the most right 
        """
        return np.concatenate((self.buffer[self.next_chunk:],self.buffer[:self.next_chunk]),axis = 0) \
                 .reshape((self.buffer.shape[0] * self.buffer.shape[1],
                           self.buffer.shape[2]))
        
#---------------- RECORDING METHODS -----------------------------------
    def open_recorder(self):
        """
        Initialise the variables for recording.
        """
        self.recording = False
        self.initialised_record = False
        self.next_rec_chunk = 0
        self.total_rec_chunk = 0
        self.recorded_data = []
        
    def record_init(self,samples = None,duration = 3):
        """
        Remove any pretrigger and postrigger data
        Calculate the number of chunk to record
        It will record more samples than necessary, then slice down to the
        amount of samples required + putting in pretrigger data
        
        Parameters
        ----------
            samples: int
                Number of samples to record
            duration: int
                The recording duration
        
        """
        if not self._record_check():
            return False
        
        self.pretrig_data = np.array([],dtype = np.int16)
        self.part_posttrig_data = np.array([],dtype = np.int16)
        if samples:
            self.actual_rec_samples = samples
            self.total_rec_chunk = (samples // self.chunk_size)+1
            self.rec_samples = self.total_rec_chunk * self.chunk_size 
        else:
            self.total_rec_chunk = int(duration * self.rate // self.chunk_size)
            self.rec_samples = self.total_rec_chunk * self.chunk_size 
            self.actual_rec_samples = self.rec_samples
            
        self.next_rec_chunk = 0
        
        self.initialised_record = True
        
        print('Recording function is ready! Use record_start() to start')
        
        return True
    
    def _record_check(self):
        """
        Check if it is possible to start a recording
        
        Returns
        ----------
            True if possible, False otherwise
        
        """
        if not self.audio_stream:
            print('No recording stream initiated!')
            return False
        
        # Check if the previous recorded data is flushed
        if self.recorded_data:
            print('Please flush your recorded data')
            return False
        
        return True

    # Function to initiate a normal recording
    def record_start(self):
        """
        Start recording if it is possible
        
        Returns
        ----------
            True if possible, False otherwise
        
        """
        if not self._record_check():
            return False
                       
        # Start the recording if recording is initialised
        if self.initialised_record: 
            self.stream_start()
            self.recording = True
            print('Recording Start!')
            return True
        else:
            print('Record not initialised! Use record_init(duration) first!')
            return False
        
    def _record_stop(self):
        """
        Stop a successful recording and emit a signal if possible
        """
        # Stop the recording
        self.recording = False
        # Give a signal that recording is done
        print('Recording Done! Please flush the data with flush_record_data().')
        if self.rEmitter:
            self.rEmitter.recorddone.emit()
            
    def record_cancel(self):
        """
        Cancel a recording and clear any recorder data
        """
        print('Recording Cancel! Recorded data has been discarded!')
        self.trigger = False
        self.recording = False
        self.recorded_data = []
           
    def record_data(self,data):
        """
        Append recorded chunk to recorder_data
        and stop doing so if neccessary amount of chunks is recorded
        """
        #data = cp.copy(self.buffer[self.next_chunk-1])
        self.recorded_data.append(data)
        # Check to see whether recording is done
        self.next_rec_chunk += 1
        if self.next_rec_chunk == self.total_rec_chunk:
            self._record_stop()
          
    def flush_record_data(self):
        """
        Add in any partial posttrigger data
        Slice the recorded data into the requested amount of samples
        Add in any pretrigger data
        
        Returns
        ----------
            flushed_data: numpy array
                2D numpy array (similar to get_buffer) 
        """
        if self.recorded_data:
            data =  np.array(self.recorded_data);
            flushed_data = data.reshape((self.rec_samples,self.channels))
            if self.part_posttrig_data.shape[0]:
                flushed_data = np.vstack((self.part_posttrig_data,flushed_data))
            
            flushed_data = flushed_data[:self.actual_rec_samples,:]

            self.recorded_data = []
            if self.pretrig_data.shape[0]:
                flushed_data = np.vstack((self.pretrig_data,flushed_data))
                
            print('Data flushed')
            return flushed_data               
                            

#---------------- STREAMING METHODS ----------------------------------- 
    @abstractmethod                                    
    def stream_init(self, playback = False):
        """
        Callback function for initialising audio streaming.
                
        Parameters
        ----------
            playback: Bool
                Whether to output the stream to a device
            
        Returns
        ----------
            True if successful, False otherwise
        """
        pass
            
    @abstractmethod 
    def stream_start(self):
        """
        Callback function for starting the audio streaming.
        """
        pass
    @abstractmethod 
    def stream_stop(self):
        """
        Callback function for stopping the audio streaming.
        """
        pass
        
    @abstractmethod 
    def stream_close(self):
        """
        Callback function for closing the audio streaming.
        """
        pass
#---------------- TRIGGER METHODS -----------------------------------
    def trigger_init(self):
        """
        Initialise the variable for the trigger recording
        """
        self.trigger = False
        self.trigger_threshold = 0
        self.trigger_channel = 0
        self.ref_level = 0.08
        self.pretrig_samples = 200
        self.pretrig_data = np.array([])
        self.part_posttrig_data = np.array([])
        
    def trigger_start(self,duration = 3, threshold = 0.09, channel = 0,pretrig = 200,posttrig = 5000):
        """
        Start the trigger if possible
        
        Returns
        ----------
            True if successful, False otherwise
        """
        if self.recording:
            print('You are current recording. Please finish the recording before starting the trigger.')
            return False
        
        if not self.trigger:
            if not self.record_init(samples = posttrig):
                return False
            self.trigger = True
            self.trigger_threshold = threshold
            self.trigger_channel = channel
            self.pretrig_samples = pretrig
            self.ref_level = np.mean(self.buffer[self.next_chunk,:,self.trigger_channel])
            print('Reference level: %.2f' % self.ref_level)
            print('Trigger Set!')
            return True
        else:
            print('You have already started a trigger')
            return False

    def _trigger_check_threshold(self,data):
        """
        Check if the trigger is set off
        Start recording if so and emit a signal if possible
        
        Parameters
        ----------
            data: Numpy Array
                data to be analysed
        """
        trig_data = data[:,self.trigger_channel]
        norm_data = abs(trig_data - np.mean(trig_data))#- self.ref_level
        
        maximum = np.amax(norm_data)
        
        if maximum > self.trigger_threshold:
            print('Triggered!')
            pos = np.argmax(norm_data)
            self.recording = True
            self.trigger = False
            try:
                self.part_posttrig_data =  cp.copy(self.buffer[self.next_chunk-1, pos:,:])
                temp = np.vstack((self.buffer[self.next_chunk-2,:,:],self.buffer[self.next_chunk-1,:pos,:]))
                self.pretrig_data = temp[temp.shape[0]-self.pretrig_samples:,:]
            except Exception as e:
                print(e)
                print('Cannot get trigger data')
            if self.rEmitter:
                self.rEmitter.triggered.emit()
            
#----------------- DECORATOR METHODS --------------------------------------
    @property
    def num_chunk(self):
        """
        int: 
            Number of chunks to store in circular buffer
            The setter method will calculate the maximum possible number of chunks
            based on an arbitrary number of sample limit (2^25 in here)
        """
        return self._num_chunk

    @num_chunk.setter
    def num_chunk(self, num_chunks):
        n = max(1, int(num_chunks))
        try:
            if n * self.chunk_size > 2**25:
                n = 2**16 // self.chunk_size
            self._num_chunk = n
            self.allocate_buffer()
            #print(self._num_chunk)
        except Exception as e:
            #print(e)
            self._num_chunks = n
        
        
    @property
    def chunk_size(self):
        """
        int: 
            Number of samples to get from each channel in one chunk
            The setter method will calculate the maximum possible size
            based on an arbitrary number of sample limit (2^25 in here)
        """
        return self._chunk_size

    @chunk_size.setter
    def chunk_size(self, chunk_size):
        n = max(1, int(chunk_size))
        try:
            if n * self.num_chunk > 2**25:
                n = 2**16 // self.num_chunk
            self._chunk_size = n
            #print(self._chunk_size)
            self.allocate_buffer()
        except Exception as e:
            #print(e)
            self._chunk_size = n

            
                                  
 