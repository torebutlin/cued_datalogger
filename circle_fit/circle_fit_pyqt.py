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
    wmin, wmax = p1.getAxis('bottom').range
    #dmin, dmax = p1.getAxis('left').range
    
    lower = np.where(w>wmin)[0][0]
    upper = np.where(w<wmax)[0][-1]
    
    d_ = d[lower:upper]
    
    p2.clear()
    p2.plot(d_.real, d_.imag)

    p3.clear()
    x0, y0, R0 = circle_fit(d_)
    x_c, y_c = circle_plot(x0, y0, R0)
    p3.plot(d_.real, d_.imag, pen=pg.mkPen(width=4))
    p3.plot(x_c, y_c, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DashLine))


from pyqtgraph.Qt import QtCore
import pyqtgraph as pg

# Create a demo FRF
w = np.linspace(0, 25 ,1e5)
d = 20*np.log10(func(w, 10, 1e-2, 8e12+1e9j) + func(w, 5, 1e-1, 8e12+1e9j) + func(w, 20, 5e-2, 8e12+1e9j) + func(w, 12, 2e-2, 8e12+1e9j))


win = pg.GraphicsWindow(title="Circle Fit")

# Transfer fn
p1 = win.addPlot(title="Transfer function", x=w, y=np.abs(d))
p_select = win.addPlot(title="Region Selection", x=w, y=np.abs(d))
lr_x = pg.LinearRegionItem([w.min(), w.max()], orientation=pg.LinearRegionItem.Vertical)
lr_y = pg.LinearRegionItem([d.min(), d.max()], orientation=pg.LinearRegionItem.Horizontal)
lr_x.setZValue(-10)
lr_y.setZValue(-10)
p_select.addItem(lr_x)
p_select.addItem(lr_y)


def update_zoom():
    p1.setXRange(*lr_x.getRegion(), padding=0)
    p1.setYRange(*lr_y.getRegion(), padding=0)

def update_region():
    lr_x.setRegion(p1.getViewBox().viewRange()[0])
    lr_y.setRegion(p1.getViewBox().viewRange()[1])
    
lr_x.sigRegionChanged.connect(update_zoom)
lr_x.sigRegionChanged.connect(update_plots)
lr_y.sigRegionChanged.connect(update_zoom)
lr_y.sigRegionChanged.connect(update_plots)
p1.sigXRangeChanged.connect(update_region)
p1.sigXRangeChanged.connect(update_plots)
update_zoom()

win.nextRow()
# Nyquist
p2 = win.addPlot(title="Nyquist plot")
# Circle
p3 = win.addPlot(title="Nyquist plot with circle fit")
   
update_plots()





