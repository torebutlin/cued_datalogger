import myRecorder as rcd
import matplotlib.pyplot as plt
import numpy as np

DURATION = 30

fig = plt.figure()
ax = fig.add_subplot(211)
ax.set_ylim(-2**7,2**7)
ax2 = fig.add_subplot(212)
ax2.set_ylim(-2**7,2**7)
fig.show()
data_array = []


try:
    rec = rcd.Recorder(channels = 2,
                       rate = 44100,
                       chunk_size = 1024,
                       num_chunk = 4,
                       device_name = 'Line (U24XL with SPDIF I/O)')
    rec.stream_init(playback = False)
except Exception as e:
    print(e)
    quit()
#rec.current_device_info()
data = rec.get_buffer()
print(data.shape)

line = ax.plot(range(len(rec.get_buffer())),data[:,0])[0]
line2 = ax2.plot(range(len(rec.get_buffer())),data[:,1])[0]
#data_array= np.append(data_array,rec.signal_data)

#line2 = ax2.plot(range(5),range(5))[0]

samples = 100
                       
try:
    while True:
    #for _ in range(samples):
        #data_array= np.append(data_array,rec.signal_data)
        #print(data_array)
        #ax2.cla()
        #ax2.plot(range(len(data_array)),data_array)
        data = rec.get_buffer()
        line.set_ydata(data[:,0])
        line2.set_ydata(data[:,1])
        fig.canvas.draw()
        fig.canvas.flush_events()
        
except Exception as e:
    print('Some error happened!')
    print(e)
finally:
    rec.stream_stop()
    rec.close()
    #plt.close(fig)
    