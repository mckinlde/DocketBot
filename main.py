import tkinter as tk
from tkinter import messagebox, scrolledtext
import sys
import os
import json
import threading

# === LICENSE CHECK ===
def get_stored_license_key():
    try:
        with open(resource_path("config.json")) as f:
            config = json.load(f)
        return config.get("bar_number", "")
    except Exception:
        return ""

def check_license():
    try:
        license_key = get_stored_license_key()
        # Simulated license check — replace with real server call if needed
        if license_key != "20789":  # replace with your validation logic
            raise Exception("License invalid or expired")
    except Exception as e:
        print("License check failed:", e)
        sys.exit(1)

# === Utility for PyInstaller pathing ===
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# === Redirect print to GUI text box ===
class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, s):
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, s)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state='disabled')

    def flush(self):
        pass  # For compatibility with file-like object

# === Initial User Config ===
def prompt_for_config(config):
    import tkinter.simpledialog as simpledialog

    root = tk.Tk()
    root.withdraw()  # hide main window

    if not config.get("base_path"):
        base_path = simpledialog.askstring("Setup", "Enter base path for your Cases folder:")
        if base_path:
            config["base_path"] = base_path

    if not config.get("shared_root"):
        shared_root = simpledialog.askstring("Setup", "Enter shared root folder path:")
        if shared_root:
            config["shared_root"] = shared_root

    if not config.get("base_path") or not config.get("shared_root"):
        messagebox.showerror("Error", "Configuration incomplete. Please restart and provide all paths.")
        sys.exit(1)

    # Save updated config.json
    config_path = resource_path("config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    root.destroy()

# === GUI Function ===
def run_gui():
    config_path = resource_path("config.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        messagebox.showerror("Error", f"Could not load config.json: {e}")
        sys.exit(1)

    if not config.get("base_path") or not config.get("shared_root"):
        prompt_for_config(config)
        # Reload updated config
        with open(resource_path("config.json"), "r") as f:
            config = json.load(f)

    bar_number = config.get("bar_number")

    root = tk.Tk()
    root.title("DocketBot")

    label = tk.Label(root, text=f"Run scraper for Bar #{bar_number}?")
    label.pack(pady=10)

    output_box = scrolledtext.ScrolledText(root, state='disabled', width=80, height=20, wrap='word')
    output_box.pack(padx=10, pady=10)

    # Redirect print output to text box
    sys.stdout = StdoutRedirector(output_box)
    sys.stderr = StdoutRedirector(output_box)

    def run_script():
        try:
            btn_run.config(state='disabled')  # disable Run button

            def target():
                try:
                    from scraper_core import run_main
                    run_main()
                finally:
                    # Re-enable button when done (in main thread)
                    root.after(0, lambda: btn_run.config(state='normal'))

            threading.Thread(target=target, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to run scraper: {e}")
            btn_run.config(state='normal')

    btn_run = tk.Button(root, text="Run Now", width=20, command=run_script)
    btn_run.pack(pady=5)

    root.mainloop()

# === CLI Handler ===
def run_scraper():
    from scraper_core import run_main
    run_main()

# === MAIN ENTRY ===
def main():
    check_license()
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        run_scraper()
    else:
        run_gui()

if __name__ == "__main__":
    main()
