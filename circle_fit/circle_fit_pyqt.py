import numpy as np

def func(w, wr, nr, c):
    return c / (wr**2 - w**2 + 1j * nr * wr**2)

def circle_fit(data):
    # Take the real and imaginary parts
    x = data.real
    y = data.imag
    
    # Use the method from "Theoretical and Experimental Modal Analysis" p221
    # Set up the matrices
    xs = np.sum(x)
    ys = np.sum(y)
    xx = np.square(x).sum()
    yy = np.square(y).sum()
    xy = np.sum(x*y)
    L = data.size
    xxx = np.sum(x*np.square(x))
    yyy = np.sum(y*np.square(y))
    xyy = np.sum(x*np.square(y))
    yxx = np.sum(y*np.square(x))
    
    A = np.asarray([[xx, xy, -xs],
                    [xy, yy, -ys],
                    [-xs, -ys, L]])
    
    B = np.asarray([[-(xxx + xyy)],
                     [-(yyy + yxx)],
                     [xx + yy]])
    
    # Solve the equation
    v = np.linalg.solve(A, B)
    
    # Find the circle parameters
    x0 = v[0]/-2
    y0 = v[1]/-2
    R0 = np.sqrt(v[2] + x0**2 + y0**2)
    return x0, y0, R0

def circle_plot(x0, y0, R0):
    theta = np.linspace(-np.pi, np.pi, 180)
    x = x0[0] + R0[0]*np.cos(theta)
    y = y0[0] + R0[0]*np.sin(theta)
    return x, y

def update_plots():
    wmin, wmax = lr.getRegion()
    
    lower = np.where(w>wmin)[0][0]
    upper = np.where(w<wmax)[0][-1]
    print(lower, upper)

    d_ = d[lower:upper]
    #d_=d
    
    p2.clear()
    p2.plot(d_.real, d_.imag)

    p3.clear()
    x0, y0, R0 = circle_fit(d_)
    x_c, y_c = circle_plot(x0, y0, R0)
    p3.plot(d_.real, d_.imag, pen=pg.mkPen(width=4))
    p3.plot(x_c, y_c, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DashLine))


from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

# Calculate FRF
w = np.linspace(0, 25 ,1e5)
d = func(w, 10, 1e-2, 500j) + func(w, 5, 1e-2, 200j) 


win = pg.GraphicsWindow(title="Circle Fit")

# Transfer fn
p1 = win.addPlot(title="Transfer function", x=w, y=np.abs(d))
p_select = win.addPlot(title="Region Selection", x=w, y=np.abs(d))
lr = pg.LinearRegionItem([w.min(), w.max()])
lr.setZValue(-10)
p_select.addItem(lr)

def update_zoom():
    p1.setXRange(*lr.getRegion(), padding=0)
def update_region():
    lr.setRegion(p1.getViewBox().viewRange()[0])
    
lr.sigRegionChanged.connect(update_zoom)
lr.sigRegionChanged.connect(update_plots)
p1.sigXRangeChanged.connect(update_region)
p1.sigXRangeChanged.connect(update_plots)
update_zoom()

win.nextRow()
# Nyquist
p2 = win.addPlot(title="Nyquist plot")
# Circle
p3 = win.addPlot(title="Nyquist plot with circle fit")
   
update_plots()





