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

def full_scan_integer(number, bytes, byteorder, signed):
    memory_space = find_memory_offsets()

    searched = []
    found = set()
    for location in memory_space:
        identifier = str(location["base"]) + "-" + str(location["size"])
        if identifier in searched:
            continue
        searched += [identifier]

        query = number.to_bytes(bytes, byteorder=byteorder, signed=signed)
        matches = search_memory(location["base"], location["size"], re.escape(query))
        for address, match in matches.items():
            number = int.from_bytes(match, byteorder=byteorder, signed=signed)
            found.add(address)

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

    def initUI(self):
        self.master.title("Buttons")
        self.style = ttk.Style()
        self.style.theme_use("default")

        tk.Label(self.window, text="High Scores", font=("Arial",30)).grid(row=0, column=0, rowspan=1, columnspan=1)

        columns = ('Position', 'Name', 'Score')
        self.list = ttk.Treeview(self.window, columns=columns, show='headings')
        for column in columns:
            self.list.heading(column, text=column)    
        self.list.grid(row=1, column=0, rowspan=1, columnspan=1)

        self.value_entry = tk.Entry(self.window)
        self.value_entry.grid(row=2, column=0, rowspan=1, columnspan=1)

        self.bytes_entry = tk.Entry(self.window)
        self.bytes_entry.grid(row=3, column=0, rowspan=1, columnspan=1)

        tk.Button(self.window, text="New Scan", width=15, command=self.new_scan).grid(row=4, column=0, rowspan=1, columnspan=1)
        tk.Button(self.window, text="Update Scan", width=15, command=self.update_scan).grid(row=5, column=0, rowspan=1, columnspan=1)
        tk.Button(self.window, text="Play", width=15, command=self.play).grid(row=6, column=0, rowspan=1, columnspan=1)
    
    def do_integer_scan(self):
        value = int(self.value_entry.get())
        bytes = int(self.bytes_entry.get())
        return full_scan_integer(value, bytes, sys.byteorder, True)

    def new_scan(self):
        self.found = self.do_integer_scan()
        self.update_list()

    def update_scan(self):
        self.found = self.found.intersection(self.do_integer_scan())
        self.update_list()

    def update_list(self):
        self.list.delete(*self.list.get_children())
        i = 0
        for address in self.found:
            if i > 20:
                break
            i += 1

            self.list.insert("", "end", values=(address, "fsda", 42))
    
    def play(self):
        gdb.execute("continue")
    
window = tk.Tk()
window.title("GUI")
window.geometry("500x500")
app = MainWindow(window)
window.mainloop()
