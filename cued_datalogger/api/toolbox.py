from PyQt5.QtCore import QPropertyAnimation, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QTabBar, QSizePolicy, QStackedWidget,
                             QHBoxLayout)


class Toolbox(QWidget):
    """A side-oriented widget similar to a TabWidget that can be collapsed and
    expanded.

    A Toolbox is designed to be a container for sets of controls, grouped into
    'pages' and accessible by a TabBar, in the same way as a TabWidget.
    A page is normally a QWidget with a layout that contains controls.
    A widget can be added as a new tab using :meth:`addTab`.
    The Toolbox has slots for triggering its collapse and expansion, both in an
    animated mode (soft slide) and a 'quick' mode which skips the animation.
    Commonly the collapse/expand slots are connected to the tabBar's
    :meth:`tabBarDoubleClicked` signal. Normally in the DataLogger a Toolbox is
    created and then added to a :class:`~cued_datalogger.api.toolbox.MasterToolbox`,
    which connects the relevant signals for collapsing and expanding the
    Toolbox.


    Attributes
    ----------
    tabBar : QTabBar
    tabPages : QStackedWidget
        The stack of widgets that form the pages of the tabs.
    collapse_animation : QPropertyAnimation
        The animation that controls how the Toolbox collapses.
    """
    sig_collapsed_changed = pyqtSignal()

    def __init__(self, widget_side='left', parent=None):
        self.parent = parent
        self.widget_side = widget_side

        super().__init__(parent)

        self.layout = QHBoxLayout()
        self.layout.setSpacing(0)
        self.setSizePolicy(QSizePolicy.Expanding,
                           QSizePolicy.Expanding)

        # # Create the tab bar
        self.tabBar = QTabBar(self)

        self.tabBar.setTabsClosable(False)
        self.tabBar.setMovable(False)
        self.tabBar.setSizePolicy(QSizePolicy.Fixed,
                                  QSizePolicy.Expanding)
        # # Create the Stacked widget for the pages
        self.tabPages = QStackedWidget(self)

        # # Link the signals so that changing tab leads to a change of page
        self.tabBar.currentChanged.connect(self.changePage)

        # # Add them to the splitter (self)
        # Right side orientation
        if self.widget_side == 'right':
            self.tabBar.setShape(QTabBar.RoundedWest)

            self.layout.addWidget(self.tabBar)
            self.layout.addWidget(self.tabPages)

        # Left side orientation
        else:
            self.tabBar.setShape(QTabBar.RoundedEast)

            self.layout.addWidget(self.tabPages)
            self.layout.addWidget(self.tabBar)

        self.setLayout(self.layout)
        self.collapsed = False
        self.expanded_width = self.sizeHint().width()

    def addTab(self, widget, title):
        """Add a new tab, with the page widget *widget* and tab title
        *title*."""
        self.tabBar.addTab(title)
        self.tabPages.addWidget(widget)

    def removeTab(self, title):
        """Remove the tab with title *title*."""
        for tab_num in range(self.tabBar.count()):
            if self.tabBar.tabText(tab_num) == title:
                self.tabBar.removeTab(tab_num)
                self.tabPages.removeWidget(self.tabPages.widget(tab_num))

    def toggle_collapse(self):
        """If collapsed, expand the widget so the pages are visible. If not
        collapsed, collapse the widget so that only the tabBar is showing."""
        # If collapsed, expand
        if self.collapsed:
            self.expand()
        # If expanded, collapse:
        else:
            self.collapse()

    def expand(self):
        """Expand the widget so that the pages are visible."""
        self.tabPages.show()
        self.sig_collapsed_changed.emit()
        self.collapsed = False

    def collapse(self):
        """Collapse the widget so that only the tab bar is visible."""
        self.tabPages.hide()
        self.sig_collapsed_changed.emit()
        self.collapsed = True

    def changePage(self, index):
        """Set the current page to *index*."""
        self.tabBar.setCurrentIndex(index)
        self.tabPages.setCurrentIndex(index)

        if self.tabPages.currentWidget():
            self.tabPages.currentWidget().resize(self.tabPages.size())

    def clear(self):
        """Remove all tabs and pages."""
        for i in range(self.tabBar.count()):
            # Remove the tab and page at position 0
            self.tabBar.removeTab(0)
            self.tabPages.removeWidget(self.tabPages.currentWidget())


class MasterToolbox(QStackedWidget):
    """A QStackedWidget of one or more Toolboxes that toggle collapse when
    the tabBar is double clicked.

    In the MasterToolbox, only the top Toolbox is expanded, and all the others
    are collapsed. When the index is changed with :meth:`set_toolbox`, the
    top Toolbox is changed and all other Toolboxes are collapsed and hidden.
    The MasterToolbox is the normal location for all tools and controls in the
    DataLogger.

    Attributes
    ----------
    Inherited attributes :
        See ``PyQt5.QtWidgets.QStackedWidget`` for inherited attributes.
    """
    sig_collapsed_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def toggle_collapse(self):
        """Toggle collapse of the MasterToolbox by toggling the collapse of the
        Toolbox that is on top."""
        self.currentWidget().toggle_collapse()

    def set_toolbox(self, toolbox_index):
        """Set current Toolbox to the Toolbox given by *toolbox_index*, by
        quick-collapsing and hiding all of the other Toolboxes. The new
        current Toolbox will be in the same collapse/expand state as the
        former current Toolbox (ie if the previous Toolbox was collapsed,
        the new current Toolbox will be collapsed, and vice versa)."""
        # Save the old toolbox
        old_toolbox_collapsed = self.currentWidget().collapsed

        # Collapse and hide all other toolboxes
        for i in range(self.count()):
            if i == toolbox_index:
                continue
            else:
                self.widget(i).collapse()
                self.widget(i).hide()

        # Collapse / Expand the toolbox
        if old_toolbox_collapsed:
            self.widget(toolbox_index).collapse()
        else:
            self.widget(toolbox_index).expand()

        # Set the current toolbox
        self.setCurrentIndex(toolbox_index)

    def add_toolbox(self, toolbox):
        """Add a Toolbox to the MasterToolbox stack."""
        # Set the Toolbox's parent
        toolbox.parent = self
        toolbox.setParent(self)
        toolbox.sig_collapsed_changed.connect(self.sig_collapsed_changed.emit)

        # When the Toolbox's tabBar is clicked, collapse the Toolbox
        toolbox.tabBar.tabBarDoubleClicked.connect(self.toggle_collapse)

        # Add the Toolbox to the stack
        self.addWidget(toolbox)
