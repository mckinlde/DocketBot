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
            label_dest.config(text=f"Destination Folder: {final_folder}")
            save_config()

    tk.Button(root, text="Change Bar Number", command=change_bar_number).pack(pady=2)
    tk.Button(root, text="Change Destination Folder", command=change_folder).pack(pady=2)

    output_box = scrolledtext.ScrolledText(root, state='disabled', width=100, height=25, wrap='word')
    output_box.pack(padx=10, pady=10)

    sys.stdout = StdoutRedirector(output_box)
    sys.stderr = StdoutRedirector(output_box)

    continue_event = threading.Event()

    def run_script():
        try:
            btn_run.config(state='disabled')
            btn_continue.config(state='normal')

            def target():
                from scraper_core import run_main
                run_main(continue_event=continue_event)

            threading.Thread(target=target, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to run scraper: {e}")
            btn_run.config(state='normal')
            btn_continue.config(state='disabled')

    def continue_scrape():
        btn_continue.config(state='disabled')
        print("\nUser clicked Continue: proceeding with scraping...\n")
        continue_event.set()

    btn_run = tk.Button(root, text="Start", width=20, command=run_script)
    btn_run.pack(pady=5)

    btn_continue = tk.Button(root, text="Continue (after captcha)", width=30, command=continue_scrape)
    btn_continue.pack(pady=5)
    btn_continue.config(state='disabled')

    root.mainloop()

def run_scraper():
    from scraper_core import run_main
    run_main()

def main():
    ensure_config()
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        run_scraper()
    else:
        run_gui()

if __name__ == "__main__":
    main()
