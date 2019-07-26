import os, json
import platform
from pydm import Display, PyDMApplication
from pydm.utilities import IconFont
from pydm.widgets import PyDMRelatedDisplayButton, PyDMEmbeddedDisplay, PyDMLabel, PyDMByteIndicator
from pydm.PyQt import QtCore

from PyQt5.QtWidgets import (QLabel, QTableWidgetItem, QWidget, QHBoxLayout, QStyleFactory,
    QTabWidget, QVBoxLayout, QGroupBox, QLineEdit, QPushButton, QScrollArea, QFrame, QApplication)
from PyQt5.QtGui import QColor, QPalette, QFont, QBrush



class AllPSDisplay(Display):
    def __init__(self, parent=None, args=[], macros=None):
        super(AllPSDisplay, self).__init__(parent=parent, args=args, macros=None)
        # Placeholder for data to filter
        self.BBB_PS_list = []
        # Reference to the PyDMApplication
        self.app = QApplication.instance()
        self.app.setApplicationDisplayName('Beaglebone Black - RS485 Serial Interface Controller')
        # Assemble the Widgets
        self.setup_ui()
        # Load data from file
        self.load_data()
        # Show all BBBs
        #self.do_search()

    def minimumSizeHint(self):
        # This is the default recommended size
        # for this screen
        return QtCore.QSize(1000, 600)

    def ui_filepath(self):
        # No UI file is being used
        return None

    def setup_ui(self):
        # Create the main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Create a Label to be the title
        lbl_title = QLabel("Beaglebone Black - RS485 Serial Interface Controller\nControls Group")
        # Add some StyleSheet to it
        lbl_title.setStyleSheet("\
            QLabel {\
                qproperty-alignment: AlignCenter;\
                border: 1px solid #FF17365D;\
                border-top-left-radius: 15px;\
                border-top-right-radius: 15px;\
                background-color: #FF17365D;\
                padding: 5px 0px;\
                color: rgb(255, 255, 255);\
                max-height: 40px;\
                font-size: 14px;\
            }")

        # Add the title label to the main layout
        main_layout.addWidget(lbl_title)

        # Create a GroupBox for subtitles
        legend_layout = QHBoxLayout()
        legend_layout.setGeometry(QtCore.QRect(10, 10, 50, 30))
        gb_legend = QGroupBox(parent=self)
        gb_legend.setLayout(legend_layout)

        # Create a squares and labels
        brush_black = QBrush(QColor(255, 255, 255))
        brush_black.setStyle(QtCore.Qt.SolidPattern)
        brush_orange = QBrush(QColor(193, 125, 17))
        brush_orange.setStyle(QtCore.Qt.SolidPattern)
        brush_blue = QBrush(QColor(52, 101, 164))
        brush_blue.setStyle(QtCore.Qt.SolidPattern)

        palette = QPalette()
        palette.setBrush(QPalette.Active, QPalette.Base, brush_black)
        palette.setBrush(QPalette.Inactive, QPalette.Base, brush_black)

        font = QFont()
        font.setItalic(True)

        self.color_IOC = QLineEdit()
        self.color_IOC.setEnabled(False)
        self.color_IOC.setMaximumSize(QtCore.QSize(15, 15))
        palette.setBrush(QPalette.Disabled, QPalette.Base, brush_blue)
        self.color_IOC.setPalette(palette)

        self.text_IOC = QLabel()
        self.text_IOC.setText("IOC")
        self.text_IOC.setFont(font)

        self.color_PES = QLineEdit()
        self.color_PES.setEnabled(False)
        self.color_PES.setMaximumSize(QtCore.QSize(15, 15))
        palette.setBrush(QPalette.Disabled, QPalette.Base, brush_orange)
        self.color_PES.setPalette(palette)

        self.text_PES = QLabel()
        self.text_PES.setText("PES")
        self.text_PES.setFont(font)

        # Add the created widgets to the layout
        legend_layout.addWidget(self.color_IOC)
        legend_layout.addWidget(self.text_IOC)
        legend_layout.addWidget(self.color_PES)
        legend_layout.addWidget(self.text_PES)

        # Add the Groupbox to the main layout
        main_layout.addWidget(gb_legend)


        # Create the Search Panel layout
        search_layout = QHBoxLayout()

        # Create a GroupBox with "Filtering" as Title
        gb_search = QGroupBox(parent=self)
        gb_search.setLayout(search_layout)

        # Create a label, line edit and button for filtering
        lbl_search = QLabel(text="Filter: ")
        self.txt_filter = QLineEdit()
        self.txt_filter.returnPressed.connect(self.do_search)
        btn_search = QPushButton()
        btn_search.setText("Search")
        btn_search.clicked.connect(self.do_search)

        # Add the created widgets to the layout
        search_layout.addWidget(lbl_search)
        search_layout.addWidget(self.txt_filter)
        search_layout.addWidget(btn_search)

        # Add the Groupbox to the main layout
        main_layout.addWidget(gb_search)

        # Create the Results Layout
        self.resultsLT_layout = QVBoxLayout()
        self.resultsLT_layout.setContentsMargins(0, 0, 0, 0)
        self.resultsBO_layout = QVBoxLayout()
        self.resultsBO_layout.setContentsMargins(0, 0, 0, 0)
        self.resultsSR_layout = QVBoxLayout()
        self.resultsSR_layout.setContentsMargins(0, 0, 0, 0)
        self.resultsDCL_layout = QVBoxLayout()
        self.resultsDCL_layout.setContentsMargins(0, 0, 0, 0)
        # Create a Frame to host the results of search
        self.frmLT_result = QFrame(parent=self)
        self.frmLT_result.setLayout(self.resultsLT_layout)
        self.frmBO_result = QFrame(parent=self)
        self.frmBO_result.setLayout(self.resultsBO_layout)
        self.frmSR_result = QFrame(parent=self)
        self.frmSR_result.setLayout(self.resultsSR_layout)
        self.frmDCL_result = QFrame(parent=self)
        self.frmDCL_result.setLayout(self.resultsDCL_layout)

        # Create a ScrollArea so we can properly handle many entries
        scroll_areaLT = QScrollArea(parent=self)
        scroll_areaBO = QScrollArea(parent=self)
        scroll_areaSR = QScrollArea(parent=self)
        scroll_areaDCL = QScrollArea(parent=self)
        scroll_areaLT.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll_areaBO.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll_areaSR.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll_areaDCL.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll_areaLT.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_areaBO.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_areaSR.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_areaDCL.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_areaLT.setWidgetResizable(True)
        scroll_areaBO.setWidgetResizable(True)
        scroll_areaSR.setWidgetResizable(True)
        scroll_areaDCL.setWidgetResizable(True)

        # Add the Frame to the scroll area
        scroll_areaLT.setWidget(self.frmLT_result)
        scroll_areaBO.setWidget(self.frmBO_result)
        scroll_areaSR.setWidget(self.frmSR_result)
        scroll_areaDCL.setWidget(self.frmDCL_result)



        # Create tabs
        self.tabWidget = QTabWidget(parent=self)
        self.tabLT = QWidget(self.tabWidget)
        self.tabWidget.addTab(self.tabLT, "LTs")
        self.LTLayout = QHBoxLayout(self.tabLT)
        self.LTLayout.setContentsMargins(0, 0, 0, 0)
        self.tabsBooster = QWidget(self.tabWidget)
        self.tabWidget.addTab(self.tabsBooster, "Booster")
        self.BOLayout = QHBoxLayout(self.tabsBooster)
        self.BOLayout.setContentsMargins(0, 0, 0, 0)
        self.tabsAnel = QWidget(self.tabWidget)
        self.tabWidget.addTab(self.tabsAnel, "Anel")
        self.SRLayout = QHBoxLayout(self.tabsAnel)
        self.SRLayout.setContentsMargins(0, 0, 0, 0)
        self.tabsDCLink = QWidget(self.tabWidget)
        self.tabWidget.addTab(self.tabsDCLink, "DC-Link")
        self.DCLLayout = QHBoxLayout(self.tabsDCLink)
        self.DCLLayout.setContentsMargins(0, 0, 0, 0)

        # Add the scroll area to the main layout
        main_layout.addWidget(self.tabWidget)

        # Add the scroll area to the main layout
        self.LTLayout.addWidget(scroll_areaLT)
        self.BOLayout.addWidget(scroll_areaBO)
        self.SRLayout.addWidget(scroll_areaSR)
        self.DCLLayout.addWidget(scroll_areaDCL)

    def load_data(self):
        # Extract the directory of this file...
        base_dir = os.path.dirname(os.path.realpath(__file__))
        # Concatenate the directory with the file name...
        data_file = os.path.join(base_dir, "ps-list.txt")
        # Open the file so we can read the data...
        self.BBB_PS_list = {}
        with open(data_file, 'r') as f:
            # For each line in the file...
            for current_line in f:
                self.BBB_PS_list[current_line.split()[0]] = current_line.split()[1:]

    def do_search(self):
        # For each widget inside the results frame, lets destroy them
        for widget in self.frmLT_result.findChildren(QWidget):
            widget.setParent(None)
            widget.deleteLater()
        for widget in self.frmBO_result.findChildren(QWidget):
            widget.setParent(None)
            widget.deleteLater()
        for widget in self.frmSR_result.findChildren(QWidget):
            widget.setParent(None)
            widget.deleteLater()
        for widget in self.frmDCL_result.findChildren(QWidget):
            widget.setParent(None)
            widget.deleteLater()

        # Grab the filter text
        filter_text = self.txt_filter.text()

        # For every entry in the dataset...
        for entry in self.BBB_PS_list:
            # Check if they match our filter
            if filter_text.upper() not in entry.upper():
                continue

            # Create macros list
            dict_macro_BBB = {"PS_CON" : entry, "PYTHON": "python" if platform.system() == "Windows" else "python3"}
            for i in range(1, len(self.BBB_PS_list[entry])+1):
                dict_macro_BBB["PS{}".format(i)] = self.BBB_PS_list[entry][i-1]
            # Create a PyDMEmbeddedDisplay for this entry
            disp = PyDMEmbeddedDisplay(parent=self)
            PyDMApplication.instance().close_widget_connections(disp)
            disp.macros = json.dumps(dict_macro_BBB)
            disp.filename = 'PS_Controller.ui'
            disp.setMinimumWidth(700)
            disp.setMinimumHeight(40)
            disp.setMaximumHeight(100)

            # Add the Embedded Display to the Results Layout
            if "DCL" in entry:
                self.resultsDCL_layout.addWidget(disp)
            elif "SI" in entry:
                self.resultsSR_layout.addWidget(disp)
            elif "BO" in entry:
                self.resultsBO_layout.addWidget(disp)
            elif ("TB" in entry) or ("TS" in entry):
                self.resultsLT_layout.addWidget(disp)

            PyDMApplication.instance().establish_widget_connections(disp)
