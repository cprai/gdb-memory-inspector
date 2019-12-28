import re
import gdb
import sys
import json
import inspect
import tkinter as tk
from tkinter import ttk

def find_memory_offsets():
    offsets = []

    memory_space = gdb.execute("info proc mappings", to_string=True).split("\n")[4:-1]
    memory_space = [section.split() for section in memory_space]
    memory_space = [
            {"name": " ".join(section[4:]), "base": int(section[0], base=16), "size": int(section[2], base=16)}
        for section in memory_space
    ]
    for section in memory_space:
        if len(section["name"]) > 0:
            continue

        offsets += [{"name": section["name"], "base": section["base"], "size": section["size"]}]

    return offsets

# http://www.rexegg.com/regex-interesting-character-classes.html
# https://sourceware.org/gdb/onlinedocs/gdb/Inferiors-In-Python.html
def search_memory(base, size, query):
    matches = {}

    try:
        memory = gdb.selected_inferior().read_memory(base, size)
        for match in re.finditer(query, memory):
            matches[base + match.start(0)] = match.group(0)
    except gdb.MemoryError:
        pass

    return matches

def full_scan_i32(query):
    memory_space = find_memory_offsets()

    searched = []
    found = set()
    for location in memory_space:
        identifier = str(location["base"]) + "-" + str(location["size"])
        if identifier in searched:
            continue
        searched += [identifier]

        matches = search_memory(location["base"], location["size"], query.to_bytes(1, sys.byteorder))
        for address, match in matches.items():
            number = int.from_bytes(match, byteorder=sys.byteorder, signed=True)
            found.add(address)
            #print(str(address) + ": " + str(number))

    #print(json.dumps(found, indent=2))
    return found

def read_byte_set(byte_set, radius):
    for address in byte_set:
        print(hex(address) + ": \t", end="")
        for i in range(-radius, radius + 1):
            memory = gdb.selected_inferior().read_memory(address + i, 1)
            number = int.from_bytes(memory, byteorder=sys.byteorder, signed=False)
            if i == 0:
                print("\u001b[31m", end="")
            print(hex(number), end="\u001b[0m\t")
        print("")

def write_byte_set(byte_set, offset, value):
    for address in byte_set:
        gdb.selected_inferior().write_memory(address + offset, value.to_bytes(1, sys.byteorder))

class MainWindow(tk.Frame):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.initUI()

    def show(self):
        self.list.insert("", "end", values=("123", "asfasd", "1342"))

    def initUI(self):
        self.master.title("Buttons")
        self.style = ttk.Style()
        self.style.theme_use("default")

        label = tk.Label(self.window, text="High Scores", font=("Arial",30)).grid(row=0, column=0, rowspan=1, columnspan=1)

        columns = ('Position', 'Name', 'Score')
        self.list = ttk.Treeview(self.window, columns=columns, show='headings')
        for column in columns:
            self.list.heading(column, text=column)    
        self.list.grid(row=1, column=0, rowspan=1, columnspan=1)

        showScores = tk.Button(self.window, text="Show scores", width=15, command=self.show).grid(row=2, column=0, rowspan=1, columnspan=1)

window = tk.Tk()
window.title("GUI")
window.geometry("500x500")
app = MainWindow(window)
window.mainloop()
