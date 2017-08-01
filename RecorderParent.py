# -*- coding: utf-8 -*-
"""
Created on Sat Jul 15 20:01:58 2017

@author: En Yi


Recorder base class:
- Sets up the buffer and skeleton for audio streaming
- Requires a derived class
- Store data as numpy arrays from recording and audio stream
    which can be accessed for plotting

"""


''' Note to self:
            Each data is int16, so it is 2 bytes per sample.
            A 3 sec recording contains 132300 samples, but 
            considering the chunk is only takes 1024 samples, 
            the nearest possible samples to take is 132096,
            so it would take up 264192 bytes(258kB)
            
            A 1 min recording would take about 5MB, while
            a 30 min recording would take about 151.4MB
            
            Supppose that an array can only contain 2GB (memory limit),
            then the longest possible recording is 24347 secs, which is
            406 mins, which is 6.76 hours.
            
            If instead a limit of 500MB is imposed, then
            the longest recording time is 5944 secs, which is 99 mins.
            
            However, data being processed later on would probably be
            int32 data type (default numpy array), hence the memory is doubled. 
            Taking that into consideration, the longest possible recording time 
            is then halved.''' 
            
from abc import ABCMeta
import numpy as np
import copy as cp

try:
    from RecEmitter import RecEmitter
    QT_EMITTER = True
except Exception as e:
    print(e)
    QT_EMITTER = False

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
        self.show_stream_settings()
        
        self.trigger_init()
        
        # For pyQt implementations
        if QT_EMITTER:
            self.rEmitter = RecEmitter()
        else:
            self.rEmitter = None
        
    def open_recorder(self):
        self.recording = False
        self.initialised_record = False
        self.next_rec_chunk = 0
        self.total_rec_chunk = 0
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
 
#---------------- DESTRUCTOR METHODS -----------------------------------     
    def show_stream_settings(self):
        print('Channels: %i' % self.channels)
        print('Rate: %i' % self.rate)
        print('Chunk size: %i' % self.chunk_size)
        print('Number of chunks: %i' % self.num_chunk)
        
    def set_filename(self,filename):
        self.filename = filename

    def set_device_by_name(self, name):
        pass
        
    def available_devices(self):
        pass
    
    def current_device_info(self):
        pass
    
#---------------- DATA METHODS -----------------------------------
    # Convert data obtained into a proper array
    def audiodata_to_array(self,data):
        return data.reshape((-1,self.channels))/ 2**15
    
#---------------- BUFFER METHODS -----------------------------------
    # Write the data obtained into buffer and move to the next chunk   
    def write_buffer(self,data):
        self.buffer[self.next_chunk,:,:] = data
        self.next_chunk = (self.next_chunk + 1) % self.num_chunk
    
    # Return the buffer data as a 2D array by stitching the chunks together  
    def get_buffer(self):
        return np.concatenate((self.buffer[self.next_chunk:],self.buffer[:self.next_chunk]),axis = 0) \
                 .reshape((self.buffer.shape[0] * self.buffer.shape[1],
                           self.buffer.shape[2]))
        
#---------------- RECORDING METHODS -----------------------------------
    def record_init(self,samples = None,duration = 3):
        self.pretrig_data = np.array([])
        self.part_posttrig_data = np.array([])
        if samples:
            self.actual_rec_samples = samples
            self.total_rec_chunk = (samples // self.chunk_size)+1
            self.rec_samples = self.total_rec_chunk * self.chunk_size
        else:
            # Calculate the number of recording chunks
            self.total_rec_chunk = (duration * self.rate // self.chunk_size)
            
        self.next_rec_chunk = 0
        
        self.initialised_record = True
        
        print('Recording function is ready! Use record_start() to start')
    # Function to check before recording
    def _record_check(self):
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
        if not self._record_check():
            return False
                       
        # Start the recording
        if self.initialised_record: 
            self.stream_start()
            self.recording = True
            print('Recording Start!')
            return True
        else:
            print('Record not initialised! Use record_init(duration) first!')
            return False
        
    
     # TODO: Add a function to end a normal recording, (internal only)
    def _record_stop(self):
        # Stop the recording
        self.recording = False
        # Give a signal that recording is done
        print('Recording Done! Please flush the data with flush_record_data().')
        if self.rEmitter:
            print('beep')
            self.rEmitter.recorddone.emit()
            
    def record_cancel(self):
        print('Recording Cancel! Recorded data has been discarded!')
        self.trigger = False
        self.recording = False
        self.recorded_data = []
    
    # Append the current chunk(which is before next_chunk) to recorded data            
    def record_data(self):
        data = cp.copy(self.buffer[self.next_chunk-1])
        self.recorded_data.append(data)
        # Check to see whether recording is done
        self.next_rec_chunk += 1
        if self.next_rec_chunk == self.total_rec_chunk:
            self._record_stop()
        
    # Return the recorded data as 2D numpy array (similar to get_buffer)    
    def flush_record_data(self):
        if self.recorded_data:
            data =  np.array(self.recorded_data);
            flushed_data = data.reshape((self.rec_samples,self.channels))
            if self.part_posttrig_data.shape[0]:
                print('part post')
                flushed_data = np.vstack((self.part_posttrig_data,flushed_data))
            
            print(flushed_data.shape)
            print(flushed_data[0,:])
            flushed_data = flushed_data[:self.actual_rec_samples,:]

            self.recorded_data = []
            print(flushed_data.shape)
            if self.pretrig_data.shape[0]:
                flushed_data = np.vstack((self.pretrig_data,flushed_data))
            print(flushed_data.shape)
            #print(flushed_data)
            return flushed_data               
                            

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
#---------------- TRIGGER METHODS -----------------------------------
    def trigger_init(self):
        self.trigger = False
        self.trigger_threshold = 0
        self.trigger_channel = 0
        self.ref_level = 0.08
        self.pretrig_samples = 200
        self.pretrig_data = np.array([])
        self.part_posttrig_data = np.array([])
        
    def trigger_start(self,duration = 3, threshold = 0.09, channel = 0,pretrig = 200,posttrig = 5000):
        if self.recording:
            print('You are current recording. Please finish the recording before starting the trigger.')
            return False
        
        if not self.trigger:
            if not self._record_check():
                return False
            self.record_init(samples = posttrig)
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
        norm_data = abs(data[:,self.trigger_channel])#- self.ref_level
        
        #Calculate RMS of chunk
        maximum = np.amax(norm_data)
        pos = np.argmax(norm_data)
        
        if maximum > self.trigger_threshold:
            print('Triggered!')
            self.recording = True
            self.trigger = False
            try:
                self.part_posttrig_data =  cp.copy(self.buffer[self.next_chunk-1, pos:,:])
                temp = np.vstack((self.buffer[self.next_chunk-2,:,:],self.buffer[self.next_chunk-1,:pos,:]))
                self.pretrig_data = temp[temp.shape[0]-self.pretrig_samples:,:]
            except Exception as e:
                print(e)
                print('Cannot get trigger data')
            self.rEmitter.triggered.emit()
            
#----------------- DECORATOR METHODS --------------------------------------
    @property
    def num_chunk(self):
        return self._num_chunk

    @num_chunk.setter
    def num_chunk(self, num_chunks):
        n = max(1, int(num_chunks))
        try:
            if n * self.chunk_size > 2**25:
                n = 2**16 // self.chunk_size
            self._num_chunk = n
            self.allocate_buffer()
            print(self._num_chunk)
        except Exception as e:
            #print(e)
            self._num_chunks = n
        
        
    @property
    def chunk_size(self):
        return self._chunk_size

    @chunk_size.setter
    def chunk_size(self, chunk_size):
        n = max(1, int(chunk_size))
        try:
            if n * self.num_chunk > 2**25:
                n = 2**16 // self.num_chunk
            self._chunk_size = n
            print(self._chunk_size)
            self.allocate_buffer()
        except Exception as e:
            #print(e)
            self._chunk_size = n

            
                                  
 