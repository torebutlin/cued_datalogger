# -*- coding: utf-8 -*-
"""
Created on Wed Aug  9 11:00:36 2017

@author: eyt21
"""
import weakref
import sys
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import( QWidget,QMenu,QAction,QActionGroup,QWidgetAction,QGridLayout,
                            QCheckBox,QRadioButton,QLineEdit,QSpinBox,QComboBox,
                            QLabel, QApplication)
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import QMetaObject,QSize,QCoreApplication


class CustomPlotWidget(pg.PlotWidget):
    def __init__(self,*arg, **kwarg):
        super().__init__(*arg, viewBox = CustomViewBox(cparent = self),**kwarg)
        
        self.plotitem = self.getPlotItem()
        self.viewbox = self.plotitem.getViewBox()
        
        # Removing some plot options
        ext_menu = self.plotItem.ctrlMenu
        ext_submenus = self.plotItem.subMenus
        ext_menu.removeAction(ext_submenus[1].menuAction())
        ext_menu.removeAction(ext_submenus[2].menuAction())
        ext_menu.removeAction(ext_submenus[3].menuAction())
        ext_menu.removeAction(ext_submenus[5].menuAction())

    def getViewedDataRegion(self, data_for_slice, axis='bottom'):
        """Return the indices of data_for_slice that are currently in the
        visible plot window"""

        # Get the axis limits
        axis_lower, axis_upper = self.plotItem.getAxis(axis).range

        # The data that is in view is where the data is within the axis limits
        data_in_display = (data_for_slice >= axis_lower) & (data_for_slice <= axis_upper)

        indices_of_data_in_display = np.where(data_in_display)[0]
        return indices_of_data_in_display[0], indices_of_data_in_display[-1]

class CustomViewBox(pg.ViewBox):
    def __init__(self, *arg,cparent = None,**kwarg):
        super().__init__(*arg,**kwarg)
        self.cparent = cparent
        self.menu = CustomViewMenu(self)

    def raiseContextMenu(self, ev):
        menu = self.getMenu(ev)
        menu.addMenu(self.cparent.getPlotItem().ctrlMenu)
        menu.popup(ev.screenPos().toPoint())

    def autoRange(self, padding= None, items=None):
        super().autoRange(padding=padding, items= None)
        r = self.viewRect()
        self.setLimits(xMin = r.left(), xMax = r.right())

class CustomViewMenu(QMenu):
    def __init__(self, view):
        QMenu.__init__(self)

        self.view = weakref.ref(view)  ## keep weakref to view to avoid circular reference (don't know why, but this prevents the ViewBox from being collected)
        self.valid = False  ## tells us whether the ui needs to be updated
        self.viewMap = weakref.WeakValueDictionary()  ## weakrefs to all views listed in the link combos

        self.setTitle("ViewBox options")
        self.viewAll = QAction("View All", self)
        self.viewAll.triggered.connect(self.autoRange)
        self.addAction(self.viewAll)

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
        ## Something about the viewbox has changed; update the menu GUI
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


if __name__ == '__main__':

    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    pg.setConfigOption('antialias', True)
    defaultpen = pg.mkPen('k')

    app = 0
    app = QApplication(sys.argv)
    w = CustomPlotWidget()
    x = np.linspace(0, 20*np.pi, 1e4)
    y = np.sin(x)
    w.plotItem.plot(x, y, pen=defaultpen)
    w.plotItem.autoRange()
    w.show()

    def print_region(*args, **kwargs):
        x_lower, x_upper = w.getViewedDataRegion(x)
        print("Index {}: {}, Index {}: {}".format(x_lower, x[x_lower], x_upper, x[x_upper]))

    w.sigRangeChanged.connect(print_region)

    sys.exit(app.exec_())
