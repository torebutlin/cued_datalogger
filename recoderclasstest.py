from Recorder import *
#import matplotlib.pyplot as plt


rec = Recorder(1,44100,1024,'Line (U24XL with SPDIF I/O)')
#rec.current_device_info()
#audio_data = rec.record(3)
#rec.play_recording()
try:
    rec.stream_audio(20,playback = True)
except:
    rec.close()

#plt.plot(np.array(range(len(audio_data)))/44100,audio_data)
#plt.show()


