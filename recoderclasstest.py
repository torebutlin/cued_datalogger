import pyaudio
from Recorder import *
#import matplotlib.pyplot as plt


rec = Recorder(1,44100,2048,pyaudio.paInt16)
#rec.set_filename('test.wav')
rec.set_device_index(1)
rec.current_device_info()
#audio_data = rec.record(3)
#rec.play_recording()
rec.stream_audio(30,playback = True)
rec.close()

#plt.plot(np.array(range(len(audio_data)))/44100,audio_data)
#plt.show()


