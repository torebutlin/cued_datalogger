from Recorder import *
import matplotlib.pyplot as plt
DURATION = 30

fig = plt.figure()
ax = fig.add_subplot(111)
ax.set_ylim(-5e4,5e4)
fig.show()

try:
    rec = Recorder(1,44100,1024,'Line (U24XL with SPDIF I/O)')
    rec.stream_init(playback = True)
except:
    quit()

line = ax.plot(range(len(rec.signal_data)),
                       rec.signal_data)[0]

try:
    while True:
    #for _ in range(DURATION * 100):
        line.set_ydata(rec.signal_data)
        fig.canvas.draw()
        fig.canvas.flush_events()
except:
    print('Some error happened!')
finally:
    rec.stream_stop()
    rec.close()
    plt.close(fig)