import json

import numpy

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
        super(AttributeSelector, self).__init__(title, parent=parent)
        
        selection_before = altmaya.Selection.get()
        altmaya.Selection.set([ai.obj for ai in preselected_attr_indices])
        
        self.object_list = []
        self.attribute_list = []
        
        self.banned = []
        
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
        return item
        
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
            for ix, a in enumerate(self.attribute_list):
                c = ix + 1
                index = altmaya.AttributeIndex(o, a)
                item = self.insert_checking_item(r, c, False, index)
                if not index.exists():
                    item.setFlags(QtCore.Qt.NoItemFlags)
                    self.banned.append((r, c))
        
        self.check_cells_corresponding_to_attrs(currently_checked)
        
        w = 100 + self.TICK_COLUMN_SIZE * len(self.attribute_list)
        h = 25 + self.ROW_SIZE * self.table_wdg.rowCount()
        self.resize(w, h)
        
    def create_widgets(self):
        self.table_wdg = QtWidgets.QTableWidget()
        self.table_wdg.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.select_button = QtWidgets.QPushButton("Select")
        self.update_button = QtWidgets.QPushButton("Update")
        self.close_button = QtWidgets.QPushButton("Close")
        
    def create_layout(self):
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(2)
        button_layout.addStretch()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.close_button)
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.table_wdg)
        main_layout.addLayout(button_layout)
        
    def create_connections(self):
        self.select_button.clicked.connect(self.select_attrs)
        self.update_button.clicked.connect(self.update_table)
        self.close_button.clicked.connect(self.close)
        self.table_wdg.horizontalHeader().sectionClicked.connect(self.toggle_checkboxes_in_column)
        self.table_wdg.itemClicked.connect(self.toggle_item)
        
    def select_attrs(self):
        altmaya.Selection.set(self.object_list)
        
    def toggle_item(_, item):
        if item.row() == 0:
            return # avoid the 0 column which has names
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
            if (r, c) not in self.banned:
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
    
    def __init__(self, parent, mapper, name):
        super(MappingEditorInterface, self).__init__("Mapping Editor - %s" % name, parent=parent)
        
        self.mapper = mapper

        if self.mapper.is_initialized():
            self.input_selector = AttributeSelector("Input Attributes", preselected_attr_indices=mapper.source.attribute_indices)
            self.output_selector = AttributeSelector("Output Attributes", preselected_attr_indices=mapper.target.attribute_indices)
        else:
            self.input_selector = AttributeSelector("Input Attributes")
            self.output_selector = AttributeSelector("Output Attributes")
            
        self.snapshot_table_column_names = [
            "Name",
            "Log",
            "Dist S",
            "Dist T",
            "GoTo Frame",
            "GoTo Target",
            "Delete"
        ]
        
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        
        self.update_table()
        self.report_message("Ready and Waiting")
        
    def create_widgets(self):
        
        self.status_bar = QtWidgets.QLabel("Status")
        
        self.edit_sigma = QtWidgets.QDoubleSpinBox()
        self.edit_sigma.setSingleStep(0.01)
        self.edit_sigma.setValue(self.mapper.sigma)
        
        self.button_set_from = QtWidgets.QPushButton("Input")
        self.button_set_to = QtWidgets.QPushButton("Output")
        self.button_init_trackers = QtWidgets.QPushButton("Initialize")
        
        self.table_snapshots = QtWidgets.QTableWidget(0, len(self.snapshot_table_column_names), self)
        self.table_snapshots.setHorizontalHeaderLabels(self.snapshot_table_column_names)
        self.table_snapshots.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.button_new_snapshot = QtWidgets.QPushButton("Snapshot")
        self.button_dists = QtWidgets.QPushButton("Get Dists")
        
        self.button_select_attrs = QtWidgets.QPushButton("Select")
        self.button_zero = QtWidgets.QPushButton("Zero")
        self.button_solve = QtWidgets.QPushButton("Solve")
        self.button_apply = QtWidgets.QPushButton("Apply")
        self.button_bake = QtWidgets.QPushButton("Bake")
        self.button_clear_animation = QtWidgets.QPushButton("Clear Anim")
        
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
        table_layout_buttons.addWidget(self.button_dists)
        layout_table_main.addLayout(table_layout_buttons)
        
        layout_bot_buttons = QtWidgets.QHBoxLayout()
        layout_bot_buttons.addWidget(self.button_select_attrs)
        layout_bot_buttons.addWidget(self.button_zero)
        layout_bot_buttons.addWidget(self.button_solve)
        layout_bot_buttons.addWidget(self.button_apply)
        layout_bot_buttons.addWidget(self.button_bake)
        layout_bot_buttons.addWidget(self.button_clear_animation)
        
        # Main
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.status_bar)
        main_layout.addLayout(layout_top)
        main_layout.addLayout(layout_table_main)
        main_layout.addLayout(layout_bot_buttons)
        
    def create_connections(self):
        self.button_set_from.clicked.connect(self.open_from_selector)
        self.button_set_to.clicked.connect(self.open_to_selector)
        self.button_init_trackers.clicked.connect(self.init_trackers)
        self.button_new_snapshot.clicked.connect(self.new_snapshot)
        self.button_dists.clicked.connect(self.update_distances)
        
        self.button_select_attrs.clicked.connect(self.select_attrs)
        self.button_zero.clicked.connect(self.reset_target_to_zero)
        self.button_solve.clicked.connect(self.solve)
        self.button_apply.clicked.connect(self.apply)
        self.button_bake.clicked.connect(self.bake)
        self.button_clear_animation.clicked.connect(self.clear_animation)
        
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
        
    def open_from_selector(self):
        self.input_selector.show()
        
    def open_to_selector(self):
        self.output_selector.show()
        
    def init_trackers(self):
        if self.mapper.is_initialized():
            if not altmaya.Ask.decision(self, "Restart trackers", "Restart trackers and earse snapshot data?"):
                self.report_warning("Cancelled command to restart trackers")
                return
        
        if len(self.input_selector.read_values_as_indices()) == 0:
            self.report_error("No input attributes are selected")
            return
            
        if len(self.output_selector.read_values_as_indices()) == 0:
            self.report_error("No output attributes are selected")
            return
            
        self.mapper.init_source(self.input_selector.read_values_as_indices())
        self.mapper.init_target(self.output_selector.read_values_as_indices())
        
        self.update_table()
        self.report_message("Successfully initialized")
        
    def update_distances(self, *args, **kwargs):
        table = self.table_snapshots
        table_keys = self.snapshot_table_column_names        
        c_name = table_keys.index("Name")
        
        if self.mapper.is_initialized():
            
            c_distance_s = table_keys.index("Dist S")
            curr_pose_s = numpy.array(self.mapper.source.current_pose())
            
            c_distance_t = table_keys.index("Dist T")
            curr_pose_t = numpy.array(self.mapper.target.current_pose())
            
            n = table.rowCount()
            for r in range(n):
                name = table.item(r, c_name).text()
                
                dist_label_s = table.item(r, c_distance_s)
                p = numpy.array(self.mapper.snapshots[name]["source"])
                distance = numpy.linalg.norm(curr_pose_s - p)
                dist_label_s.setText("%2.2fmm" % distance)
                
                dist_label_t = table.item(r, c_distance_t)
                p = numpy.array(self.mapper.snapshots[name]["target"])
                distance = numpy.linalg.norm(curr_pose_t - p)
                dist_label_t.setText("%2.2fmm" % distance)
            
    def update_table(self):
        # Columns are:
        #     Name | Log | DistS | DistT | GoTo Frame | GoTo Target | Delete
        
        
        names = self.mapper.names_of_snapshots()
        # TODO: remove this hack!!!!
        # names = sorted(names, key=lambda name: int(name[1:]))
        n = self.mapper.number_of_snapshots()
        
        self.table_snapshots.setRowCount(n)
        self.table_snapshots.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        
        def add_label(text, ix, col_name):
            item = QtWidgets.QTableWidgetItem()
            item.setText(text)
            self.table_snapshots.setItem(ix, self.snapshot_table_column_names.index(col_name), item)

        def add_button(text, callback, ix, col_name):
            button = QtWidgets.QPushButton(text)
            button.clicked.connect(callback)
            self.table_snapshots.setCellWidget(ix, self.snapshot_table_column_names.index(col_name), button)
            
        for (ix, name) in enumerate(names):

            # Name
            add_label(name, ix, "Name")
            
            # Log
            def callback(ix, name):
                snapshot = self.mapper.snapshots[name]
                def fn():
                    message = "Snapshot %s:" % name
                    message += "\n\tSource: %s" % str(snapshot["source"])
                    message += "\n\tTarget: %s" % str(snapshot["target"])
                    altmaya.Report.message(message)
                return fn
            add_button("Log", callback(ix, name), ix, "Log")
            
            # Distances
            add_label("", ix, "Dist S")
            add_label("", ix, "Dist T")
            
            # GoTo Frame
            def callback(ix, name):
                def fn():
                    if name.startswith("@") and name[1:].isdigit():
                        frame = float(name.split("@")[1])
                        altmaya.Timeline.set_current_frame(frame)
                    self.mapper.go_to_snapshot(name)
                return fn
            add_button("GoTo Frame", callback(ix, name), ix, "GoTo Frame")

            # GoTo Target
            def callback(ix, name):
                def fn():
                    self.mapper.go_to_snapshot(name)
                return fn
            add_button("GoTo Target", callback(ix, name), ix, "GoTo Target")
            
            # Delete
            def callback(ix, name):
                def fn():
                    self.report_message("Deleting snapshot %s" % name)
                    self.mapper.delete_snapshot(name)
                    self.update_table()
                return fn
            add_button("Delete", callback(ix, name), ix, "Delete")
            
        self.update_distances()
    
    def new_snapshot(self):
        if self.mapper.source is None:
            self.report_error("Source pose is not setup yet")
            return
        if self.mapper.source is None:
            self.report_error("Target pose is not setup yet")
            return
        n = self.mapper.number_of_snapshots()
        # name = "Snapshot %d" % (n + 1)
        name = "@%s" % int(altmaya.Timeline.get_current_frame())
        name = altmaya.Ask.string(self, "New Snapshot", "Enter name for snapshot", name)
        if name == "":
            self.report_warning("Cancelled new snapshot command (user cancelled)")
            return
        self.mapper.new_snapshot(name)
        self.report_message("New snapshot created: %s" % name)
        self.update_table()
    
    def select_attrs(self):
        attrs = []
        attrs += [a.key for a in self.mapper.source.attribute_indices]
        attrs += [a.key for a in self.mapper.target.attribute_indices]
        altmaya.Selection.set(attrs)
        
    def reset_target_to_zero(self):
        self.mapper.target.go_to_zero()
        self.report_message("Reset target to zero")
        
    def solve(self):
        try:
            self.mapper.sigma = self.edit_sigma.value()
            self.mapper.solve()
            self.report_message("Solved mapper")
        except numpy.linalg.LinAlgError as e:
            self.report_error("Failed to solve: do you have two or more snapshots with the same input values?")
        except ValueError as e:
            self.report_error(str(e))
    
    def apply(self):
        try:
            self.mapper.apply_current()
            self.report_message("Applied mapper")
        except ValueError as e:
            self.report_error(str(e))
            
    def bake(self):
        self.solve()
        
        s = int(altmaya.Timeline.get_start())
        e = int(altmaya.Timeline.get_end())
        n = e - s + 1
        m = len(self.mapper.target.attribute_indices)

        times = []
        anim = numpy.matrix(numpy.zeros((n, m)))
        for i in range(n):
            times.append(s + i)
            s_pose = self.mapper.source.pose_at_frame(s + i)
            t_pose = self.mapper.apply(s_pose)
            anim[i,:] = t_pose
        
        self.report_message("Baking attrs:")
        for ix, attr in enumerate(self.mapper.target.attribute_indices):
            self.report_message("   ... baking %s" % attr.key)
            values = anim[:,ix].flatten().tolist()[0]
            altmaya.Animation.add_keyframes(attr, times, values)
        self.report_message("Baked mapper")
        
    def clear_animation(self):
        s = int(altmaya.Timeline.get_start())
        e = int(altmaya.Timeline.get_end())
        self.report_message("Clearing attrs:")
        for attr in self.mapper.target.attribute_indices:
            self.report_message("       ... clearing attr %s" % attr.key)
            altmaya.Animation.clear_range(attr, s, e)
        self.report_message("Cleared animation")            
        
    def closeEvent(self, event):
        self.input_selector.close()
        self.output_selector.close()
        event.accept()
        

class MappingCollectionInterface(altmaya.StandardMayaWindow):
    
    def __init__(self):
        super(MappingCollectionInterface, self).__init__("Mapping Collection")

        self.mapper_table_column_names = [
            "Name",
            "Sigma",
            "Edit",
            "Solve",
            "Apply",
            "Active",
            "Delete"
        ]

        self.mappers = {}
        self.mapper_guis = {}
        self.active_callbacks = {}
        self.timeline_callback = None

        self.setGeometry(0, 0, 400, 400)
        self.create_widgets()
        self.create_layout()
        self.create_connections()

        self.update_table()
        self.report_message("Ready and Waiting")

    def create_widgets(self):
        
        # Status 
        self.status_bar = QtWidgets.QLabel("Status")
        
        # Top buttons
        self.button_export_mapping_data = QtWidgets.QPushButton("Export")
        self.button_import_mapping_data = QtWidgets.QPushButton("Import")

        # Table and buttons
        self.table_mappers = QtWidgets.QTableWidget(0, len(self.mapper_table_column_names), self)
        self.table_mappers.setHorizontalHeaderLabels(self.mapper_table_column_names)
        self.table_mappers.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.button_new_mapping = QtWidgets.QPushButton("New")

        # Bottom buttons
        self.button_zero = QtWidgets.QPushButton("Zero")
        self.button_snapshot_mappings = QtWidgets.QPushButton("Snapshot All")
        self.button_solve_mappings = QtWidgets.QPushButton("Solve")
        self.button_apply_mappings = QtWidgets.QPushButton("Apply")
        self.button_activate_timeline = QtWidgets.QPushButton("Go Go")
        self.button_key_snapshots = QtWidgets.QPushButton("Key Snapshots")
        self.button_bake_mappings = QtWidgets.QPushButton("Bake")
        self.button_clear_animation = QtWidgets.QPushButton("Clear Anim")

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
        layout_bot_buttons.addWidget(self.button_zero)
        layout_bot_buttons.addWidget(self.button_snapshot_mappings)
        layout_bot_buttons.addWidget(self.button_solve_mappings)
        layout_bot_buttons.addWidget(self.button_apply_mappings)
        layout_bot_buttons.addWidget(self.button_activate_timeline)
        layout_bot_buttons.addWidget(self.button_key_snapshots)
        layout_bot_buttons.addWidget(self.button_bake_mappings)
        layout_bot_buttons.addWidget(self.button_clear_animation)
        
        # Main
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.status_bar)
        main_layout.addLayout(layout_top_buttons)
        main_layout.addLayout(layout_table_main)
        main_layout.addLayout(layout_bot_buttons)
        
    def create_connections(self):
        self.button_export_mapping_data.clicked.connect(self.export_to_json_prompt)
        self.button_import_mapping_data.clicked.connect(self.import_from_json_prompt)
        
        self.button_new_mapping.clicked.connect(self.add_new_mapping)
        
        self.button_zero.clicked.connect(self.reset_targets_to_zero)
        self.button_snapshot_mappings.clicked.connect(self.snapshot_mappings)
        self.button_solve_mappings.clicked.connect(self.solve_mappings)
        self.button_apply_mappings.clicked.connect(self.apply_mappings)
        self.button_activate_timeline.clicked.connect(self.toggle_timeline_callback)
        self.button_key_snapshots.clicked.connect(self.keyframe_snapshots)
        self.button_bake_mappings.clicked.connect(self.bake_mappings)
        self.button_clear_animation.clicked.connect(self.clear_animation)
        
    def set_status(self, message, color_as_hex):
        font_hex = "%02x%02x%02x" % (55, 55, 55)
        self.status_bar.setText("> " + message)
        self.status_bar.setStyleSheet("background: #%s; color: #%s" % (color_as_hex, font_hex))
    
    def report_error(self, message):
        self.set_status(message, "F20505")
        altmaya.Report.error("Mapping Manager: " + message)
        
    def report_warning(self, message):
        self.set_status(message, "F2BE22")
        altmaya.Report.warning("Mapping Manager: " + message)
        
    def report_message(self, message):
        self.set_status(message, "446644")
        altmaya.Report.message("Mapping Manager: " + message)
        
    def export_to_json_prompt(self):
        filepath = altmaya.Ask.choose_file_to_save_json(self, "Export Mappers to JSON")
        if filepath == "":
            self.report_warning("Cancelled command to export mappers")
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
            
        self.report_message("Exported mappers to %s" % filepath)
        
    def import_from_json_filepath(self, filepath):
        with open(filepath, "r") as f:
            data = json.loads(f.read())
            
        for datum in data:
            m = mapper.CrossMapping()
            m.init_source([altmaya.AttributeIndex.from_key(key) for key in datum["source_indices"]])
            m.init_target([altmaya.AttributeIndex.from_key(key) for key in datum["target_indices"]])
            m.sigma = datum["sigma"]
            m.snapshots = datum["snapshots"]
            self.mappers[datum["name"]] = m
            
        self.report_message("Imported mappers from %s" % filepath)
        self.update_table()
        
    def import_from_json_prompt(self):
        filepath = altmaya.Ask.choose_file_to_open_json(self, "Import Mappers from JSON")
        if filepath == "":
            self.report_warning("Cancelled command to import mappers")
            return 
        else:
            self.import_from_json_filepath(filepath)
            
        
    def read_sigma(self, ix):
        slider = self.table_mappers.cellWidget(ix, self.mapper_table_column_names.index("Sigma"))
        return slider.value()
        
    def read_is_checked(self, ix):
        check = self.table_mappers.cellWidget(ix, self.mapper_table_column_names.index("Active"))
        return check.checkState() == QtCore.Qt.CheckState.Checked
        
    def read_is_checked_by_name(self, queried_name):
        for r in range(self.table_mappers.rowCount()):
            name = self.table_mappers.item(r, 0).text()
            if name == queried_name:
                return self.read_is_checked(r)
        raise ValueError("%s is not found in table?" % queried_name)
        return
        
    def update_table(self):
        # Columns are:
        #     Name | Sigma | Edit | Solve | Apply | Active | Delete
        self.mapper_guis = {}
        
        mappers = self.mappers
        keys = list(mappers.keys())

        self.table_mappers.setRowCount(len(keys))
        self.table_mappers.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        
        def add_label(text, ix, col_name):
            item = QtWidgets.QTableWidgetItem()
            item.setText(text)
            self.table_mappers.setItem(ix, self.mapper_table_column_names.index(col_name), item)
            
        def add_editable_number(init, ix, col_name):
            item = QtWidgets.QDoubleSpinBox()
            # item.setRange(0.0, 1.0)
            item.setSingleStep(0.01)
            item.setValue(init)
            self.table_mappers.setCellWidget(ix, self.mapper_table_column_names.index(col_name), item)

        def add_button(text, callback, ix, col_name):
            button = QtWidgets.QPushButton(text)
            button.clicked.connect(callback)
            self.table_mappers.setCellWidget(ix, self.mapper_table_column_names.index(col_name), button)
        
        def add_tick_box(callback, ix, col_name):
            tick = QtWidgets.QCheckBox()
            tick.toggled.connect(callback)
            self.table_mappers.setCellWidget(ix, self.mapper_table_column_names.index(col_name), tick)
        
        for (ix, key) in enumerate(keys):
            mapper = self.mappers[key]
            self.mapper_guis[key] = MappingEditorInterface(self, mapper, key)

            # Name
            add_label(key, ix, "Name")

            # Edit
            def callback(ix, key):
                def fn():
                    self.mapper_guis[key].show()
                return fn
            add_button("Edit", callback(ix, key), ix, "Edit")
                        
            # Solve
            def callback(ix, key):
                def fn():
                    try:
                        self.mappers[key].sigma = self.read_sigma(ix)
                        self.mappers[key].solve()
                        self.report_message("Solved %s" % key)
                    except ValueError as e:
                        self.report_error(str(e))
                return fn
            add_button("Solve", callback(ix, key), ix, "Solve")
            
            # Sigma
            add_editable_number(mapper.sigma, ix, "Sigma")

            # Apply
            def callback(ix, key):
                def fn():
                    try:
                        self.mappers[key].apply_current()
                        self.report_message("Applied %s" % key)
                    except ValueError as e:
                        self.report_error(str(e))
                return fn
            add_button("Apply", callback(ix, key), ix, "Apply")

            # Active
            def callback(ix, key):
                
                mapper = self.mappers[key]
                
                def make_attr_callback(mapper):
                    def fn(*args):
                        mapper.try_apply_current()
                    return fn
                        
                def fn(checked):
                    # self.report_warning("Call back turned off")
                    if checked:
                        print("Adding callbacks")
                        for ai in mapper.source.attribute_indices:
                            if not altmaya.AttributeChangeCallback.is_already_registered(ai):
                                attr_callback = make_attr_callback(mapper)
                                altmaya.AttributeChangeCallback(ai,attr_callback)
                    else:
                        print("Stopping callbacks")
                        for ai in mapper.source.attribute_indices:
                            if altmaya.AttributeChangeCallback.is_already_registered(ai):
                                altmaya.AttributeChangeCallback.kill_for_index(ai)
                return fn
            add_tick_box(callback(ix, key), ix, "Active")
            
            # Delete
            def callback(ix, key):
                def fn():
                    self.report_message("Deleting %s" % key)
                    del self.mappers[key]
                    self.update_table()
                return fn
            add_button("Delete", callback(ix, key), ix, "Delete")
            
    def add_new_mapping(self):
        n = len(self.mappers.keys())
        name = str("Mapper %d" % (n + 1))
        name = altmaya.Ask.string(self, "New Mapping", "Enter name for mapping:", name)
        if name != "":
            self.mappers[name] = mapper.CrossMapping()
            self.update_table()
            self.report_message("Created new mapping: %s" % name)
        else:
            self.report_warning("Cancelled command to make a new mapping (user cancelled)")
            
    def reset_targets_to_zero(self):
        keys = self.mappers.keys()
        for key in keys:
            mapper = self.mappers[key]
            mapper.target.go_to_zero()
        self.report_message("Reset targets to zero")
        
    def snapshot_mappings(self):
        c_name = self.mapper_table_column_names.index("Name")        
        n = self.table_mappers.rowCount()
        snapshot_name = "@%d" % int(altmaya.Timeline.get_current_frame())
        n_applied = 0
        for r in range(n):
            name = self.table_mappers.item(r, c_name).text()
            if self.read_is_checked_by_name(name):
                mapper = self.mappers[name]
                # if mapper.is_ready_to_run():
                try:
                    mapper.new_snapshot(snapshot_name)
                    self.report_message("took snapshot for " + name)
                    n_applied += 1
                except ValueError as e:
                    self.report_error("Failed to apply %s: %s" % (name, str(e)))
                    return
    
        for c in test_dialog.children():
            if type(c) == MappingEditorInterface:
                c.update_table()
                
        self.report_message("Snapshots taken for %d mappings" % (n_applied))
        
    def solve_mappings(self):
        c_name = self.mapper_table_column_names.index("Name")
        c_sigma = self.mapper_table_column_names.index("Sigma")
        
        n_applied = 0
        n = self.table_mappers.rowCount()
        for r in range(n):
            name = self.table_mappers.item(r, c_name).text()
            if self.read_is_checked_by_name(name):
                sigma = self.table_mappers.cellWidget(r, c_sigma).value()
                mapper = self.mappers[name]
                try:
                    mapper.sigma = sigma
                    mapper.solve()
                    self.report_message("solved " + name)
                    n_applied += 1
                except ValueError as e:
                    self.report_error("Failed to solve %s: %s" % (name, str(e)))
                    return
                    
        self.report_message("Solved %d mappings" % (n_applied))

    def apply_mappings(self):
        c_name = self.mapper_table_column_names.index("Name")        
        n = self.table_mappers.rowCount()
        n_applied = 0
        for r in range(n):
            name = self.table_mappers.item(r, c_name).text()
            if self.read_is_checked_by_name(name):
                mapper = self.mappers[name]
                if mapper.is_ready_to_run():
                    try:
                        mapper.apply_current()
                        n_applied += 1
                    except ValueError as e:
                        self.report_error("Failed to apply %s: %s" % (name, str(e)))
                        return
        
        self.report_message("Applied %d mappings" % (n_applied))

    def toggle_timeline_callback(self):
        def callback(_):
            self.apply_mappings()
                                                        
        if self.timeline_callback is None:
            self.report_message("Turning on timeline callback")
            self.timeline_callback = altmaya.TimelineChangeCallback(callback)
        else:
            self.report_message("Turning off timeline callback")
            self.timeline_callback.kill()
            self.timeline_callback = None
        
    def bake_mappings(self):
        self.solve_mappings()
        
        c_name = self.mapper_table_column_names.index("Name")
        s = int(altmaya.Timeline.get_start())
        e = int(altmaya.Timeline.get_end())
        n = e - s + 1
        
        self.report_message("Baking mappers:")
        
        n_mappers = self.table_mappers.rowCount()
        n_applied = 0
        for r in range(n_mappers):
            name = self.table_mappers.item(r, c_name).text()
            
            self.report_message("    ... baking mapper %s" % name)
            if self.read_is_checked_by_name(name):
                n_applied += 1 
                mapper = self.mappers[name]
        
                m = len(mapper.target.attribute_indices)

                times = []
                anim = numpy.matrix(numpy.zeros((n, m)))
                for i in range(n):
                    times.append(s + i)
                    s_pose = mapper.source.pose_at_frame(s + i)
                    t_pose = mapper.apply(s_pose)
                    anim[i,:] = t_pose
                
                for ix, attr in enumerate(mapper.target.attribute_indices):
                    self.report_message("       ... baking attr %s" % attr.key)
                    values = anim[:,ix].flatten().tolist()[0]
                    altmaya.Animation.add_keyframes(attr, times, values)
        
        self.report_message("Baked %d mappers" % n_applied)

    def keyframe_snapshots(self):
        self.solve_mappings()
        
        c_name = self.mapper_table_column_names.index("Name")
        
        self.report_message("Keying snapshots:")
        
        n_mappers = self.table_mappers.rowCount()
        n_applied = 0
        for r in range(n_mappers):
            name = self.table_mappers.item(r, c_name).text()
            
            self.report_message("    ... keying snapshots in mapper %s" % name)
            if self.read_is_checked_by_name(name):
                n_applied += 1 
                mapper = self.mappers[name]
                keyframes = mapper.keyframes_of_snapshots()
                attrs = mapper.target.attribute_indices
                
                
                for (i, k) in enumerate(keyframes):
                    self.report_message("        ... keying for frame %d" % k)
                    s_pose = mapper.source.pose_at_frame(k)
                    t_pose = mapper.apply(s_pose)
                    for (attr, value) in zip(attrs, t_pose):
                        self.report_message("            ... set attr %s to %2.2f" % (attr.key, value))
                        attr.set_at_time(k, value)
        
        self.report_message("Keyed snapshots for %d mappers" % n_applied)
    
    def clear_animation(self):        
        c_name = self.mapper_table_column_names.index("Name")
        s = int(altmaya.Timeline.get_start())
        e = int(altmaya.Timeline.get_end())
        
        self.report_message("Clearning animation:")
        
        n_mappers = self.table_mappers.rowCount()
        n_applied = 0
        for r in range(n_mappers):
            name = self.table_mappers.item(r, c_name).text()
            
            self.report_message("    ... clearing mapper %s" % name)
            if self.read_is_checked_by_name(name):
                n_applied += 1    
                mapper = self.mappers[name]
                
                for attr in mapper.target.attribute_indices:
                    self.report_message("       ... clearing attr %s" % attr.key)
                    altmaya.Animation.clear_range(attr, s, e)
                    
        self.report_message("Cleared %d mappers" % n_applied)
        
    def closeEvent(self, event):
        altmaya.AttributeChangeCallback.clear()
        for c in self.children():
            if type(c) == MappingEditorInterface:
                c.close()
        
        # Turn off all callbacks
        if self.timeline_callback is not None:
            self.timeline_callback.kill()
        for key in self.mappers.keys():
            mapper = self.mappers[key]
            for ai in mapper.source.attribute_indices:
                if altmaya.AttributeChangeCallback.is_already_registered(ai):
                    altmaya.AttributeChangeCallback.kill_for_index(ai)
                    
        self.report_message("Enjoy your mapping!")
        event.accept()
