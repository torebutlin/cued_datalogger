if __name__ == '__main__':
    sys.path.append('../../')

import weakref
import sys
import numpy as np
import pyqtgraph as pg
from pyqtgraph import ImageItem
from datalogger.api.pyqt_widgets import matplotlib_lookup_table
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
        self.show_region = show_region
        self.show_crosshair = show_crosshair
        self.show_label = show_label

        super().__init__(parent)

        layout = QVBoxLayout(self)

        # # Set up the PlotWidget
        self.PlotWidget = CustomPlotWidget(self, *args, **kwargs)

        self.PlotItem = self.PlotWidget.getPlotItem()
        self.PlotItem.disableAutoRange()

        self.ViewBox = self.PlotWidget.getViewBox()

        self.vline = pg.InfiniteLine(angle=90)
        self.hline = pg.InfiniteLine(angle=0)

        self.region = pg.LinearRegionItem(bounds=[0, None])
        self.region.sigRegionChanged.connect(self.updateBoxFromRegion)

        layout.addWidget(self.PlotWidget)

        self.label = pg.LabelItem(angle = 0)
        self.label.setParentItem(self.ViewBox)
        #ViewBox.addItem(self.label)

        self.proxy = pg.SignalProxy(self.PlotWidget.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)

        self.ViewBox.menu.sig_show_region.connect(self.set_show_region)
        self.ViewBox.menu.sig_show_crosshair.connect(self.set_show_crosshair)
        self.ViewBox.menu.sig_show_label.connect(self.set_show_label)

        # # Set up the controls
        control_layout = QHBoxLayout()
        self.lower_box = pg.SpinBox(self, bounds=(0, None))
        self.lower_box.valueChanged.connect(self.on_region_changed)
        self.upper_box = pg.SpinBox(self, bounds=(0, None))
        self.upper_box.valueChanged.connect(self.on_region_changed)
        self.zoom_btn = QPushButton('Zoom', self)
        self.zoom_btn.clicked.connect(self.zoomToRegion)

        control_layout.addWidget(QLabel('Lower', self))
        control_layout.addWidget(self.lower_box)
        control_layout.addWidget(QLabel('Upper', self))
        control_layout.addWidget(self.upper_box)
        control_layout.addWidget(self.zoom_btn)
        layout.addLayout(control_layout)

        # # Create a QTimer for smooth updating of the region
        self.updatetimer = QTimer(self)
        self.updatetimer.timeout.connect(self.updateRegionFromBox)
        self.updatetimer.start(20)

        self.clear()

    def on_region_changed(self):
        lower = self.lower_box.value()
        upper = self.upper_box.value()
        self.sig_region_changed.emit(lower, upper)

    def mouseMoved(self, mouse_moved_event):
        mouse_position = mouse_moved_event[0]  ## using signal proxy turns original arguments into a tuple
        # If the mouse is in the PlotItem
        if self.PlotItem.sceneBoundingRect().contains(mouse_position):
            # Convert it to the coordinate system
            mousePoint = self.ViewBox.mapSceneToView(mouse_position)
            # Update the label
            self.label.setText((("<span style='font-size: 12pt;color: black'>"
                                 "x=%0.4f,"
                                 "<span style='color: red'>y1=%0.4f</span>" )
                                % (mousePoint.x(), mousePoint.y()) ))
            self.vline.setPos(mousePoint.x())
            self.hline.setPos(mousePoint.y())

    def clear(self):
        """Clear the PlotItem and add the default items back in."""
        self.PlotItem.clear()
        if self.show_crosshair:
            self.PlotItem.addItem(self.vline)
            self.PlotItem.addItem(self.hline)
        if self.show_region:
            self.PlotItem.addItem(self.region)

    def updateRegionFromBox(self):
        # Get the bounds of the region as defined by the spinboxes
        region_bounds = [self.lower_box.value(), self.upper_box.value()]
        # Sort them so that the lower one is first
        region_bounds.sort()
        # Update the region
        self.region.setRegion(region_bounds)
        # Update the spinboxes
        self.lower_box.setValue(region_bounds[0])
        self.upper_box.setValue(region_bounds[1])

    def updateBoxFromRegion(self):
        # Get the region bounds as defined by the region
        region_bounds = list(self.region.getRegion())
        # Sort it so the lowest is first
        region_bounds.sort()
        # Set the spinboxes to reflect the bounds of the region
        self.lower_box.setValue(region_bounds[0])
        self.upper_box.setValue(region_bounds[1])

    def zoomToRegion(self, padding=0.1):
        """Zoom to the region, with given padding."""
        pos = self.region.getRegion()
        self.PlotItem.setXRange(pos[0],pos[1],padding=padding)

    def getRegionBounds(self):
        """Return the lower and upper bounds of the region."""
        return self.lower_box.value(), self.upper_box.value()

    def closeEvent(self, close_event):
        # Tidy everything up when told to close
        #self.proxy.disconnect()
        if self.updatetimer.isActive():
            self.updatetimer.stop()
        close_event.accept()

    def plot(self, x=None, y=None, *args, **kwargs):
        """:func:`update_limits` from the x and y values, then plot
        the data on the plotWidget."""
        self.update_limits(x, y)
        self.PlotWidget.plot(x, y, *args, **kwargs)
        self.ViewBox.autoRange()

    def update_limits(self, x, y):
        """Set the increment of the spinboxes, the limits of zooming and
        scrolling the PlotItem, and move the region to x=0"""

        if x is not None and y is not None:
            # Update the increment of the spinboxes
            self.lower_box.setSingleStep(x.max()/100)
            self.upper_box.setSingleStep(x.max()/100)

            # Set the linear region to be in view
            #self.lower_box.setValue(x.max()*0.4)
            #self.upper_box.setValue(x.max()*0.6)
            #self.lower_box.setValue(0)
            #self.upper_box.setValue(0)

            # Set the limits of the PlotItem
            self.PlotItem.setLimits(xMin=0, xMax=x.max())
            self.PlotItem.setRange(xRange=(x.min(), x.max()),
                                   yRange=(y.min(), y.max()),
                                   padding=0.2)

    def getPlotItem(self):
        """Return the PlotItem (reimplemented from
        :method:`pg.PlotWidget.getPlotItem`)."""
        return self.PlotWidget.getPlotItem()

    def set_show_crosshair(self, show_crosshair):
        """Set whether the crosshair is visible."""
        self.show_crosshair = show_crosshair

        if self.show_crosshair:
            self.PlotItem.addItem(self.vline)
            self.PlotItem.addItem(self.hline)
        else:
            self.PlotItem.removeItem(self.vline)
            self.PlotItem.removeItem(self.hline)

    def set_show_region(self, show_region):
        """Set whether the region is visible."""
        self.show_region = show_region

        if self.show_region:
            self.PlotItem.addItem(self.region)
        else:
            self.PlotItem.removeItem(self.region)

    def set_show_label(self, show_label):
        """Set whether the label is visible."""
        self.show_label = show_label

        if self.show_label:
            self.label.show()
        else:
            self.label.hide()


class CustomPlotWidget(pg.PlotWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, viewBox=CustomViewBox(cparent=self), **kwargs)

        self.PlotItem = self.getPlotItem()
        self.ViewBox = self.PlotItem.getViewBox()

        # Removing some plot options
        ext_menu = self.PlotItem.ctrlMenu
        ext_submenus = self.PlotItem.subMenus
        ext_menu.removeAction(ext_submenus[1].menuAction())
        ext_menu.removeAction(ext_submenus[2].menuAction())
        ext_menu.removeAction(ext_submenus[3].menuAction())
        ext_menu.removeAction(ext_submenus[5].menuAction())

    def getViewBox(self):
        return self.ViewBox

    def getViewedDataRegion(self, data_for_slice, axis='bottom'):
        """Return the indices of data_for_slice that are currently in the
        visible plot window"""

        # Get the axis limits
        axis_lower, axis_upper = self.PlotItem.getAxis(axis).range

        # The data that is in view is where the data is within the axis limits
        data_in_display = (data_for_slice >= axis_lower) & (data_for_slice <= axis_upper)

        indices_of_data_in_display = np.where(data_in_display)[0]
        return indices_of_data_in_display[0], indices_of_data_in_display[-1]


class CustomViewBox(pg.ViewBox):
    def __init__(self, cparent=None, *arg, **kwarg):
        super().__init__(*arg,**kwarg)
        self.cparent = cparent
        self.menu = CustomViewMenu(self)

    def raiseContextMenu(self, ev):
        menu = self.getMenu(ev)
        print(menu)
        menu.addMenu(self.cparent.getPlotItem().ctrlMenu)
        menu.popup(ev.screenPos().toPoint())

    def autoRange(self, padding= None, items=None):
        super().autoRange(padding=padding, items= None)
        r = self.viewRect()
        self.setLimits(xMin = r.left(), xMax = r.right())


class CustomViewMenu(QMenu):
    sig_show_crosshair = pyqtSignal(bool)
    sig_show_region = pyqtSignal(bool)
    sig_show_label = pyqtSignal(bool)

    def __init__(self, view):
        QMenu.__init__(self)

        self.view = weakref.ref(view)  ## keep weakref to view to avoid circular reference (don't know why, but this prevents the ViewBox from being collected)
        self.valid = False  ## tells us whether the ui needs to be updated
        self.viewMap = weakref.WeakValueDictionary()  ## weakrefs to all views listed in the link combos

        self.setTitle("ViewBox options")
        self.autorange_action = QAction("Autorange", self)
        self.autorange_action.triggered.connect(self.autoRange)
        self.addAction(self.autorange_action)

        # Display menu
        self.display_menu = QMenu("Display options")

        show_crosshair_action = QAction("Show crosshair", self.display_menu)
        show_crosshair_action.setCheckable(True)
        show_crosshair_action.setChecked(True)
        show_crosshair_action.triggered.connect(self.sig_show_crosshair.emit)
        self.display_menu.addAction(show_crosshair_action)

        show_region_action = QAction("Show region", self.display_menu)
        show_region_action.setCheckable(True)
        show_region_action.setChecked(True)
        show_region_action.triggered.connect(self.sig_show_region.emit)
        self.display_menu.addAction(show_region_action)

        show_label_action = QAction("Show Label", self.display_menu)
        show_label_action.setCheckable(True)
        show_label_action.setChecked(True)
        show_label_action.triggered.connect(self.sig_show_label.emit)
        self.display_menu.addAction(show_label_action)

        self.addMenu(self.display_menu)

        self.axes = []
        self.ctrl = []
        self.widgetGroups = []
        self.dv = QDoubleValidator(self)
        for axis in 'XY':
            m = QMenu()
            m.setTitle("%s Axis" % axis)
            w = QWidget()
            ui = CustomUITemplate()
            ui.setupUi(w)
            a = QWidgetAction(self)
            a.setDefaultWidget(w)
            m.addAction(a)
            self.addMenu(m)
            self.axes.append(m)
            self.ctrl.append(ui)
            self.widgetGroups.append(w)

            connects = [
                (ui.mouseCheck.toggled, 'MouseToggled'),
                (ui.manualRadio.clicked, 'ManualClicked'),
                (ui.minText.editingFinished, 'MinTextChanged'),
                (ui.maxText.editingFinished, 'MaxTextChanged'),
                (ui.autoRadio.clicked, 'AutoClicked'),
                (ui.autoPercentSpin.valueChanged, 'AutoSpinChanged'),
                (ui.linkCombo.currentIndexChanged, 'LinkComboChanged'),
                (ui.autoPanCheck.toggled, 'AutoPanToggled'),
                (ui.visibleOnlyCheck.toggled, 'VisibleOnlyToggled')
            ]

            for sig, fn in connects:
                sig.connect(getattr(self, axis.lower()+fn))

        self.ctrl[0].invertCheck.toggled.connect(self.xInvertToggled)
        self.ctrl[1].invertCheck.toggled.connect(self.yInvertToggled)

        self.leftMenu = QMenu("Mouse Mode")
        group = QActionGroup(self)

        pan = QAction("3 button", self.leftMenu)
        zoom = QAction("1 button", self.leftMenu)
        self.leftMenu.addAction(pan)
        self.leftMenu.addAction(zoom)
        pan.triggered.connect(self.set3ButtonMode)
        zoom.triggered.connect(self.set1ButtonMode)

        pan.setCheckable(True)
        zoom.setCheckable(True)
        pan.setActionGroup(group)
        zoom.setActionGroup(group)
        self.mouseModes = [pan, zoom]
        self.addMenu(self.leftMenu)

        self.view().sigStateChanged.connect(self.viewStateChanged)

        self.updateState()

    def viewStateChanged(self):
        self.valid = False
        if self.ctrl[0].minText.isVisible() or self.ctrl[1].minText.isVisible():
            self.updateState()

    def updateState(self):
        ## Something about the ViewBox has changed; update the menu GUI
        state = self.view().getState(copy=False)
        if state['mouseMode'] == pg.ViewBox.PanMode:
            self.mouseModes[0].setChecked(True)
        else:
            self.mouseModes[1].setChecked(True)

        for i in [0,1]:  # x, y
            tr = state['targetRange'][i]
            self.ctrl[i].minText.setText("%0.5g" % tr[0])
            self.ctrl[i].maxText.setText("%0.5g" % tr[1])
            if state['autoRange'][i] is not False:
                self.ctrl[i].autoRadio.setChecked(True)
                if state['autoRange'][i] is not True:
                    self.ctrl[i].autoPercentSpin.setValue(state['autoRange'][i]*100)
            else:
                self.ctrl[i].manualRadio.setChecked(True)
            self.ctrl[i].mouseCheck.setChecked(state['mouseEnabled'][i])

            ## Update combo to show currently linked view
            c = self.ctrl[i].linkCombo
            c.blockSignals(True)
            try:
                view = state['linkedViews'][i]  ## will always be string or None
                if view is None:
                    view = ''

                ind = c.findText(view)

                if ind == -1:
                    ind = 0
                c.setCurrentIndex(ind)
            finally:
                c.blockSignals(False)

            self.ctrl[i].autoPanCheck.setChecked(state['autoPan'][i])
            self.ctrl[i].visibleOnlyCheck.setChecked(state['autoVisibleOnly'][i])
            xy = ['x', 'y'][i]
            self.ctrl[i].invertCheck.setChecked(state.get(xy+'Inverted', False))

        self.valid = True

    def popup(self, *args):
        if not self.valid:
            self.updateState()
        QMenu.popup(self, *args)

    def autoRange(self):
        self.view().autoRange()  ## don't let signal call this directly--it'll add an unwanted argument

    def xMouseToggled(self, b):
        self.view().setMouseEnabled(x=b)

    def xManualClicked(self):
        self.view().enableAutoRange(pg.ViewBox.XAxis, False)

    def xMinTextChanged(self):
        self.ctrl[0].manualRadio.setChecked(True)
        self.view().setXRange(float(self.ctrl[0].minText.text()), float(self.ctrl[0].maxText.text()), padding=0)

    def xMaxTextChanged(self):
        self.ctrl[0].manualRadio.setChecked(True)
        self.view().setXRange(float(self.ctrl[0].minText.text()), float(self.ctrl[0].maxText.text()), padding=0)

    def xAutoClicked(self):
        val = self.ctrl[0].autoPercentSpin.value() * 0.01
        self.view().enableAutoRange(pg.ViewBox.XAxis, val)

    def xAutoSpinChanged(self, val):
        self.ctrl[0].autoRadio.setChecked(True)
        self.view().enableAutoRange(pg.ViewBox.XAxis, val*0.01)

    def xLinkComboChanged(self, ind):
        self.view().setXLink(str(self.ctrl[0].linkCombo.currentText()))

    def xAutoPanToggled(self, b):
        self.view().setAutoPan(x=b)

    def xVisibleOnlyToggled(self, b):
        self.view().setAutoVisible(x=b)


    def yMouseToggled(self, b):
        self.view().setMouseEnabled(y=b)

    def yManualClicked(self):
        self.view().enableAutoRange(pg.ViewBox.YAxis, False)

    def yMinTextChanged(self):
        self.ctrl[1].manualRadio.setChecked(True)
        self.view().setYRange(float(self.ctrl[1].minText.text()), float(self.ctrl[1].maxText.text()), padding=0)

    def yMaxTextChanged(self):
        self.ctrl[1].manualRadio.setChecked(True)
        self.view().setYRange(float(self.ctrl[1].minText.text()), float(self.ctrl[1].maxText.text()), padding=0)

    def yAutoClicked(self):
        val = self.ctrl[1].autoPercentSpin.value() * 0.01
        self.view().enableAutoRange(pg.ViewBox.YAxis, val)

    def yAutoSpinChanged(self, val):
        self.ctrl[1].autoRadio.setChecked(True)
        self.view().enableAutoRange(pg.ViewBox.YAxis, val*0.01)

    def yLinkComboChanged(self, ind):
        self.view().setYLink(str(self.ctrl[1].linkCombo.currentText()))

    def yAutoPanToggled(self, b):
        self.view().setAutoPan(y=b)

    def yVisibleOnlyToggled(self, b):
        self.view().setAutoVisible(y=b)

    def yInvertToggled(self, b):
        self.view().invertY(b)

    def xInvertToggled(self, b):
        self.view().invertX(b)

    def exportMethod(self):
        act = self.sender()
        self.exportMethods[str(act.text())]()

    def set3ButtonMode(self):
        self.view().setLeftButtonAction('pan')

    def set1ButtonMode(self):
        self.view().setLeftButtonAction('rect')

    def setViewList(self, views):
        names = ['']
        self.viewMap.clear()

        ## generate list of views to show in the link combo
        for v in views:
            name = v.name
            if name is None:  ## unnamed views do not show up in the view list (although they are linkable)
                continue
            names.append(name)
            self.viewMap[name] = v

        for i in [0,1]:
            c = self.ctrl[i].linkCombo
            current = c.currentText()
            c.blockSignals(True)
            changed = True
            try:
                c.clear()
                for name in names:
                    c.addItem(name)
                    if name == current:
                        changed = False
                        c.setCurrentIndex(c.count()-1)
            finally:
                c.blockSignals(False)

            if changed:
                c.setCurrentIndex(0)
                c.currentIndexChanged.emit(c.currentIndex())

class CustomUITemplate(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(186, 154)
        Form.setMaximumSize(QSize(200, 16777215))
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QLabel(Form)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 7, 0, 1, 2)
        self.linkCombo = QComboBox(Form)
        self.linkCombo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.linkCombo.setObjectName("linkCombo")
        self.gridLayout.addWidget(self.linkCombo, 7, 2, 1, 2)
        self.autoPercentSpin = QSpinBox(Form)
        self.autoPercentSpin.setEnabled(True)
        self.autoPercentSpin.setMinimum(1)
        self.autoPercentSpin.setMaximum(100)
        self.autoPercentSpin.setSingleStep(1)
        self.autoPercentSpin.setProperty("value", 100)
        self.autoPercentSpin.setObjectName("autoPercentSpin")
        self.gridLayout.addWidget(self.autoPercentSpin, 2, 2, 1, 2)
        self.autoRadio = QRadioButton(Form)
        self.autoRadio.setChecked(True)
        self.autoRadio.setObjectName("autoRadio")
        self.gridLayout.addWidget(self.autoRadio, 2, 0, 1, 2)
        self.manualRadio = QRadioButton(Form)
        self.manualRadio.setObjectName("manualRadio")
        self.gridLayout.addWidget(self.manualRadio, 1, 0, 1, 2)
        self.minText = QLineEdit(Form)
        self.minText.setObjectName("minText")
        self.gridLayout.addWidget(self.minText, 1, 2, 1, 1)
        self.maxText = QLineEdit(Form)
        self.maxText.setObjectName("maxText")
        self.gridLayout.addWidget(self.maxText, 1, 3, 1, 1)
        self.invertCheck = QCheckBox(Form)
        self.invertCheck.setObjectName("invertCheck")
        self.gridLayout.addWidget(self.invertCheck, 5, 0, 1, 4)
        self.mouseCheck = QCheckBox(Form)
        self.mouseCheck.setChecked(True)
        self.mouseCheck.setObjectName("mouseCheck")
        self.gridLayout.addWidget(self.mouseCheck, 6, 0, 1, 4)
        self.visibleOnlyCheck = QCheckBox(Form)
        self.visibleOnlyCheck.setObjectName("visibleOnlyCheck")
        self.gridLayout.addWidget(self.visibleOnlyCheck, 3, 2, 1, 2)
        self.autoPanCheck = QCheckBox(Form)
        self.autoPanCheck.setObjectName("autoPanCheck")
        self.gridLayout.addWidget(self.autoPanCheck, 4, 2, 1, 2)

        self.retranslateUi(Form)
        QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label.setText(_translate("Form", "Link Axis:"))
        self.linkCombo.setToolTip(_translate("Form", "<html><head/><body><p>Links this axis with another view. When linked, both views will display the same data range.</p></body></html>"))
        self.autoPercentSpin.setToolTip(_translate("Form", "<html><head/><body><p>Percent of data to be visible when auto-scaling. It may be useful to decrease this value for data with spiky noise.</p></body></html>"))
        self.autoPercentSpin.setSuffix(_translate("Form", "%"))
        self.autoRadio.setToolTip(_translate("Form", "<html><head/><body><p>Automatically resize this axis whenever the displayed data is changed.</p></body></html>"))
        self.autoRadio.setText(_translate("Form", "Auto"))
        self.manualRadio.setToolTip(_translate("Form", "<html><head/><body><p>Set the range for this axis manually. This disables automatic scaling. </p></body></html>"))
        self.manualRadio.setText(_translate("Form", "Manual"))
        self.minText.setToolTip(_translate("Form", "<html><head/><body><p>Minimum value to display for this axis.</p></body></html>"))
        self.minText.setText(_translate("Form", "0"))
        self.maxText.setToolTip(_translate("Form", "<html><head/><body><p>Maximum value to display for this axis.</p></body></html>"))
        self.maxText.setText(_translate("Form", "0"))
        self.invertCheck.setToolTip(_translate("Form", "<html><head/><body><p>Inverts the display of this axis. (+y points downward instead of upward)</p></body></html>"))
        self.invertCheck.setText(_translate("Form", "Invert Axis"))
        self.mouseCheck.setToolTip(_translate("Form", "<html><head/><body><p>Enables mouse interaction (panning, scaling) for this axis.</p></body></html>"))
        self.mouseCheck.setText(_translate("Form", "Mouse Enabled"))
        self.visibleOnlyCheck.setToolTip(_translate("Form", "<html><head/><body><p>When checked, the axis will only auto-scale to data that is visible along the orthogonal axis.</p></body></html>"))
        self.visibleOnlyCheck.setText(_translate("Form", "Visible Data Only"))
        self.autoPanCheck.setToolTip(_translate("Form", "<html><head/><body><p>When checked, the axis will automatically pan to center on the current data, but the scale along this axis will not change.</p></body></html>"))
        self.autoPanCheck.setText(_translate("Form", "Auto Pan Only"))


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
    w.PlotItem.plot(x, y, pen=defaultpen)
    w.PlotItem.autoRange()
    w.show()

    sys.exit(app.exec_())
