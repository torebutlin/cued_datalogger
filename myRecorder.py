"""
Functions:
- Sets up recording and configurations of recording device
- Sets up audio stream
"""

from RecorderParent import RecorderParent
# Add codes to install pyaudio if pyaudio is not installed
import pyaudio
import numpy as np
import pprint as pp
import copy as cp

class Recorder(RecorderParent):
#---------------- INITIALISATION METHODS -----------------------------------
    def __init__(self,channels = 1,rate = 44100, chunk_size = 1024,
                 num_chunk = 4,device_name = None):
        
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
        
    def open_recorder(self):
        super().open_recorder()
        if self.p == None:
            self.p = pyaudio.PyAudio()

#---------------- DESTRUCTOR METHODS -----------------------------------
    # Close the audio object, to be called if streaming is no longer needed        
    def close(self):
        super().close()
        #self.stream_close()
        if not self.p:
            self.p.terminate()
            self.p = None
            
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
                    #return None
        except IOError:
            print('Device chosen cannot be found!')
            #return None
                    
                
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
        if self.device_index:
            pp.pprint(self.p.get_device_info_by_index(self.device_index))
        else:
            print('No index set')
    
    # Set the selected device by index, Private Function
    def _set_device_by_index(self,index):
        if index:
            self.device_index = index;
            self.device_name = self.p.get_device_info_by_index(index)['name']
            print("Selected device: %s" % self.device_name)
        
#---------------- DATA METHODS -----------------------------------
    # Convert data obtained into a proper array
    def audiodata_to_array(self,data):
        return np.frombuffer(data, dtype = np.int16).reshape((self.chunk_size,self.channels))/ 2**15
                           
#---------------- STREAMING METHODS -----------------------------------
    # Callback function for audio streaming
    def stream_audio_callback(self,in_data, frame_count, time_info, status):
        data_array = self.audiodata_to_array(in_data)
        self.write_buffer(data_array)
        
        # TODO: Add trigger check
        if self.trigger:
            self._trigger_check_threshold(data_array)
            
        if self.recording:
            self.record_data()
            
        return(in_data,pyaudio.paContinue)
    
    # TODO: Check for valid device, channels and all that before initialisation
    def stream_init(self, playback = False):
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
            except Exception as e:
                print(e)
                self.audio_stream = None
                return False
            
            print('Input latency: %.3e' % self.audio_stream.get_input_latency())
            print('Output latency: %.3e' % self.audio_stream.get_output_latency())
            print('Read Available: %i' % self.audio_stream.get_read_available())
            print('Write Available: %i' % self.audio_stream.get_write_available())
            
            self.stream_start()
            return True
        else:
            return False
            
    # Start the streaming
    def stream_start(self):
        if self.audio_stream:
            if self.audio_stream.is_stopped():
                self.audio_stream.start_stream()
            else:
                print('Stream already started')
        else:
            print('No audio stream is set up')
            
    # Stop the streaming
    def stream_stop(self):
        if self.audio_stream: 
            if not self.audio_stream.is_stopped():
                self.audio_stream.stop_stream()
            else:
                print('Stream already stopped')
        else:
            print('No audio stream is set up')
        
    # Close the stream, probably needed if any parameter of the stream is changed
    def stream_close(self):
        if self.audio_stream and self.audio_stream.is_active():
            self.stream_stop()
            self.audio_stream.close()
            self.audio_stream = None
            
    #---------------- RECORD TRIGGER METHODS ----------------------------------
    '''def trigger_init(self):
        self.trigger = False
        self.trigger_threshold = 0
        self.trigger_channel = 0
        self.ref_rms = 0'''
    
    def trigger_start(self,duration = 3, threshold = 0.09, channel = 0):
        if self.recording:
            print('You are current recording. Please finish the recording before starting the trigger.')
            return False
        
        if not self.trigger:
            if not self._record_check():
                return False
            self.record_init(duration = duration)
            self.trigger = True
            self.trigger_threshold = threshold
            self.trigger_channel = channel
            self.ref_level = np.mean(self.buffer[self.next_chunk,:,self.trigger_channel])
            print('Reference level: %.2f' % self.ref_level)
            print('Trigger Set!')
            return True
        else:
            print('You have already started a trigger')
            return False

    def _trigger_check_threshold(self,data):
        #Calculate RMS of chunk
        norm_data = data[:,self.trigger_channel]
        rms = np.sqrt(np.mean(norm_data ** 2))
        print(rms - self.ref_level)
        
        if abs(rms - self.ref_level) > self.trigger_threshold:
            print('Triggered!')
            self.recording = True
            self.trigger = False
            self.pretrig_data = cp.copy(self.buffer[self.next_chunk-2,:,:])
            
        
        
            
            
            
            
            
            
            
            
            
            
            
            
            
        