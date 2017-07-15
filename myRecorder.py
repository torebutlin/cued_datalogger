"""
Recorder class:
- Allow recording and configurations of recording device
- Allow audio stream
- Store data as numpy arrays for both recording and audio stream
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


# Add codes to install pyaudio if pyaudio is not installed
import pyaudio
import numpy as np
import pprint as pp
import copy as cp

class Recorder():
#---------------- INITIALISATION METHODS -----------------------------------
    def __init__(self,channels = 1,rate = 44100, chunk_size = 1024,
                 num_chunk = 4,device_name = None):
        self.channels = channels
        self.rate = rate
        self.chunk_size = chunk_size
        self.num_chunk = num_chunk;
        self.audio_stream = None
        
        print('You are using pyAudio for recording')
        self.p = None
        self.format = pyaudio.paInt16
        self.device_index = None;
        
        self.open_recorder()
        self.allocate_buffer()
        
        self.set_device_by_name(str(device_name))


    def __del__(self):
        self.close()
        
    def open_recorder(self):
        if self.p == None:
            self.p = pyaudio.PyAudio()
        self.recording = False
        self.recorded_data = []
        
        
                     
    # Set up the buffer         
    def allocate_buffer(self):
        self.buffer = np.zeros(shape = (self.num_chunk,
                                        self.chunk_size,
                                        self.channels))
        self.next_chunk = 0;
            
#---------------- DEVICE SETTING METHODS -----------------------------------            
     # Set the recording audio device by name, 
     # revert to default if no such device found
     # TODO: Change to do Regular Expression???
    def set_device_by_name(self, name):
        dev_name,dev_index = self.available_devices()
        if not dev_name:
            print("Seems like you don't have any input devices")
            return None
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
                    return None
        except IOError:
            print('Device chosen cannot be found!')
            return None
                    
                
    # Get audio device names, only the ones with inputs 
    def available_devices(self):
        names = [self.p.get_device_info_by_index(i)['name']
                  for i in range(self.p.get_device_count())
                  if self.p.get_device_info_by_index(i)['maxInputChannels']>0]
        
        index = [self.p.get_device_info_by_index(i)['index'] 
                for i in range(self.p.get_device_count())
                if self.p.get_device_info_by_index(i)['maxInputChannels']>0]
        
        return(names,index)
    
     # Display the current selected device info      
    def current_device_info(self):
        pp.pprint(self.p.get_device_info_by_index(self.device_index))
            
    # Originally setting file name   
    def set_filename(self,filename):
        self.filename = filename
    
    # Set the selected device by index, Private Function
    def _set_device_by_index(self,index):
        self.device_index = index;
        print("Selected device: %s" % (self.p.get_device_info_by_index(index)['name']))
        
#---------------- DATA METHODS -----------------------------------
    # Convert data obtained into a proper array
    def audiodata_to_array(self,data):
        return np.frombuffer(data, dtype = np.int16).reshape((-1,self.channels))
    
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
    def stream_audio_callback(self,in_data, frame_count, time_info, status):
        self.write_buffer(self.audiodata_to_array(in_data))
        if self.recording:
            self.record_data()
        return(in_data,pyaudio.paContinue)
    
    # TODO: Check for valid device, channels and all that before initialisation
    def stream_init(self, playback = False):
        if self.audio_stream == None and not self.device_index == None:
            self.audio_stream = self.p.open(channels = self.channels,
                             rate = self.rate,
                             format = self.format,
                             input = True,
                             output = playback,
                             frames_per_buffer = self.chunk_size,
                             input_device_index = self.device_index,
                             stream_callback = self.stream_audio_callback)
            
            print('Input latency: %.3e' % self.audio_stream.get_input_latency())
            print('Output latency: %.3e' % self.audio_stream.get_output_latency())
            print('Read Available: %i' % self.audio_stream.get_read_available())
            print('Write Available: %i' % self.audio_stream.get_write_available())
            
            self.stream_start()
            
    # Start the streaming
    def stream_start(self):
        self.audio_stream.start_stream()
    # Stop the streaming
    def stream_stop(self):
        self.audio_stream.stop_stream()
        
    # Close the stream, probably needed if any parameter of the stream is changed
    def stream_close(self):
        if self.audio_stream and self.audio_stream.is_active():
            if not self.audio_stream.is_stopped():
                self.stream_stop()
            self.audio_stream.close()
            self.audio_stream = None
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
            
#---------------- DESTRUCTOR??? METHODS -----------------------------------
    # Close the audio object, to be called if streaming is no longer needed        
    def close(self):
        self.stream_close()
        if not self.p:
            self.p.terminate()
            self.p = None

