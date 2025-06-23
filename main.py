import subprocess
import os
import sys
import json
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, simpledialog

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def default_desktop_path():
    return os.path.join(os.path.expanduser("~"), "Desktop", "00000 Misdemeanor Clients")

def ensure_config():
    path = resource_path("config.json")
    config = {
        "bar_number": "00000",
        "destination_folder": default_desktop_path()
    }

    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                existing = json.load(f)
                config.update(existing)
        except:
            pass

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

def open_folder(path):
    path = os.path.realpath(path)
    print(f"[DEBUG] Opening folder: {path}")
    if os.path.exists(path) and os.path.isdir(path):
        if os.name == 'nt':
            subprocess.run(f'explorer "{path}"', shell=True)
        elif os.name == 'posix':
            subprocess.run(["xdg-open", path])
    else:
        messagebox.showerror("Error", f"Folder does not exist:\n{path}")

def run_gui():
    config_path = resource_path("config.json")
    config = ensure_config()

    def save_config():
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"[DEBUG] Saved config: {config}")

    root = tk.Tk()
    root.title("DocketBot")
    root.configure(padx=20, pady=20)
    root.resizable(False, False)

    # === Bar Number Display ===
    bar_frame = tk.Frame(root)
    bar_frame.pack(anchor="w", pady=(0, 5))

    label_bar = tk.Label(bar_frame, text=f"Bar Number: {config['bar_number']}", font=("Segoe UI", 11, "bold"))
    label_bar.pack(anchor="w")

    def change_bar_number():
        new_bar = simpledialog.askstring("Change Bar Number", "Enter new Bar Number:", parent=root)
        if new_bar:
            config["bar_number"] = new_bar
            label_bar.config(text=f"Bar Number: {new_bar}")
            save_config()

    tk.Button(bar_frame, text="Change Bar Number", command=change_bar_number).pack(anchor="w", pady=2)

    # === Destination Folder Display ===
    dest_frame = tk.Frame(root)
    dest_frame.pack(anchor="w", pady=(10, 5))

    label_dest = tk.Label(dest_frame, text=f"Destination Folder: {config['destination_folder']}", font=("Segoe UI", 10))
    label_dest.pack(anchor="w")

    def change_folder():
        base_folder = filedialog.askdirectory(title="Select base folder")
        if base_folder and config.get("bar_number"):
            final_folder = os.path.join(base_folder, f"{config['bar_number']} Misdemeanor Clients")
            config["destination_folder"] = final_folder
            label_dest.config(text=f"Destination Folder: {final_folder}")
            save_config()

    buttons_row = tk.Frame(dest_frame)
    buttons_row.pack(anchor="w", pady=2)

    tk.Button(buttons_row, text="Change Folder", command=change_folder).pack(side="left", padx=(0, 10))
    tk.Button(buttons_row, text="Open Folder", command=lambda: open_folder(config["destination_folder"])).pack(side="left")

    # === Output Box ===
    output_box = scrolledtext.ScrolledText(root, state='disabled', width=80, height=12, wrap='word')  # Fixed size
    output_box.pack(pady=15, expand=False)  # Removed fill="both" to keep it small

    sys.stdout = StdoutRedirector(output_box)
    sys.stderr = StdoutRedirector(output_box)

    continue_event = threading.Event()

    def run_script():
        try:
            btn_run.config(state='disabled')
            btn_continue.config(state='normal')

            # Only now create the folder
            os.makedirs(config["destination_folder"], exist_ok=True)

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

    # === Control Buttons ===
    controls_frame = tk.Frame(root)
    controls_frame.pack(pady=10)

    btn_run = tk.Button(controls_frame, text="Start", width=20, command=run_script)
    btn_run.pack(side="left", padx=10)

    btn_continue = tk.Button(controls_frame, text="Continue (after captcha)", width=30, command=continue_scrape)
    btn_continue.pack(side="left", padx=10)
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
