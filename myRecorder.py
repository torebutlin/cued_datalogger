"""
Recorder class:
- Allow recording and configurations of recording device
- Allow audio stream
- Store data as numpy arrays for both recording and audio stream
    which can be accessed for plotting
"""

# Add codes to install pyaudio if pyaudio is not installed
import pyaudio
import numpy as np
import wave
import pprint as pp

class Recorder():
#---------------- INITIALISATION METHODS -----------------------------------
    # TODO: Account for different audio format during plotting
    def __init__(self,channels = 1,rate = 44100, chunk_size = 1024,
                 num_chunk = 4,device_name = None):
        self.channels = channels
        self.rate = rate
        self.chunk_size = chunk_size
        self.format = pyaudio.paInt16
        self.filename = None
        self.p = None
        self.device_index = 0;
        self.signal_data = np.array([0] * self.chunk_size)
        self.audio_stream = None
        self.num_chunk = num_chunk;
        
        self.open_recorder()
        if device_name != None:
            self.set_device_by_name(str(device_name))
            
        self.allocate_buffer()
        
    def open_recorder(self):
        if self.p == None:
            self.p = pyaudio.PyAudio()
            
    def allocate_buffer(self):
        self.buffer = np.zeros(shape = (self.num_chunk,
                                        self.chunk_size,
                                        self.channels))
        self.next_chunk = 0;
            
#---------------- DEVICE SETTING METHODS -----------------------------------            
     # Set the recording audio device by name, 
     # revert to default if no such device found
    def set_device_by_name(self, name):
        try:
            self.set_device_by_index(self.available_devices().index(name))
        except ValueError:
            try:
                print('Device not found, reverting to default')
                default = self.p.get_default_input_device_info()
                self.set_device_by_index(default['index'])
            except IOError:
                print('No default device!')
                
    # Get audio device names 
    def available_devices(self):
        return ([ self.p.get_device_info_by_index(i)['name'] 
                  for i in range(self.p.get_device_count())] )
    
    def set_device_by_index(self,index):
       # TODO: Add check for invalid index input
        self.device_index = index;
        print("Selected device: %s" % (self.p.get_device_info_by_index(index)['name']))
        
    def current_device_info(self):
        pp.pprint(self.p.get_device_info_by_index(self.device_index))
            
    # Originally setting file name   
    def set_filename(self,filename):
        self.filename = filename
        
#---------------- RECORDING METHODS -----------------------------------            
    # Currently it is using blocking method
    # Will remove wave recording in the future. or make it an option???
    def record(self,duration):
        rc = wave.open(self.filename,'wb')
        rc.setnchannels(self.channels)
        rc.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        rc.setframerate(self.rate)
        data_array = []
        input_stream = self.p.open(channels = self.channels,
                         rate = self.rate,
                         format = self.format,
                         input = True,
                         chunk_size = self.chunk_size,
                         input_device_index = self.device_index)

        print('RECORDING...')
        for _ in range(int(self.rate/self.chunk_size * duration)):
            data = input_stream.read(self.chunk_size)
            rc.writeframes(data)
            data_array.append(np.fromstring(data,dtype = np.int16))

        print('RECORDING END')
        rc.close()
        input_stream.stop_stream()
        input_stream.close()

        return np.hstack(data_array)

    # May consider the recording method to be non-blocking
    def record_callback(self,in_data,frame_count,time_info,status_flag):
        #TODO: insert code to record data
        return(data,pyaudio.paContinue)
    
    # Play back a recording    
    def play_recording(self,filename = None):
        if filename == None:
            filename = self.filename
        
        if filename != None:
            wf = wave.open(filename,'rb')

            output_stream = self.p.open(format = self.p.get_format_from_width(wf.getsampwidth()),
                            channels = wf.getnchannels(),
                            rate = wf.getframerate(),
                            output = True)
            
            data = wf.readframes(self.chunk_size)
            print('PLAYBACK...')
            while len(data)>0:
                output_stream.write(data)
                data = wf.readframes(self.chunk_size)
            print('PLAYBACK STOP')
            
            wf.close()
            output_stream.stop_stream()
            output_stream.close()

#---------------- BUFFER METHODS -----------------------------------
    def audiodata_to_array(self,data):
        return np.array(np.frombuffer(data, dtype = np.int16).reshape((-1,self.channels)))
    
    def write_buffer(self,data):
        self.buffer[self.next_chunk,:,:] = self.audiodata_to_array(data)
        self.next_chunk = (self.next_chunk + 1) % self.num_chunk
        
    def get_buffer(self):
        return np.concatenate((self.buffer[self.next_chunk:],self.buffer[:self.next_chunk]),axis = 0) \
                 .reshape((self.buffer.shape[0] * self.buffer.shape[1],
                           self.buffer.shape[2]))
#---------------- STREAMING METHODS -----------------------------------
    # Callback function for audio streaming
    def stream_audio_callback(self,in_data, frame_count, time_info, status):
        self.write_buffer(self.audiodata_to_array(in_data))
        self.signal_data = self.buffer[self.next_chunk-1]
        return(in_data,pyaudio.paContinue)
    
    def stream_init(self, playback):
        if self.audio_stream == None:
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
            
    def stream_start(self):
        self.audio_stream.start_stream()

    def stream_stop(self):
        self.signal_data *= 0 #np.array([0] * self.chunk_size)
        self.buffer *= 0
        self.audio_stream.stop_stream()
    
    def stream_close(self):
        if self.audio_stream.is_active():
            if not self.audio_stream.is_stopped():
                self.stream_stop()
            self.audio_stream.close()
            self.audio_stream = None
            
#---------------- DESTRUCTOR??? METHODS -----------------------------------         
    def close(self):
        self.stream_close()
        self.p.terminate()
        self.p = None

