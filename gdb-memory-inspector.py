#!/usr/bin/env python3

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
        btn.clicked.connect(self.parent.boom)
        self.layout.addWidget(btn)
        self.layout.addWidget(QPushButton('Bottom'))
        self.table = QTableWidget(0, 3)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

    def library_loaded(self, library):
        self.table.insertRow(self.table.rowCount())
        self.table.setItem(self.table.rowCount() - 1, 0, QTableWidgetItem(library["id"]))
        if len(library["ranges"][0]) > 0:
            self.table.setItem(self.table.rowCount() - 1, 1, QTableWidgetItem(library["ranges"][0]["from"]))
            self.table.setItem(self.table.rowCount() - 1, 2, QTableWidgetItem(library["ranges"][0]["to"]))

class ProcessControlBar(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.layout = QGridLayout()

        attachButton = QPushButton("Attach")
        attachButton.clicked.connect(self.on_attach)
        self.layout.addWidget(attachButton, 0, 0, 1, 1)

        self.textbox = QLineEdit()
        self.layout.addWidget(self.textbox, 0, 1, 1, 1)

        self.setLayout(self.layout)

    def on_attach(self):
        target = int(self.textbox.text())
        self.parent.gdbmi_attach(target)

class GdbMemoryInspector(QApplication):
    def __init__(self):
        super().__init__([])

        # Start gdb
        self.gdbmi = gdbcontroller.GdbController()
        self.gdbmi_read_thread = threading.Thread(target=self.gdbmi_read_thread)
        self.gdbmi_read_thread.start()

        # Init UI
        self.create_interface()

    def boom(self):
        self.gdbmi_execute("info proc mappings")
        self.gdbmi_execute("c")

    def gdbmi_attach(self, target):
        print(target)
        self.gdbmi_execute("-target-attach %d" % (target,))

    def gdbmi_read_thread(self):
        while True:
            try:
                responses = self.gdbmi.get_gdb_response()
            except gdbcontroller.GdbTimeoutError:
                pass
            else:
                for response in responses:
                    self.gdbmi_handle_response(response)

    def gdbmi_handle_response(self, response):
        print(json.dumps(response, indent=2))
        #if response["type"] == "notify" and response["message"] == "library-loaded":
        if response["message"] == "library-loaded":
            self.memorySpaceView.library_loaded(response["payload"])

    def gdbmi_execute(self, command):
        self.gdbmi.write(command, read_response=False)

    def create_interface(self):
        self.window = QWidget()
        self.layout = QGridLayout()
        self.layout.addWidget(ProcessControlBar(self), 0, 0, 1, 1)
        self.memorySpaceView = MemorySpaceView(self)
        self.layout.addWidget(self.memorySpaceView, 1, 0, 1, 1)
        self.window.setLayout(self.layout)
        self.window.show()

if __name__ == "__main__":
    GdbMemoryInspector().exec_()
