import gui
reload(gui)

try:
    cmm_interface.close() # pylint: disable=E0601
    cmm_interface.deleteLater()
except:
    pass

cmm_interface = gui.MappingCollectionInterface()
cmm_interface.import_from_json_filepath("/Users/richardroberts/Development/CrossMappingMaya/testing.json")
cmm_interface.show()

