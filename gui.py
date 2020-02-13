import sys
sys.path.append("F:/Development/CrossMappingMaya")

import json

from PySide2 import QtCore
from PySide2 import QtWidgets

import AltMaya as altmaya
import mapper

reload(altmaya)
reload(mapper)


class AttributeSelector(altmaya.StandardMayaWindow):
    
    VALUE_ROLE = QtCore.Qt.UserRole
    TICK_COLUMN_SIZE = 50
    ROW_SIZE = 50
    
    def __init__(self, title, preselected_attr_indices=[], parent=None):
        super(AttributeSelector, self).__init__(title)
        
        selection_before = altmaya.Selection.get()
        altmaya.Selection.set([ai.obj for ai in preselected_attr_indices])
        
        self.object_list = []
        self.attribute_list = []
        
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        self.update_table()
        self.check_cells_corresponding_to_attrs(preselected_attr_indices)
        
        altmaya.Selection.set(selection_before)
        
    def get_item_text(self, item): return item.text()
    def set_item_text(self, item, text): item.setText(text)    
    def get_item_value(self, item): return item.data(self.VALUE_ROLE)
    def set_item_value(self, item, value): item.setData(self.VALUE_ROLE, value)
        
    def insert_standard_item(self, row, column, text, value):
        item = QtWidgets.QTableWidgetItem()
        self.set_item_text(item, text)
        self.set_item_value(item, value)
        self.table_wdg.setItem(row, column, item)
        
    def insert_checking_item(self, row, column, checked, value):
        item = QtWidgets.QTableWidgetItem()
        if checked: item.setCheckState(QtCore.Qt.Checked)
        else: item.setCheckState(QtCore.Qt.Unchecked)
        self.table_wdg.setItem(row, column, item)
        self.set_item_value(item, value)
        
    def check_cells_corresponding_to_attrs(self, attr_indices):
        for ai in attr_indices:
            for r in range(self.table_wdg.rowCount()):
                obj_item = self.table_wdg.item(r, 0)
                if self.get_item_text(obj_item) == ai.obj:
                    c = self.attribute_list.index(ai.attr) + 1
                    if c >= 1:
                        attr_item = self.table_wdg.item(r, c)
                        attr_item.setCheckState(QtCore.Qt.Checked)
                    continue
        
    def update_table(self):
        currently_checked = self.read_values_as_indices()
        
        while self.table_wdg.rowCount() > 0: self.table_wdg.removeRow(0)
        
        self.object_list = altmaya.Selection.get()
        self.attribute_list = []
        for o in self.object_list:
            for a in altmaya.Animation.list_keyable_attributes(o):
                if a not in self.attribute_list:
                    self.attribute_list.append(a)
                    
        self.table_wdg.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.table_wdg.setColumnCount(len(self.attribute_list) + 1)
        self.table_wdg.setHorizontalHeaderLabels(["Object"] + self.attribute_list)
        self.table_wdg.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        for i in range(1, self.table_wdg.columnCount() + 1):
            self.table_wdg.setColumnWidth(i, self.TICK_COLUMN_SIZE)
            
        for o in self.object_list:
            r = self.table_wdg.rowCount()
            self.table_wdg.insertRow(r)
            self.insert_standard_item(r, 0, o, None)
            for c, a in enumerate(self.attribute_list):
                index = altmaya.AttributeIndex(o, a)
                if index.exists():
                    self.insert_checking_item(r, c + 1, False, index)
        
        self.check_cells_corresponding_to_attrs(currently_checked)
        
        w = 100 + self.TICK_COLUMN_SIZE * len(self.attribute_list)
        h = 25 + self.ROW_SIZE * self.table_wdg.rowCount()
        self.resize(w, h)
        
    def create_widgets(self):
        self.table_wdg = QtWidgets.QTableWidget()
        self.table_wdg.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.update_button = QtWidgets.QPushButton("Update")
        self.close_button = QtWidgets.QPushButton("Close")
        
    def create_layout(self):
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(2)
        button_layout.addStretch()
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.close_button)
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.table_wdg)
        main_layout.addLayout(button_layout)
        
    def create_connections(self):
        self.update_button.clicked.connect(self.update_table)
        self.close_button.clicked.connect(self.close)
        self.table_wdg.horizontalHeader().sectionClicked.connect(self.toggle_checkboxes_in_column)
        self.table_wdg.itemClicked.connect(self.toggle_item)
        
    def toggle_item(_, item):
        if item.checkState() == QtCore.Qt.Checked:
            item.setCheckState(QtCore.Qt.Unchecked)
        else:
            item.setCheckState(QtCore.Qt.Checked)        
        
    def toggle_checkboxes_in_column(self, column):
        c = column
        if c == 0:
            return # no action for column zero (name column)
            
        states = []
        for r in range(self.table_wdg.rowCount()):
            states.append(self.table_wdg.item(r, c).checkState())
            
        nTrue = states.count(QtCore.Qt.Checked)
        nFalse = states.count(QtCore.Qt.Unchecked)
        new_state = QtCore.Qt.Checked if nTrue <= nFalse else QtCore.Qt.Unchecked
            
        for r in range(self.table_wdg.rowCount()):
            self.table_wdg.item(r, c).setCheckState(new_state)
            
    def read_values_as_indices(self):
        indices = []
        for r in range(self.table_wdg.rowCount()):
            for c in range(1, self.table_wdg.columnCount()):
                checked = self.table_wdg.item(r, c).checkState() == QtCore.Qt.Checked
                if checked:
                    item = self.table_wdg.item(r, c)
                    index = self.get_item_value(item)
                    indices.append(index)
        return indices
        
        
class MappingEditorInterface(altmaya.StandardMayaWindow):
    
    def __init__(self, mapper):
        super(MappingEditorInterface, self).__init__("Mapping Editor")
        
        self.mapper = mapper
        
        self.input_selector = AttributeSelector("Input Attributes", preselected_attr_indices=mapper.source.attribute_indices)
        self.output_selector = AttributeSelector("Output Attributes", preselected_attr_indices=mapper.target.attribute_indices)
        
        self.snapshot_table_column_names = [
            "Name",
            "Log",
            "Delete"
        ]
        
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        
        self.update_table()
        
    def create_widgets(self):
        
        self.edit_sigma = QtWidgets.QDoubleSpinBox()
        # self.edit_sigma.setRange(0.0, 1.0)
        self.edit_sigma.setSingleStep(0.01)
        self.edit_sigma.setValue(self.mapper.sigma)
        
        self.button_set_from = QtWidgets.QPushButton("Input")
        self.button_set_to = QtWidgets.QPushButton("Output")
        self.button_init_trackers = QtWidgets.QPushButton("Initialize")
        
        self.table_snapshots = QtWidgets.QTableWidget(0, len(self.snapshot_table_column_names), self)
        self.table_snapshots.setHorizontalHeaderLabels(self.snapshot_table_column_names)
        self.table_snapshots.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.button_new_snapshot = QtWidgets.QPushButton("Snapshot")
        
        self.button_solve = QtWidgets.QPushButton("Solve")
        self.button_apply = QtWidgets.QPushButton("Apply")
        
    def create_layout(self):
        
        layout_top = QtWidgets.QVBoxLayout()
        layout_buttons = QtWidgets.QHBoxLayout()
        layout_buttons.addWidget(self.button_set_from)
        layout_buttons.addWidget(self.button_set_to)
        layout_buttons.addWidget(self.button_init_trackers)
        layout_top.addLayout(layout_buttons)
        layout_sigma = QtWidgets.QHBoxLayout()
        layout_sigma.addWidget(QtWidgets.QLabel("Sigma"))
        layout_sigma.addWidget(self.edit_sigma)
        layout_top.addLayout(layout_sigma)
        
        layout_table_main = QtWidgets.QHBoxLayout()
        layout_table_main.addWidget(self.table_snapshots)
        table_layout_buttons = QtWidgets.QVBoxLayout()
        table_layout_buttons.addWidget(self.button_new_snapshot)
        layout_table_main.addLayout(table_layout_buttons)
        
        layout_bot_buttons = QtWidgets.QHBoxLayout()
        layout_bot_buttons.addWidget(self.button_solve)
        layout_bot_buttons.addWidget(self.button_apply)
        
        # Main
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(layout_top)
        main_layout.addLayout(layout_table_main)
        main_layout.addLayout(layout_bot_buttons)
        
    def create_connections(self):
        self.button_set_from.clicked.connect(self.open_from_selector)
        self.button_set_to.clicked.connect(self.open_to_selector)
        self.button_init_trackers.clicked.connect(self.init_trackers)
        self.button_new_snapshot.clicked.connect(self.new_snapshot)
        
        self.button_solve.clicked.connect(self.solve)
        self.button_apply.clicked.connect(self.apply)
        
    def open_from_selector(self):
        self.input_selector.show()
        
    def open_to_selector(self):
        self.output_selector.show()
        
    def init_trackers(self):
        if self.mapper.is_initialized():
            if not altmaya.Ask.decision(self, "Restart trackers", "Restart trackers and earse snapshot data?"):
                altmaya.Report.warning("Cancelled command to restart trackers")
                return
                
        self.mapper.init_source(self.input_selector.read_values_as_indices())
        self.mapper.init_target(self.output_selector.read_values_as_indices())
        
    def update_table(self):
        # Columns are:
        #     Name | Log | Delete
        
        names = self.mapper.names_of_snapshots()
        n = self.mapper.number_of_snapshots()
        
        self.table_snapshots.setRowCount(n)
        self.table_snapshots.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        
        def add_label(text, col_name):
            item = QtWidgets.QTableWidgetItem()
            item.setText(text)
            self.table_snapshots.setItem(ix, self.snapshot_table_column_names.index(col_name), item)

        def add_button(text, callback, col_name):
            button = QtWidgets.QPushButton(text)
            button.clicked.connect(callback)
            self.table_snapshots.setCellWidget(ix, self.snapshot_table_column_names.index(col_name), button)
        
        for (ix, name) in enumerate(names):

            # Name
            add_label(name, "Name")
            
            # Log
            def callback(ix, name):
                snapshot = self.mapper.snapshots[name]
                def fn():
                    message = "Snapshot %s:" % name
                    message += "\n\tSource: %s" % str(snapshot["source"])
                    message += "\n\tTarget: %s" % str(snapshot["target"])
                    altmaya.Report.message(message)
                return fn
            add_button("Log", callback(ix, name), "Log")
            
            # Delete
            def callback(ix, name):
                def fn():
                    altmaya.Report.message("Deleting snapshot %s" % name)
                    self.mapper.delete_pose(name)
                    self.update_table()
                return fn
            add_button("Delete", callback(ix, name), "Delete")
    
    def new_snapshot(self):
        if self.mapper.source is None:
            altmaya.Report.error("Source pose is not setup yet")
            return
        if self.mapper.source is None:
            altmaya.Report.error("Target pose is not setup yet")
            return
        n = self.mapper.number_of_snapshots()
        name = "Snapshot %d" % (n + 1)
        name = altmaya.Ask.string(self, "New Snapshot", "Enter name for snapshot", name)
        if name == "":
            altmaya.Report.warning("Cancelled new snapshot command (user cancelled)")
            return
        self.mapper.new_snapshot(name)
        self.update_table()
        
    def solve(self):
        try:
            self.mapper.sigma = self.edit_sigma.value()
            self.mapper.solve()
            altmaya.Report.message("Solved mapper")
        except ValueError as e:
            altmaya.Report.error(str(e))
    
    def apply(self):
        try:
            self.mapper.apply_current()
            altmaya.Report.message("Applied mapper")
        except ValueError as e:
            altmaya.Report.error(str(e))
        

class MappingCollectionInterface(altmaya.StandardMayaWindow):
    
    def __init__(self):
        super(MappingCollectionInterface, self).__init__("Mapping Collection")

        self.mapper_table_column_names = [
            "Name",
            "Sigma",
            "Edit",
            "Solve",
            "Apply",
            "Delete"
        ]

        self.mappers = {}

        self.setGeometry(0, 0, 800, 400)
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
        self.button_export_mapping_data.clicked.connect(self.export_to_json)
        self.button_import_mapping_data.clicked.connect(self.import_from_json)
        
        self.button_new_mapping.clicked.connect(self.add_new_mapping)
        
    def export_to_json(self):
        filepath = altmaya.Ask.choose_file_to_save_json(self, "Export Mappers to JSON")
        if filepath == "":
            altmaya.Report.warning("Cancelled command to export mappers")
            return 
            
        data = []
        for key in self.mappers.keys():
            mapper = self.mappers[key]
            source = mapper.source
            target = mapper.target
            data.append({
                "name": key,
                "sigma": mapper.sigma,
                "source_indices": [str(ind) for ind in source.attribute_indices],
                "target_indices": [str(ind) for ind in target.attribute_indices],
                "snapshots": mapper.snapshots
            })
            
        with open(filepath, "w") as f:
            f.write(json.dumps(data, indent=4, separators=(',', ': ')))
            
        altmaya.Report.message("Exported mappers to %s" % filepath)

        
    def import_from_json(self):
        filepath = altmaya.Ask.choose_file_to_open_json(self, "Import Mappers from JSON")
        if filepath == "":
            altmaya.Report.warning("Cancelled command to import mappers")
            return 
            
        with open(filepath, "r") as f:
            data = json.loads(f.read())
            
        for datum in data:
            m = mapper.CrossMapping()
            m.init_source([altmaya.AttributeIndex.from_key(key) for key in datum["source_indices"]])
            m.init_target([altmaya.AttributeIndex.from_key(key) for key in datum["target_indices"]])
            m.sigma = datum["sigma"]
            m.snapshots = datum["snapshots"]
            self.mappers[datum["name"]] = m
            
        altmaya.Report.message("Imported mappers from %s" % filepath)
        self.update_table()

    def update_table(self):
        # Columns are:
        #     Name | Sigma | Edit | Solve | Apply | Delete

        mappers = self.mappers
        keys = list(mappers.keys())

        self.table_mappers.setRowCount(len(keys))
        self.table_mappers.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        
        def add_label(text, col_name):
            item = QtWidgets.QTableWidgetItem()
            item.setText(text)
            self.table_mappers.setItem(ix, self.mapper_table_column_names.index(col_name), item)
            
        def add_editable_number(init, col_name):
            item = QtWidgets.QDoubleSpinBox()
            # item.setRange(0.0, 1.0)
            item.setSingleStep(0.01)
            item.setValue(init)
            self.table_mappers.setCellWidget(ix, self.mapper_table_column_names.index(col_name), item)

        def add_button(text, callback, col_name):
            button = QtWidgets.QPushButton(text)
            button.clicked.connect(callback)
            self.table_mappers.setCellWidget(ix, self.mapper_table_column_names.index(col_name), button)
            
        def read_sigma(ix):
            slider = self.table_mappers.cellWidget(ix, self.mapper_table_column_names.index("Sigma"))
            return slider.value()
        
        for (ix, key) in enumerate(keys):
            mapper = self.mappers[key]

            # Name
            add_label(key, "Name")

            # Edit
            def callback(ix, key):
                def fn():
                    altmaya.Report.message("Editing %s" % key)
                    MappingEditorInterface(self.mappers[key]).show()
                return fn
            add_button("Edit", callback(ix, key), "Edit")
                        
            # Solve
            def callback(ix, key):
                def fn():
                    altmaya.Report.message("Solving %s" % key)
                    self.mappers[key].sigma = read_sigma(ix)
                    self.mappers[key].solve()
                return fn
            add_button("Solve", callback(ix, key), "Solve")
            
            # Sigma
            add_editable_number(mapper.sigma, "Sigma")

            # Apply
            def callback(ix, key):
                def fn():
                    altmaya.Report.message("Applying %s" % key)
                    self.mappers[key].apply_current()
                return fn
            add_button("Apply", callback(ix, key), "Apply")

            # Delete
            def callback(ix, key):
                def fn():
                    altmaya.Report.message("Deleting %s" % key)
                    del self.mappers[key]
                    self.update_table()
                return fn
            add_button("Delete", callback(ix, key), "Delete")
            
    def add_new_mapping(self):
        n = len(self.mappers.keys())
        name = str("Mapper %d" % (n + 1))
        name = altmaya.Ask.string(self, "New Mapping", "Enter name for mapping:", name)
        if name != "":
            self.mappers[name] = mapper.CrossMapping()
            self.update_table()
        else:
            altmaya.Report.warning("Cancelled command to make a new mapping (user cancelled)")
        

if __name__ == "__main__":
        
    try:
        test_dialog.close() # pylint: disable=E0601
        test_dialog.deleteLater()
    except:
        pass

    test_dialog = MappingCollectionInterface()
    test_dialog.show()
