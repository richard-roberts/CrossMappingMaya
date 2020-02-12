from PySide2 import QtCore
from PySide2 import QtWidgets

import AltMaya as altmaya
import mapper

class CrossMappingInterface(altmaya.StandardMayaWindow):
    
    def __init__(self):
        super(CrossMappingInterface, self).__init__("Cross Mapping")

        self.mapper_table_column_names = [
            "Name",
            "Input",
            "Output",
            "Sigma",
            "Edit",
            "Apply",
            "Solve",
            "Delete"
        ]

        self.mappers = {
           "X to XY": mapper.CrossMapping(["x"], ["x", "y"], 1.0)
        }

        self.setGeometry(0, 0, 1200, 400)
        self.create_widgets()
        self.create_layout()
        self.create_connections()

        self.update_table()

    def create_widgets(self):
        
        # Top buttons
        self.button_export_mapping_data = QtWidgets.QPushButton("Export")
        self.button_import_mapping_data = QtWidgets.QPushButton("Import")

        # Table and buttons
        self.table_mappers = QtWidgets.QTableWidget(0, len(self.mapper_table_column_names), self)
        self.table_mappers.setHorizontalHeaderLabels(self.mapper_table_column_names)
        # self.table_mappers.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table_mappers.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.button_new_mapping = QtWidgets.QPushButton("New")

        # Bottom buttons
        self.button_solve_mappings = QtWidgets.QPushButton("Solve")
        self.button_apply_mappings = QtWidgets.QPushButton("Apply")
        self.button_bake_mappings = QtWidgets.QPushButton("Bake")

    def create_layout(self):
        
        # Top buttons
        layout_top_buttons = QtWidgets.QHBoxLayout()
        layout_top_buttons.addWidget(self.button_export_mapping_data)
        layout_top_buttons.addWidget(self.button_import_mapping_data)

        # Table and buttons
        layout_table_main = QtWidgets.QHBoxLayout()
        layout_table_main.addWidget(self.table_mappers)
        table_layout_buttons = QtWidgets.QVBoxLayout()
        table_layout_buttons.addWidget(self.button_new_mapping)
        layout_table_main.addLayout(table_layout_buttons)
        
        # Bottom buttons
        layout_bot_buttons = QtWidgets.QHBoxLayout()
        layout_bot_buttons.addWidget(self.button_solve_mappings)
        layout_bot_buttons.addWidget(self.button_apply_mappings)
        layout_bot_buttons.addWidget(self.button_bake_mappings)

        # Main
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(layout_top_buttons)
        main_layout.addLayout(layout_table_main)
        main_layout.addLayout(layout_bot_buttons)
        
    def create_connections(self):
        # self.set_attributes_button.clicked.connect(self.set_attributes)
        pass

    def update_table(self):
        # Columns are:
        #     Name | In | Out | Sigma | Edit | Apply | Solve | Delete

        mappers = self.mappers
        keys = list(mappers.keys())

        self.table_mappers.setRowCount(len(keys))
        # self.table_mappers.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        
        for (ix, key) in enumerate(keys):
            mapper = self.mappers[key]

            def add_editable_text(text, col_name):
                item = QtWidgets.QTableWidgetItem()
                item.setText(text)
                self.table_mappers.setItem(ix, self.mapper_table_column_names.index(col_name), item)
                
            def add_editable_number(init, col_name):
                item = QtWidgets.QDoubleSpinBox()
                item.setRange(0.0, 1.0)
                item.setSingleStep(0.01)
                item.setValue(init)
                self.table_mappers.setCellWidget(ix, self.mapper_table_column_names.index(col_name), item)

            def add_button(text, callback, col_name):
                button = QtWidgets.QPushButton(text)
                button.clicked.connect(callback)
                self.table_mappers.setCellWidget(ix, self.mapper_table_column_names.index(col_name), button)

            # Name
            add_editable_text(key, "Name")

            # Input
            def callback():
                print("Running", "Input")
            add_button("Input", callback, "Input")

            # Output
            def callback():
                print("Running", "Output")
            add_button("Output", callback, "Output")

            # Sigma
            add_editable_number(1.0, "Sigma")

            # Edit
            def callback():
                print("Running", "Edit")
            add_button("Edit", callback, "Edit")

            # Apply
            def callback():
                print("Running", "Apply")
            add_button("Apply", callback, "Apply")

            # Solve
            def callback():
                print("Running", "Solve")
            add_button("Solve", callback, "Solve")

            # Delete
            def callback():
                print("Running", "Delete")
            add_button("Delete", callback, "Delete")

if __name__ == "__main__":
        
    try:
        test_dialog.close() # pylint: disable=E0601
        test_dialog.deleteLater()
    except:
        pass

    test_dialog = CrossMappingInterface()
    test_dialog.show()
