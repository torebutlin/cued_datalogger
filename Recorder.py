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
    def __init__(self,channels,rate,frames_per_buffer,device_name = None):
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self.format = pyaudio.paInt16
        self.filename = None
        self.p = None
        self.device_index = 0;
        self.signal_data = np.array([0] * frames_per_buffer)
        self.audio_stream = None
        
        self.open_recorder()
        if device_name != None:
            self.set_device_by_name(str(device_name))
        
    def open_recorder(self):
        if self.p == None:
            self.p = pyaudio.PyAudio()
            
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
            
    # Originally setting file name   
    def set_filename(self,filename):
        self.filename = filename
        
    def current_device_info(self):
        pp.pprint(self.p.get_device_info_by_index(self.device_index))

#---------------- RECORDING METHODS -----------------------------------            
    # Currently it is using blocking method
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
                         frames_per_buffer = self.frames_per_buffer,
                         input_device_index = self.device_index)

        print('RECORDING...')
        for _ in range(int(self.rate/self.frames_per_buffer * duration)):
            data = input_stream.read(self.frames_per_buffer)
            rc.writeframes(data)
            data_array.append(np.fromstring(data,dtype = np.int16))

        print('RECORDING END')
        rc.close()
        input_stream.stop_stream()
        input_stream.close()

        return np.hstack(data_array)

    #TODO: Complete callback function for non-blocking method?????
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
            
            data = wf.readframes(self.frames_per_buffer)
            print('PLAYBACK...')
            while len(data)>0:
                output_stream.write(data)
                data = wf.readframes(self.frames_per_buffer)
            print('PLAYBACK STOP')
            
            wf.close()
            output_stream.stop_stream()
            output_stream.close()
            
#---------------- STREAMING METHODS -----------------------------------             
    # Callback function for audio streaming
    def stream_audio_callback(self,in_data, frame_count, time_info, status):
        self.signal_data = np.array(np.fromstring(in_data, dtype = np.int16))
        return(self.signal_data,pyaudio.paContinue)
    
    def stream_init(self, playback):
        if self.audio_stream == None:
            self.audio_stream = self.p.open(channels = self.channels,
                             rate = self.rate,
                             format = self.format,
                             input = True,
                             output = playback,
                             frames_per_buffer = self.frames_per_buffer,
                             input_device_index = self.device_index,
                             stream_callback = self.stream_audio_callback)
            print('Input latency: %.3e' % self.audio_stream.get_input_latency())
            print('Output latency: %.3e' % self.audio_stream.get_output_latency())
            print('Read Available: %i' % self.audio_stream.get_read_available())
            print('Write Available: %i' % self.audio_stream.get_write_available())
            self.audio_stream.start_stream()
            
    # TODO: Live oscilloscope here?
    # TODO: Learn Python GUI and implement a button to stop and start recording
    # Function for audio streaming for a limited time
    def stream_audio(self):
        return (self.signal_data)
        '''stream = self.p.open(channels = self.channels,
                         rate = self.rate,
                         format = self.format,
                         input = True,
                         output = playback,
                         frames_per_buffer = self.frames_per_buffer,
                         input_device_index = self.device_index,
                         stream_callback = self.stream_audio_callback)'''
        
                                
        '''if draw: 
            fig = plt.figure()
            ax = fig.add_subplot(111)
            ax.set_ylim(-5e4,5e4)
            fig.show()
        
        self.audio_stream.start_stream()
       
        print('STREAMING...')
        print(len(self.signal_data)) 
        line = ax.plot(np.array(range(len(self.signal_data)))/self.rate,
                       self.signal_data)[0]
           
        for i in range(duration*100):               
            line.set_ydata(self.signal_data)
            fig.canvas.draw()
            fig.canvas.flush_events()
                
        print('STREAMING END')'''
        
    def stream_stop(self):  
        self.audio_stream.stop_stream()
        self.audio_stream.close()
        self.audio_stream = None
        self.signal_data = np.array([0] * self.frames_per_buffer)
        '''if draw:
            plt.close(fig)'''
        
    def close(self):
        self.p.terminate()
        self.p = None

