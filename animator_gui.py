import os
import json

import pandas
import numpy

from PySide2 import QtCore
from PySide2 import QtWidgets

import AltMaya as altmaya
reload(altmaya)


class AnimatorInterface(altmaya.StandardMayaWindow):
    
    def __init__(self):
        super(AnimatorInterface, self).__init__("Animator Interface")  
        
        self.data = None
        self.attrs = []
        
        self.column_names = [
            "Maya Key",
            "Data Key",
            "Shift",
            "Scale",
            "Apply"
        ]
        self.column_widths = [
            100,
            150,
            100,
            100,
            100
        ]
        
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        
        self.setFixedWidth(800)
        self.report_message("Ready and Waiting")
        
    def create_widgets(self):
        self.status_bar = QtWidgets.QLabel("Status")
        
        self.table_properties = QtWidgets.QTableWidget(0, len(self.column_names), self)
        self.table_properties.setHorizontalHeaderLabels(self.column_names)
        for (ix, w) in enumerate(self.column_widths):
            self.table_properties.setColumnWidth(ix, w)
        self.table_properties.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        
        self.button_open = QtWidgets.QPushButton("Open")
        self.button_set_selected = QtWidgets.QPushButton("Set Selected")
        self.button_close = QtWidgets.QPushButton("Close")
        
    def create_layout(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.status_bar)
        main_layout.addWidget(self.table_properties)
        footer_layout = QtWidgets.QHBoxLayout(self)
        footer_layout.addWidget(self.button_open)
        footer_layout.addWidget(self.button_set_selected)
        footer_layout.addWidget(self.button_close)
        main_layout.addLayout(footer_layout)
        
    def create_connections(self):
        self.button_open.clicked.connect(self.open_data_prompt)
        self.button_set_selected.clicked.connect(self.set_selected)
        self.button_close.clicked.connect(self.close)
        
    def set_status(self, message, color_as_hex):
        font_hex = "%02x%02x%02x" % (55, 55, 55)
        self.status_bar.setText("> " + message)
        self.status_bar.setStyleSheet("background: #%s; color: #%s" % (color_as_hex, font_hex))
        
    def report_error(self, message):
        self.set_status(message, "F20505")
        altmaya.Report.error("Mapping Editor: " + message)
        
    def report_warning(self, message):
        self.set_status(message, "F2BE22")
        altmaya.Report.warning("Mapping Editor: " + message)
        
    def report_message(self, message):
        self.set_status(message, "446644")
        altmaya.Report.message("Mapping Editor: " + message)
        
    def update_table(self):
        n = len(self.attrs)
        self.setFixedHeight(n * 30 + 150)
         
        self.table_properties.setRowCount(n)
        self.table_properties.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        
        def add_label(text, ix, col_name):
            item = QtWidgets.QTableWidgetItem()
            item.setText(text)
            c = self.column_names.index(col_name)
            self.table_properties.setItem(ix, c, item)
            
        def add_editable_number(init, ix, col_name, minv=-1, maxv=-1, inc=0.01):
            item = QtWidgets.QDoubleSpinBox()
            if minv != -1 and maxv != -1:
                item.setRange(minv, maxv)
            item.setSingleStep(inc)
            item.setValue(init)
            c = self.column_names.index(col_name)
            self.table_properties.setCellWidget(ix, c, item)
            
        def add_combo_box(options, ix, col_name):
            item = QtWidgets.QComboBox()
            item.addItems(options)
            c = self.column_names.index(col_name)
            self.table_properties.setCellWidget(ix, c, item)

        def add_button(text, callback, ix, col_name):
            item = QtWidgets.QPushButton(text)
            item.clicked.connect(callback)
            c = self.column_names.index(col_name)
            self.table_properties.setCellWidget(ix, c, item)
            
        # Columns are:
        #     Maya Key | Data Key | Shift | Scale | Apply
            
        for (ix, ai) in enumerate(self.attrs):

            # Maya Key
            add_label(ai.key, ix, "Maya Key")
            
            # Data Key
            add_combo_box(self.data.columns, ix, "Data Key")
            
            # Shift
            add_editable_number(0.0, ix, "Shift", minv=-100, maxv=100)
            
            # Scale
            add_editable_number(1.0, ix, "Scale", minv=-100, maxv=100)
            
            # Apply
            def callback(ix):
                def fn():
                    attr = self.attrs[ix]
                    key = self.table_properties.cellWidget(ix, self.column_names.index("Data Key")).currentText()
                    shift = self.table_properties.cellWidget(ix, self.column_names.index("Shift")).value()
                    scale = self.table_properties.cellWidget(ix, self.column_names.index("Scale")).value()
                    
                    values = self.data[key]
                    adjusted = values * scale + shift
                    s = altmaya.Timeline.get_start()
                    times = [s + i for (i, _) in enumerate(values)]
                    altmaya.Animation.add_keyframes(attr, times, adjusted)
                    
                    self.report_message("Animating %s from %s (shift=%2.2f, scale=%2.2f)" % (
                        attr, key, shift, scale
                    ))
                    
                return fn
            add_button("Apply", callback(ix), ix, "Apply")
        
    def open_data(self, filepath):
        with open(filepath, "r") as f:
            self.data = pandas.read_csv(filepath, skipinitialspace=True)
            self.report_message("Opened %s successfully" % os.path.basename(filepath))
            
    def open_data_prompt(self):
        filepath = altmaya.Ask.choose_file_to_open_csv(self, "Open Animation Data")
        if filepath != "":
            self.open_data(filepath)
        else:
            self.report_warning("Cancelled open data command")
            
    def set_selected(self):
        self.attrs = altmaya.AttributeIndex.enumerate_selected()
        self.update_table()
        
    def closeEvent(self, event):
        self.report_message("Enjoy your animation!")
        event.accept()
        

try:
    animator_interface.close() # pylint: disable=E0601
    animator_interface.deleteLater()
except:
    pass

animator_interface = AnimatorInterface()
# animator_interface.open_data("F:/Maya Projects/Piku Piku/data/ROM-Richard-Tracked.csv")
# animator_interface.open_data("F:/Maya Projects/Piku Piku/data/Richard_ROM_2.csv")
# animator_interface.set_selected()
animator_interface.show()

