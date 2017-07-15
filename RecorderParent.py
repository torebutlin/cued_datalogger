# -*- coding: utf-8 -*-
"""
Created on Sat Jul 15 20:01:58 2017

@author: En Yi
"""
from abc import ABCMeta
import numpy as np
import copy as cp

class RecorderParent(object):
    __metaclass__ = ABCMeta
#---------------- INITIALISATION METHODS -----------------------------------    
    def __init__(self,channels = 1,rate = 44100, chunk_size = 1024,
                 num_chunk = 4):
        self.channels = channels
        self.rate = rate
        self.chunk_size = chunk_size
        self.num_chunk = num_chunk;
        self.audio_stream = None
        
        self.allocate_buffer()
        
    def open_recorder(self):
        self.recording = False
        self.recorded_data = []
        
        # Set up the buffer         
    def allocate_buffer(self):
        self.buffer = np.zeros(shape = (self.num_chunk,
                                        self.chunk_size,
                                        self.channels))
        self.next_chunk = 0;

#---------------- DESTRUCTOR METHODS -----------------------------------     
    def __del__(self):
        self.close()
   
    # Close the audio object, to be called if streaming is no longer needed        
    def close(self):
        self.stream_close()
    
    def set_device_by_name(self, name):
        pass
        
    def available_devices(self):
        pass
    
    def current_device_info(self):
        pass
    
    def set_filename(self,filename):
        self.filename = filename
        
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
    def stream_init(self, playback = False):
        pass
            
    # Start the streaming
    def stream_start(self):
        pass
    # Stop the streaming
    def stream_stop(self):
        pass
        
    # Close the stream, probably needed if any parameter of the stream is changed
    def stream_close(self):
        pass

#----------------- DECORATOR METHODS --------------------------------------
    @property
    def num_chunk(self):
        return self._num_chunk

    @num_chunk.setter
    def num_chunk(self, num_chunks):
        n = max(1, int(num_chunks))
        try:
            if n * self.chunk_size > 2**16:
                n = 2**16 // self.chunk_size
            self._num_chunk = n
            self.allocate_buffer()
        except Exception as e:
            print(e)
            self._num_chunks = n
        
    @property
    def chunk_size(self):
        return self._chunk_size

    @chunk_size.setter
    def chunk_size(self, chunk_size):
        n = max(1, int(chunk_size))
        try:
            if n * self.num_chunk > 2**16:
                n = 2**16 // self.num_chunk
            self._chunk_size = n
            self.allocate_buffer()
        except Exception as e:
            print(e)
            self._chunk_size = n
            
                                  
 