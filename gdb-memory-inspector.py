import json
import threading
from PyQt5.QtWidgets import *
from pygdbmi import gdbmiparser
from pygdbmi import gdbcontroller

class MemorySpaceView(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("Hello Qt"))
        btn = QPushButton('Top')
        #btn.clicked.connect(self.parent.fn)
        self.layout.addWidget(btn)
        self.layout.addWidget(QPushButton('Bottom'))
        self.table = QTableWidget(0, 3)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)
    
    def library_loaded(self, library):
        self.table.insertRow(self.table.rowCount())
        self.table.setItem(self.table.rowCount() - 1, 0, QTableWidgetItem(library["id"]))
        self.table.setItem(self.table.rowCount() - 1, 1, QTableWidgetItem(library["ranges"][0]["from"]))
        self.table.setItem(self.table.rowCount() - 1, 2, QTableWidgetItem(library["ranges"][0]["to"]))

class GdbMemoryInspector(QApplication):
    def __init__(self):
        super().__init__([])

        # Start gdb
        self.gdbmi = gdbcontroller.GdbController()
        self.gdbmi_read_thread = threading.Thread(target=self.gdbmi_read_thread)
        self.gdbmi_read_thread.start()

        # Start program
        self.gdbmi_execute("-target-attach 15108")

        # Init UI
        self.create_interface()
    
    def gdbmi_read_thread(self):
        try:
            responses = self.gdbmi.get_gdb_response()
        except gdbcontroller.GdbTimeoutError:
            pass
        else:
            for response in responses:
                self.gdbmi_handle_response(response)
    
    def gdbmi_handle_response(self, response):
        print(json.dumps(response, indent=2))
        if response["type"] == "notify" and response["message"] == "library-loaded":
            self.window.library_loaded(response["payload"])

    def gdbmi_execute(self, command):
        self.gdbmi.write(command, read_response=False)

    def create_interface(self):
        self.window = MemorySpaceView(self)
        self.window.show()

if __name__ == "__main__":
    GdbMemoryInspector().exec_()
