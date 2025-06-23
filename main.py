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

def check_license(bar_number, password):
    try:
        # TODO: Replace this dummy check with API request
        if not (bar_number == "20789" and password):
            raise Exception("Invalid login or expired license")
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
    from tkinter import filedialog

    root = tk.Tk()
    root.title("Initial Configuration")
    root.geometry("400x200")
    root.eval('tk::PlaceWindow . center')

    root.update()

    # Move bar_number prompt before folder selection
    if not config.get("bar_number"):
        bar_number = simpledialog.askstring("Login", "Enter your Docket ID (Bar Number):", parent=root)
        if bar_number:
            config["bar_number"] = bar_number
    
    if not config.get("password"):
        password = simpledialog.askstring("Login", "Enter your password:", show='*', parent=root)
        if password:
            config["password"] = password

    remember = messagebox.askyesno("Remember Login?", "Save login credentials on this device?", parent=root)
    config["remember_credentials"] = remember
    if not remember:
        config.pop("bar_number", None)
        config.pop("password", None)


    if not config.get("destination_folder"):
        messagebox.showinfo("Folder Selection",
                            "Choose a base directory. A folder named '[BAR_NUMBER] Misdemeanor Clients' will be created inside it, and the spreadsheet and case files/folders will be saved there.",
                            parent=root)
        base_folder = filedialog.askdirectory(title="Select base directory", parent=root)
        if base_folder and config.get("bar_number"):
            final_folder = os.path.join(base_folder, f"{config['bar_number']} Misdemeanor Clients")
            os.makedirs(final_folder, exist_ok=True)
            config["destination_folder"] = final_folder

    with open(resource_path("config.json"), "w") as f:
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

    if not config.get("destination_folder") or not config.get("bar_number"):
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

    continue_event = threading.Event()

    def run_script():
        try:
            btn_run.config(state='disabled')  # disable Run button
            btn_continue.config(state='normal')  # enable Continue button

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

    btn_run = tk.Button(root, text="Run Now", width=20, command=run_script)
    btn_run.pack(pady=5)

    btn_continue = tk.Button(root, text="Continue (after captcha)", width=30, command=continue_scrape)
    btn_continue.pack(pady=5)
    btn_continue.config(state='disabled')

    root.mainloop()

# === CLI Handler ===
def run_scraper():
    from scraper_core import run_main
    run_main()

# === MAIN ENTRY ===
def main():
    config_path = resource_path("config.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except:
        config = {}

    if not config.get("destination_folder") or not config.get("bar_number"):
        prompt_for_config(config)

    bar_number = config.get("bar_number")
    password = config.get("password", "")
    check_license(bar_number, password)

    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        run_scraper()
    else:
        run_gui()


if __name__ == "__main__":
    main()
