import weakref
import sys
if __name__ == '__main__':
    sys.path.append('../../')
import numpy as np
import pyqtgraph as pg
from pyqtgraph import ImageItem
from cued_datalogger.api.pyqt_widgets import matplotlib_lookup_table
from PyQt5.QtWidgets import(QWidget,QMenu,QAction,QActionGroup,QWidgetAction,QGridLayout,
                            QCheckBox,QRadioButton,QLineEdit,QSpinBox,QComboBox,
                            QLabel, QApplication, QVBoxLayout, QHBoxLayout, QPushButton)
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import QMetaObject,QSize,QCoreApplication, QTimer, pyqtSignal


class InteractivePlotWidget(QWidget):
    """A QWidget containing a :class:`CustomPlotWidget` with mouse tracking
    crosshairs, a :class:`LinearRegionItem`, and spinboxes
    to display and control the values of the bounds of the linear region.
    Any additional arguments to :method:`__init__` are passed to the
    CustomPlotWidget.

    Attributes
    ----------
    PlotWidget : pg.PlotWidget
        The PlotWidget contained in the InteractivePlotWidget.
    ViewBox : pg.ViewBox
        The ViewBox contained in the InteractivePlotWidget.
    region : pg.LinearRegionItem
        The LinearRegionItem contained in the InteractivePlotWidget.
    vline : pg.InfiniteLine
        Vertical mouse-tracking line.
    hline : pg.InfiniteLine
        Horizontal mouse-tracking line.
    label : pg.LabelItem
        LabelItem displaying current mouse position.
    lower_box : QSpinBox
        QSpinBox displaying lower bound of :attr:`region`.
    upper_box : QSpinBox
        QSpinBox displaying upper bound of :attr:`region`.
    zoom_btn : QPushButton
        Press to zoom to the :attr:`region` with a set amount of padding.
    show_region : bool
        Controls whether the region is displayed.
    show_crosshair : bool
        Controls whether the crosshair is displayed.
    sig_region_changed : pyqtSignal([int, int])
        The signal emitted when the region is changed.
    """

    sig_region_changed = pyqtSignal([float, float])

    def __init__(self, parent=None,
                 show_region=True, show_crosshair=True, show_label=True,
                 *args, **kwargs):
        self.parent = parent

        super().__init__(parent)

        layout = QVBoxLayout(self)

        # # Set up the PlotWidget
        self.PlotWidget = CustomPlotWidget(self, show_region=show_region,
                                           show_crosshair=show_crosshair,
                                           show_label=show_label,
                                           *args, **kwargs)

        self.PlotWidget.region.sigRegionChanged.connect(self.updateBoxFromRegion)

        self.PlotItem = self.PlotWidget.PlotItem
        self.ViewBox = self.PlotWidget.ViewBox

        layout.addWidget(self.PlotWidget)

        # # Set up the region controls
        control_layout = QHBoxLayout()
        self.lower_box = pg.SpinBox(self, bounds=(None, None))
        self.lower_box.valueChanged.connect(self.updateRegionFromBox)
        self.lower_box_proxy = pg.SignalProxy(self.lower_box.valueChanged,
                                              rateLimit=30,
                                              slot=self.on_region_changed)
        self.upper_box = pg.SpinBox(self, bounds=(None, None))
        self.upper_box_proxy = pg.SignalProxy(self.upper_box.valueChanged,
                                              rateLimit=30,
                                              slot=self.on_region_changed)
        self.upper_box.valueChanged.connect(self.updateRegionFromBox)

        self.zoom_btn = QPushButton('Zoom', self)
        self.zoom_btn.clicked.connect(self.zoomToRegion)

        control_layout.addWidget(QLabel('Lower', self))
        control_layout.addWidget(self.lower_box)
        control_layout.addWidget(QLabel('Upper', self))
        control_layout.addWidget(self.upper_box)
        control_layout.addWidget(self.zoom_btn)
        layout.addLayout(control_layout)

        self.clear()

    def getPlotItem(self):
        return self.PlotItem

    def on_region_changed(self):
        lower = self.lower_box.value()
        upper = self.upper_box.value()
        self.sig_region_changed.emit(lower, upper)

    def clear(self):
        """Clear the PlotWidget and add the default items back in."""
        self.PlotWidget.clear()

    def updateRegionFromBox(self):
        # Get the bounds of the region as defined by the spinboxes
        region_bounds = [self.lower_box.value(),
                         self.upper_box.value()]
        # Sort them so that the lower one is first
        region_bounds.sort()
        # Update the region
        self.PlotWidget.region.setRegion(region_bounds)
        # Update the spinboxes
        self.lower_box.setValue(region_bounds[0])
        self.upper_box.setValue(region_bounds[1])

    def updateBoxFromRegion(self):
        # Get the region bounds as defined by the region
        region_bounds = list(self.PlotWidget.region.getRegion())
        # Sort it so the lowest is first
        region_bounds.sort()
        # Set the spinboxes to reflect the bounds of the region
        self.lower_box.setValue(region_bounds[0])
        self.upper_box.setValue(region_bounds[1])

    def zoomToRegion(self, padding=0.1):
        """Zoom to the region, with given padding."""
        lower, upper = self.PlotWidget.region.getRegion()
        self.PlotItem.setXRange(lower, upper, padding=padding)

    def getRegionBounds(self):
        """Return the lower and upper bounds of the region."""
        return self.lower_box.value(), self.upper_box.value()

    def plot(self, x=None, y=None, *args, **kwargs):
        """:func:`update_limits` from the x and y values, then plot
        the data on the plotWidget."""
        self.PlotWidget.plot(x, y, *args, **kwargs)

    def update_limits(self, x, y):
        """Set the increment of the spinboxes, the limits of zooming and
        scrolling the PlotItem, and move the region to x=0"""
        if x is not None and y is not None:
            # Update the increment of the spinboxes
            try:
                self.lower_box.setSingleStep(x.max()/100)
                self.upper_box.setSingleStep(x.max()/100)

                # Set the linear region to be in view
                #self.lower_box.setValue(x.max()*0.4)
                #self.upper_box.setValue(x.max()*0.6)
                #self.lower_box.setValue(0)
                #self.upper_box.setValue(0)

                # Set the limits of the PlotItem
                self.PlotItem.setLimits(xMin=x.min(), xMax=x.max())
                self.PlotItem.setRange(xRange=(x.min(), x.max()),
                                       yRange=(y.min(), y.max()),
                                       padding=0.2)
            except:
                print("Error in scaling limits.")


class CustomPlotWidget(pg.PlotWidget):
    def __init__(self, *args,
                 show_region=True, show_crosshair=True, show_label=True,
                 **kwargs):

        self.show_region = show_region
        self.show_crosshair = show_crosshair
        self.show_label = show_label

        super().__init__(*args, **kwargs)

        self.PlotItem = self.getPlotItem()
        self.PlotItem.disableAutoRange()
        self.ViewBox = self.PlotItem.getViewBox()

        #------------- Manually override wrapped methods ----------------------
        # Pyqtgraph's PlotWidget wraps some methods from PlotItem and ViewBox
        # In order to use our defined functions for these methods, we need
        # to override them using setattr rather than just redefining them
        methods_to_override = ["plot", "clear", "autoRange"]

        for method in methods_to_override:
            setattr(self, method, getattr(self, method + "_override"))

        #--------------------- Add default items ------------------------------
        # # Crosshair
        self.crosshair_x = pg.InfiniteLine(angle=0)
        self.crosshair_y = pg.InfiniteLine(angle=90)
        self.proxy = pg.SignalProxy(self.scene().sigMouseMoved, rateLimit=30,
                                    slot=self.mouseMoved)
        self.PlotItem.addItem(self.crosshair_y)
        self.PlotItem.addItem(self.crosshair_x)

        # # Region
        self.region = pg.LinearRegionItem(values=[0,0])
        self.PlotItem.addItem(self.region)

        # # Label
        self.label = pg.LabelItem(angle = 0)
        self.label.setParentItem(self.ViewBox)

        #---------------- Customise menus -------------------------------------
        # # Customise the plot item menu
        self.plotitem_menu = self.PlotItem.ctrlMenu
        self.plotitem_controls = self.PlotItem.ctrl

        for action in self.plotitem_menu.actions():
            # Remove all but two actions
            if action.text() not in ["Alpha", "Grid"]:
                self.plotitem_menu.removeAction(action)
            # Rename Alpha -> Transparency (easier to understand)
            if action.text() == "Alpha":
                action.setText("Transparency")
                self.plotitem_controls.alphaGroup.setTitle("Enable "
                                                           "transparency")

        self.show_crosshair_action = QAction("Show crosshair")
        self.show_crosshair_action.setCheckable(True)
        self.show_crosshair_action.triggered.connect(self.set_show_crosshair)
        self.show_crosshair_action.setChecked(self.show_crosshair)
        self.plotitem_menu.addAction(self.show_crosshair_action)

        self.show_region_action = QAction("Show region")
        self.show_region_action.setCheckable(True)
        self.show_region_action.triggered.connect(self.set_show_region)
        self.show_region_action.setChecked(self.show_region)
        self.plotitem_menu.addAction(self.show_region_action)

        self.show_label_action = QAction("Show Label")
        self.show_label_action.setCheckable(True)
        self.show_label_action.triggered.connect(self.set_show_label)
        self.show_label_action.setChecked(self.show_label)
        self.plotitem_menu.addAction(self.show_label_action)

        # # Customise the view box menu
        self.viewbox_menu = self.ViewBox.menu

        # Get rid of the current AutoRange action
        for action in self.viewbox_menu.actions():
            if action.text() == "View All":
                self.viewbox_menu.removeAction(action)

        # Add in our own AutoRange action
        self.autorange_action = QAction("Autorange", self)
        self.autorange_action.triggered.connect(self.autoRange)
        self.viewbox_menu.insertAction(self.viewbox_menu.actions()[0],
                                       self.autorange_action)

    #--------------------- Plot configuration ---------------------------------
    def mouseMoved(self, mouse_moved_event):
        """
        Update the crosshair and label to match the mouse position.
        """
        # Using a signal proxy turns the event into a tuple
        mouse_position = mouse_moved_event[0]

        # Check if the mouse is in the PlotItem
        if self.PlotItem.sceneBoundingRect().contains(mouse_position):
            # Convert it to the coordinate system
            try:
                mouse_point = self.ViewBox.mapSceneToView(mouse_position)
                # Update the label
                self.label.setText("<span style='font-size: 12pt;"
                                     "color: black'>"
                                     "x={:.2e},"
                                     "<span style='color: red'>"
                                     "y={:.2e}</span>".format(mouse_point.x(),
                                                              mouse_point.y()))
                self.crosshair_y.setPos(mouse_point.x())
                self.crosshair_x.setPos(mouse_point.y())

            except np.linalg.LinAlgError:
                print("Warning: Exception raised in calculating mouse position"
                      " (np.linalg.LinAlgError)")

    def autoRange_override(self, padding=None, items=None):
        """Autorange the view to fit the plotted data, ignoring the location
        of the crosshair. Accessed as :func:`autoRange`, not as
        :func:`autoRange_override`.
        """
        if items is None:
            items = self.PlotItem.items
        if self.crosshair_x in items:
            items.remove(self.crosshair_x)
        if self.crosshair_y in items:
            items.remove(self.crosshair_y)

        self.ViewBox.autoRange(padding=padding, items=items)

    def set_show_crosshair(self, show_crosshair):
        """Set whether the crosshair is visible."""
        self.show_crosshair = show_crosshair

        if self.show_crosshair:
            self.addItem(self.crosshair_x)
            self.addItem(self.crosshair_y)
        else:
            self.removeItem(self.crosshair_x)
            self.removeItem(self.crosshair_y)

    def set_show_region(self, show_region):
        """Set whether the region is visible."""
        self.show_region = show_region

        if self.show_region:
            self.addItem(self.region)
        else:
            self.removeItem(self.region)

    def set_show_label(self, show_label):
        """Set whether the label is visible."""
        self.show_label = show_label

        if self.show_label:
            self.label.show()
        else:
            self.label.hide()

    #-------------------- Plot interaction ------------------------------------
    def plot_override(self, *args, **kwargs):
        """Plot data on the widget and autoRange.
        Accessed as :func:`plot`, not as :func:`plot_override`."""

        self.PlotItem.plot(*args, **kwargs)
        self.autoRange(padding=0)

    def clear_override(self, *args, **kwargs):
        """Clear the PlotItem and add the default items back in.
        Accessed as :func:`clear`, not as :func:`clear_override`."""
        self.PlotItem.clear()
        self.set_show_crosshair(self.show_crosshair)
        self.set_show_region(self.show_region)


class ColorMapPlotWidget(InteractivePlotWidget):
    """An InteractivePlotWidget optimised for plotting color(heat) maps.
    Uses the Matplotlib colormap given by *cmap* to color the map.

    Attributes
    ----------
    lookup_table : ndarray
        The lookup table generated from *cmap* to colour the image with
    num_contours : int
        The number of different colour levels to plot
    contour_spacing : int
        How closely spaced the colour levels are
    """
    def __init__(self, parent=None, cmap="jet"):
        self.lookup_table = matplotlib_lookup_table(cmap)
        self.num_contours = 5
        self.contour_spacing_dB = 5
        self.parent = parent
        super().__init__(parent=self.parent)

    def plot_colormap(self, x, y, z, num_contours=5, contour_spacing_dB=5):
        """Plot *x*, *y* and *z* on a colourmap, with colour intervals defined
        by *num_contours* at *contour_spacing_dB* intervals."""

        #self.PlotWidget.removeItem(self.z_img)

        self.x = x
        self.y = y
        self.z = z

        self.num_contours = num_contours
        self.contour_spacing_dB = contour_spacing_dB
        self.update_lowest_contour()

        # Set up axes:
        x_axis = self.PlotWidget.getAxis('bottom')
        y_axis = self.PlotWidget.getAxis('left')

        self.x_scale_fact = self.get_scale_fact(x)
        self.y_scale_fact = self.get_scale_fact(y)

        x_axis.setScale(self.x_scale_fact)
        y_axis.setScale(self.y_scale_fact)

        #self.autoRange()

        self.z_img = ImageItem(z.transpose())
        self.z_img.setLookupTable(self.lookup_table)
        self.z_img.setLevels([self.lowest_contour, self.highest_contour])

        self.PlotWidget.addItem(self.z_img)

        self.PlotWidget.autoRange()
        #self.PlotWidget.ViewBox.autoRange()

    def get_scale_fact(self, var):
        return var.max() / var.size

    def update_lowest_contour(self):
        """Find the lowest contour to plot, as determined by the number of
        contours and the contour spacing."""
        self.lowest_contour = self.z.max() - (self.num_contours * self.contour_spacing_dB)
        self.highest_contour = self.z.max()


if __name__ == '__main__':

    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    pg.setConfigOption('antialias', True)
    defaultpen = pg.mkPen('k')

    app = 0
    app = QApplication(sys.argv)
    w = InteractivePlotWidget()
    x = np.linspace(0, 20*np.pi, 1e4)
    y = np.sin(x)
    w.plot(x, y, pen=defaultpen)
    w.show()

    sys.exit(app.exec_())
