# main.py

import subprocess
import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog

APP_NAME = "DocketBot"
DEFAULT_BAR = "00000"

CONFIG_KEYS = {
    "scraper.bar_number": DEFAULT_BAR,
    "scraper.destination_folder": os.path.join(os.path.expanduser("~"), "Desktop", f"{DEFAULT_BAR} Misdemeanor Clients"),
    "waiver.waiver_output_dir": os.path.join(os.path.expanduser("~"), "Desktop", f"{DEFAULT_BAR} Misdemeanor Waivers"),
    "waiver.signature_image_path": os.path.join(os.path.expanduser("~"), "Desktop", "signature.png")
}

def config_path():
    return os.path.join(os.environ["LOCALAPPDATA"], APP_NAME, "config.json")

def ensure_config():
    path = config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
    else:
        data = {}
    updated = False
    for key, default in CONFIG_KEYS.items():
        if key not in data:
            data[key] = default
            updated = True
    if updated:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    return data

def save_config(config):
    with open(config_path(), "w") as f:
        json.dump(config, f, indent=2)

def load_config():
    with open(config_path(), "r") as f:
        return json.load(f)

def reset_config():
    bar = CONFIG_KEYS["scraper.bar_number"]
    updated_config = {
        "scraper.bar_number": bar,
        "scraper.destination_folder": os.path.join(os.path.expanduser("~"), "Desktop", f"{bar} Misdemeanor Clients"),
        "waiver.waiver_output_dir": os.path.join(os.path.expanduser("~"), "Desktop", f"{bar} Misdemeanor Waivers"),
        "waiver.signature_image_path": CONFIG_KEYS["waiver.signature_image_path"]
    }
    save_config(updated_config)
    return updated_config

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
    if os.path.exists(path) and os.path.isdir(path):
        if os.name == 'nt':
            subprocess.run(f'explorer "{path}"', shell=True)
        else:
            subprocess.run(["xdg-open", path])
    else:
        messagebox.showerror("Error", f"Folder does not exist:\n{path}")

def run_gui():
    config = ensure_config()

    def reload_config():
        nonlocal config
        config = load_config()
        update_settings_tab()

    def perform_reset():
        result = messagebox.askyesno("Reset Config", "Are you sure you want to reset all settings to defaults?")
        if result:
            nonlocal config
            config = reset_config()
            update_settings_tab()

    root = tk.Tk()
    root.title("DocketBot")
    root.configure(padx=20, pady=20)
    root.resizable(False, False)

    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    tab_settings = tk.Frame(notebook)
    tab_scraper = tk.Frame(notebook)
    tab_waivers = tk.Frame(notebook)

    notebook.add(tab_settings, text='Settings')
    notebook.add(tab_scraper, text='Scrape Cases')
    notebook.add(tab_waivers, text='Generate Waivers')

    # Wrap the settings widgets in a sub-frame so we can cleanly reset
    settings_frame = tk.Frame(tab_settings)
    settings_frame.pack(fill='both', expand=True)

    def update_settings_tab():
        for widget in settings_frame.winfo_children():
            widget.destroy()

        tk.Label(settings_frame, text="Configuration Settings (read-only)", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=5)
        for key in sorted(CONFIG_KEYS):
            val = config.get(key, "")
            tk.Label(settings_frame, text=f"{key}: {val}", font=("Segoe UI", 10)).pack(anchor="w")
        tk.Label(settings_frame, text="\nTo edit settings, switch to the corresponding feature tab.", font=("Segoe UI", 9, "italic"), fg="gray").pack(anchor="w", pady=10)
        tk.Button(settings_frame, text="Refresh Settings", command=reload_config).pack(anchor="w", pady=5)
        tk.Button(settings_frame, text="Reset to Defaults", command=perform_reset).pack(anchor="w", pady=5)

    update_settings_tab()

    def change_bar_number():
        new_bar = simpledialog.askstring("Change Bar Number", "Enter new Bar Number:", parent=root)
        if new_bar:
            config["scraper.bar_number"] = new_bar
            config["scraper.destination_folder"] = os.path.join(os.path.expanduser("~"), "Desktop", f"{new_bar} Misdemeanor Clients")
            config["waiver.waiver_output_dir"] = os.path.join(os.path.expanduser("~"), "Desktop", f"{new_bar} Misdemeanor Waivers")
            save_config(config)
            reload_config()

    def change_dest_folder():
        folder = filedialog.askdirectory(title="Select base folder")
        if folder:
            config["scraper.destination_folder"] = folder
            save_config(config)
            reload_config()

    def run_scraper():
        btn_scrape.config(state='disabled')
        btn_continue.config(state='normal')
        def target():
            import scripts.scrape_cases as scrape_cases
            scrape_cases.run_main(continue_event)
        threading.Thread(target=target, daemon=True).start()

    def continue_scraping():
        print("\n[INFO] User clicked Continue\n")
        continue_event.set()

    tk.Button(tab_scraper, text="Change Bar Number", command=change_bar_number).pack(anchor="w", pady=5)
    tk.Button(tab_scraper, text="Change Destination Folder", command=change_dest_folder).pack(anchor="w", pady=5)
    tk.Button(tab_scraper, text="Open Folder", command=lambda: open_folder(config["scraper.destination_folder"])).pack(anchor="w", pady=5)
    btn_scrape = tk.Button(tab_scraper, text="Start Scraper", command=run_scraper)
    btn_scrape.pack(anchor="w", pady=5)
    btn_continue = tk.Button(tab_scraper, text="Continue (after captcha)", command=continue_scraping)
    btn_continue.pack(anchor="w", pady=5)
    btn_continue.config(state='disabled')

    def set_signature_image():
        img = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if img:
            config["waiver.signature_image_path"] = img
            save_config(config)
            reload_config()

    def set_waiver_output():
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            config["waiver.waiver_output_dir"] = folder
            save_config(config)
            reload_config()

    def run_waiver_generator():
        sig_path = config.get("waiver.signature_image_path")
        output_path = config.get("waiver.waiver_output_dir")
        if not os.path.exists(sig_path):
            messagebox.showerror("Error", f"Signature image not found:\n{sig_path}")
            return
        if not os.path.isdir(output_path):
            messagebox.showerror("Error", f"Waiver output folder not found:\n{output_path}")
            return
        btn_waiver_run.config(state='disabled')
        btn_waiver_continue.config(state='normal')
        def target():
            import scripts.create_waivers as create_waivers
            create_waivers.main(waiver_event)
        threading.Thread(target=target, daemon=True).start()

    def continue_waivers():
        print("\n[INFO] User clicked Continue (Waiver Captcha)\n")
        waiver_event.set()

    tk.Button(tab_waivers, text="Set Signature Image", command=set_signature_image).pack(anchor="w", pady=5)
    tk.Label(
        tab_waivers,
        text="💡 Recommended: Use a transparent .svg for your signature.\nConvert at https://www.pngtosvg.com/",
        font=("Segoe UI", 8, "italic"),
        fg="gray"
    ).pack(anchor="w", padx=5, pady=(0, 10))
    tk.Button(tab_waivers, text="Set Output Folder", command=set_waiver_output).pack(anchor="w", pady=5)
    tk.Button(tab_waivers, text="Open Output Folder", command=lambda: open_folder(config["waiver.waiver_output_dir"])).pack(anchor="w", pady=5)
    btn_waiver_run = tk.Button(tab_waivers, text="Run Waiver Generator", command=run_waiver_generator)
    btn_waiver_run.pack(anchor="w", pady=5)
    btn_waiver_continue = tk.Button(tab_waivers, text="Continue (after captcha)", command=continue_waivers)
    btn_waiver_continue.pack(anchor="w", pady=5)
    btn_waiver_continue.config(state='disabled')

    # === Shared Output Footer ===
    footer_frame = tk.Frame(root)
    footer_frame.pack(fill="x", pady=(10, 0))

    output_box = scrolledtext.ScrolledText(footer_frame, state='disabled', width=80, height=12, wrap='word')
    output_box.pack()
    sys.stdout = StdoutRedirector(output_box)
    sys.stderr = StdoutRedirector(output_box)

    continue_event = threading.Event()
    waiver_event = threading.Event()
    root.mainloop()

def main():
    ensure_config()
    run_gui()

if __name__ == "__main__":
    main()
