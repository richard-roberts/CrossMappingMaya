import sys

try:
    import AltMaya.gui as gui
except ImportError:
    sys.path.append("D:/Development")
    import AltMaya.gui as gui
    
    
class PikuPikuInterface(StandardWindow):
    
    default_window_size = 21
    default_gauss_width = 7
    default_alpha = 0.80
    default_k_nearest_neigbour = 1
    
    file_filters = "CSV (*.csv);;All Files (*.*)"
    selected_file_filter = "CSV (*.csv)"

    def __init__(self):
        super(PikuPikuInterface, self).__init__("Piku Piku")
                    
        self.last_row_executed = -1
        self.anim_curve_caches_by_row_index = {}

        self.setMinimumSize(1000, 800)
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        
    def get_item_text(self, item): return item.text()
    def set_item_text(self, item, text): item.setText(text)
    
    VALUE_ROLE = QtCore.Qt.UserRole
    def get_item_value(self, item): return item.data(self.VALUE_ROLE)
    def set_item_value(self, item, value): item.setData(self.VALUE_ROLE, value)

    def create_widgets(self):
        
        self.table_wdg.setColumnCount(11)
        self.table_wdg.setColumnWidth( 1, 100)
        self.table_wdg.setColumnWidth( 2, 80)
        self.table_wdg.setColumnWidth( 3, 80)
        self.table_wdg.setColumnWidth( 4, 80)
        self.table_wdg.setColumnWidth( 5, 80)
        self.table_wdg.setColumnWidth( 6, 80)
        self.table_wdg.setColumnWidth( 7, 80)
        self.table_wdg.setColumnWidth( 8, 60)
        self.table_wdg.setColumnWidth( 9, 60)
        self.table_wdg.setColumnWidth(10, 60)
        self.table_wdg.setHorizontalHeaderLabels([
            "Maya Index",
            "Reference Index",
            "Patch Size",
            "Gauss Width",
            "Alpha",
            "K Nearest",
            "Execution",
            "Time (ms)",
            "Select",
            "Revert",
            "Cache"
        ])
        self.table_wdg.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.table_wdg.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)        
        self.set_attributes_button = QtWidgets.QPushButton("Set Attributes")
        self.add_patch_sets_button = QtWidgets.QPushButton("Add Patch Sets")
        self.reset_patch_sets_button = QtWidgets.QPushButton("Reset Patch Sets")
        self.select_all_button = QtWidgets.QPushButton("Select All")
        self.deselect_all_button = QtWidgets.QPushButton("Clear Selection")
        self.execute_all_button = QtWidgets.QPushButton("Execute All")
        self.revert_all_button = QtWidgets.QPushButton("Revert All")
        self.close_button = QtWidgets.QPushButton("Close")

    def create_layout(self):
        table_layout = QtWidgets.QHBoxLayout()
        table_layout.addWidget(self.table_wdg)
        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.set_attributes_button)
        button_layout.addWidget(self.add_patch_sets_button)
        button_layout.addWidget(self.reset_patch_sets_button)
        button_layout.addWidget(self.select_all_button)
        button_layout.addWidget(self.deselect_all_button)
        button_layout.addWidget(self.execute_all_button)
        button_layout.addWidget(self.revert_all_button)
        button_layout.addWidget(self.close_button)
            
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(table_layout)
        main_layout.addLayout(button_layout)
        
    def create_connections(self):
        self.set_attributes_button.clicked.connect(self.set_attributes)
        self.add_patch_sets_button.clicked.connect(self.add_patch_sets)
        self.reset_patch_sets_button.clicked.connect(self.reset_patch_sets)
        self.select_all_button.clicked.connect(self.select_all)
        self.deselect_all_button.clicked.connect(self.deselect_all)
        self.execute_all_button.clicked.connect(self.execute_all)
        self.revert_all_button.clicked.connect(self.revert_all)
        self.close_button.clicked.connect(self.close)
        
  
    
    def insert_row(self, maya_index, patch_set=None):
        i = self.table_wdg.rowCount()
        self.table_wdg.insertRow(i)
        self.insert_standard_item (i,  0, str(maya_index), maya_index)
        self.insert_choice_item   (i,  1, maya.cmds.pikupikuGetSets())
        self.insert_standard_item (i,  2, str(self.default_window_size), self.default_window_size)
        self.insert_standard_item (i,  3, str(self.default_gauss_width), self.default_gauss_width)
        self.insert_standard_item (i,  4, str(self.default_alpha), self.default_alpha)
        self.insert_standard_item (i,  5, str(self.default_k_nearest_neigbour), self.default_k_nearest_neigbour)
        self.insert_button_item   (i,  6, "Select", self.create_select_for_row_fn(i))
        self.insert_readonly_item (i,  7, "", -1.0)
        self.insert_button_item   (i,  8, "Execute", self.create_pikupiku_for_row_fn(i))
        self.insert_button_item   (i,  9, "Revert", self.create_revert_for_row_fn(i))
        self.insert_button_item   (i, 10, "Cache", self.create_cache_for_row_fn(i))
        
        
        if patch_set:
            index = self.table_wdg.cellWidget(i, 1).findText(patch_set, QtCore.Qt.MatchFixedString)
            if index < 0:
                Display.error("%s is not a valid patch set" % patch_set)
            else:
                self.table_wdg.cellWidget(i, 1).setCurrentIndex(index)
        
        curve = AnimationCurve(maya_index)
        curve.cache_current()
        self.anim_curve_caches_by_row_index[i] = curve
        
    def set_attributes(self):
        dialog = AttributeSelectorForCurrentSelection()
        dialog.exec_()
        for maya_index in dialog.read_values_as_indices():
            self.insert_row(maya_index)
            
    def update_patch_set_choice_widgets(self):
        for r in range(self.table_wdg.rowCount()):
            widget = self.table_wdg.cellWidget(r, 1)
            while widget.count() > 0: widget.removeItem(0)
            widget.addItems(maya.cmds.pikupikuGetSets())
    
    def add_patch_sets_from_file(self, filepath):
        patch_size = self.default_window_size
        gauss_width = self.default_gauss_width
        alpha = self.default_alpha
        maya.cmds.pikupikuAddSets(filepath, patch_size, gauss_width, alpha)
        self.update_patch_set_choice_widgets()
                
    def add_patch_sets(self):
        patch_size = self.default_window_size
        gauss_width = self.default_gauss_width
        alpha = self.default_alpha
        
        filepath, self.selected_file_filter = QtWidgets.QFileDialog.getOpenFileName(self, "Select reference filepath", "", self.file_filters, self.selected_file_filter)
        if filepath:
            if not os.path.exists(filepath):
                Dispay.error("The file %s does not exist" % filepath)
            else:
                self.add_patch_sets_from_file(filepath)
        else:
            Display.warning("cancelling add patch sets (not filepath provided")
            
    def reset_patch_sets(self):
        cmds.unloadPlugin("pikupikuCmd")
        cmds.loadPlugin("pikupikuCmd")
            
    def deselect_all(self):
        Selection.clear()
    
    def select_all(self):
        Selection.clear()
        for r in range(self.table_wdg.rowCount()):
            maya_index = self.get_item_value(self.table_wdg.item(r, 0))
            Selection.add(maya_index.obj)
        
    def run_pikupiku_for_row(self, row_index):    
        r = row_index
        self.last_row_executed = r
        
        patch_set_name = self.table_wdg.cellWidget(r, 1).currentText()
        maya_index  = self.get_item_value(self.table_wdg.item(r, 0))
        patch_size  = float(self.get_item_text(self.table_wdg.item(r, 2)))
        gauss_width = float(self.get_item_text(self.table_wdg.item(r, 3)))
        alpha       = float(self.get_item_text(self.table_wdg.item(r, 4)))
        k_nn        = float(self.get_item_text(self.table_wdg.item(r, 5)))
        exe_speed_item = self.table_wdg.item(r, 7)
        
        print(patch_set_name, str(maya_index), patch_size, gauss_width, alpha, k_nn)

        start_time = time.time()
        output = maya.cmds.pikupikuRun(patch_set_name, maya_index.obj, maya_index.attr, patch_size, gauss_width, alpha, k_nn)
        end_time = time.time()
        
        time_in_milliseconds = (end_time - start_time) * 1000.0
        self.set_item_text(exe_speed_item, "%03d" % time_in_milliseconds)
        
        # Set keyframes on curve
        History.start_undo_block()
        s = int(Timeline.get_start()) + int(patch_size / 2) + 1
        e = s + len(output)
        maya.cmds.cutKey(str(maya_index), time=(s, e))
        for ix in range(len(output)):
            t = s + ix
            cmds.setKeyframe(str(maya_index), time=t, value=output[ix])
        History.finish_undo_block()
        
    def rerun_last_executed_row(self):
        if self.last_row_executed == -1: 
            Display.warning("PikuPiku has not been run yet (execute a row to get started)")
            return
        else:
            self.run_pikupiku_for_row(self.last_row_executed)
       
    def create_pikupiku_for_row_fn(self, row):
        def fn():
            self.run_pikupiku_for_row(row)
        return fn
    
    def execute_all(self):
        for r in range(self.table_wdg.rowCount()):
            self.run_pikupiku_for_row(r)
        
    def revert_row(self, row_index):
        r = row_index
        self.anim_curve_caches_by_row_index[r].revert_to_cached()
        
    def revert_all(self):
        for r in range(self.table_wdg.rowCount()):
            self.revert_row(r)
        
    def create_revert_for_row_fn(self, row):
        def fn():
            self.revert_row(row)
        return fn
        
    def cache_row(self, row_index):
        r = row_index
        self.anim_curve_caches_by_row_index[r].cache_current()
        
    def create_cache_for_row_fn(self, row):
        def fn():
            self.cache_row(row)
        return fn
        
    def select_row(self, row_index):
        r = row_index
        index = self.get_item_value(self.table_wdg.item(r, 0))
        Selection.add(index.obj)
        
    def create_select_for_row_fn(self, row):
        def fn():
            self.select_row(row)
        return fn
        
    
if __name__ == "__main__":
    
    # maya.cmds.loadPlugin("PikuPikuCmd.py")
    maya.cmds.loadPlugin("pikupikuCmd")
    
    try:
        test_dialog.close() # pylint: disable=E0601
        test_dialog.deleteLater()
    except:
        pass
        
    patch_sets = maya.cmds.pikupikuGetSets()
        
    test_dialog = PikuPikuInterface()
    test_dialog.add_patch_sets_from_file("D:/Rafa-FACS.csv")
    # test_dialog.add_patch_sets_from_file("D:/Rafa-Expressions.csv")
    for o in Selection.get():
        # x1 = o.split("_")[0]
        # print(x1)
        # x2 = x1.split("AU")[1]
        # print(x2)
        au_index = int(o.split("_")[0].split("AU")[1])
        patch_set = "AU%02d" % au_index
        if patch_set in patch_sets:
            maya_index = AttributeIndex(o, "tx")
            test_dialog.insert_row(maya_index, patch_set=patch_set)
    test_dialog.show()
