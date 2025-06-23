import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, simpledialog
import sys
import os
import json
import threading

# === Utility for PyInstaller pathing ===
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def default_desktop_path():
    return os.path.join(os.path.expanduser("~"), "Desktop", "00000 Misdemeanor Clients")

def ensure_config():
    path = resource_path("config.json")
    if not os.path.exists(path):
        config = {
            "bar_number": "00000",
            "destination_folder": default_desktop_path()
        }
        os.makedirs(config["destination_folder"], exist_ok=True)
        with open(path, "w") as f:
            json.dump(config, f, indent=2)
    else:
        with open(path, "r") as f:
            config = json.load(f)
        if "bar_number" not in config:
            config["bar_number"] = "00000"
        if "destination_folder" not in config:
            config["destination_folder"] = default_desktop_path()
        os.makedirs(config["destination_folder"], exist_ok=True)
        with open(path, "w") as f:
            json.dump(config, f, indent=2)
    return config

class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, s):
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, s)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state='disabled')

    def flush(self):
        pass

def run_gui():
    config_path = resource_path("config.json")
    config = ensure_config()

    def save_config():
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    root = tk.Tk()
    root.title("DocketBot")
    root.geometry("850x650")

    label_bar = tk.Label(root, text=f"Bar Number: {config['bar_number']}", font=("Arial", 10, "bold"))
    label_bar.pack(pady=5)

    label_dest = tk.Label(root, text=f"Destination Folder: {config['destination_folder']}", font=("Arial", 10))
    label_dest.pack(pady=5)

    def change_bar_number():
        new_bar = simpledialog.askstring("Change Bar Number", "Enter new Bar Number:", parent=root)
        if new_bar:
            config["bar_number"] = new_bar
            label_bar.config(text=f"Bar Number: {new_bar}")
            # auto-update destination folder if it includes bar number
            if "Misdemeanor Clients" in config["destination_folder"]:
                base = os.path.dirname(config["destination_folder"])
                config["destination_folder"] = os.path.join(base, f"{new_bar} Misdemeanor Clients")
                os.makedirs(config["destination_folder"], exist_ok=True)
                label_dest.config(text=f"Destination Folder: {config['destination_folder']}")
            save_config()

    def change_folder():
        base_folder = filedialog.askdirectory(title="Select base folder")
        if base_folder and config.get("bar_number"):
            final_folder = os.path.join(base_folder, f"{config['bar_number']} Misdemeanor Clients")
            os.makedirs(final_folder, exist_ok=True)
            config["destination_folder"] = final_folder
            label
