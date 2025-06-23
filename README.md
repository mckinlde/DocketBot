Here’s a `README.md` tailored for your **DocketBot** project in its current state, with appropriate placeholders, usage instructions, and notes based on what you've shared so far:

---

````markdown
# DocketBot

DocketBot is a lightweight desktop application for downloading, organizing, and viewing Washington State court documents. Designed for attorneys and legal researchers, it provides an intuitive GUI interface, secure login workflow, and persistent folder structure to save cases by attorney and docket ID.

---

## 🚀 Features

- 🧠 **Smart Folder Structure**  
  Organizes downloaded cases by Attorney (`Doug` or `Stacey`) and Docket ID under a user-defined root directory.

- 🔒 **User Login with License Validation**  
  Secure login flow with stubbed cloud-based license validation.

- 📂 **Case Downloading & Parsing**  
  Scrapes and saves HTML content for case dockets; parses fields using BeautifulSoup.

- 🖥️ **Simple GUI Interface**  
  A standalone desktop GUI with redirected output for easy feedback and error tracking.

- 💾 **Persistent Configuration**  
  Saves selected download paths and optional credentials across sessions.

---

## 🛠️ Setup

### 1. Clone the Repo
```bash
git clone https://github.com/mckinlde/DocketBot.git
cd DocketBot
````

### 2. Create Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the App

```bash
python main.py
```

Or run the built executable (if built via PyInstaller):

```bash
dist\DocketBot\DocketBot.exe
```

---

## ⚙️ Build Instructions

To build the standalone `.exe` file:

```bash
pyinstaller DocketBot.spec
```

> **Note**: If you get a `PermissionError`, ensure the app is not already running or that no files in `dist/DocketBot` are open or locked by another process.

---

## 🧪 Useful Code Snippets

### Clear stdout inside GUI

```python
sys.stdout = StdoutRedirector(text_widget)
```

### Auto-create folder structure

```python
os.makedirs(os.path.join(root_dir, attorney, docket_id), exist_ok=True)
```

### Config file format (`config.ini`)

```ini
[credentials]
docket_id = example123
password = secret
save_credentials = True

[paths]
root_directory = C:/Users/.../CourtDocs
```

---

## ❗ Known Issues

* `chrome.dll` lock may cause PyInstaller to fail; ensure all Chrome-related processes are closed.
* `pytest` warning on `bs4.tests` is harmless unless testing support is required.
* Pushing to GitHub with SSH may fail unless your key is configured; HTTPS is recommended unless you're using a credential helper.

---

## 📌 TODO (future features)

* [ ] Validate license against real cloud API
* [ ] Enable login credentials saving and auto-fill securely
* [ ] Progress bar or status messages in GUI
* [ ] Add retry logic and error handling for failed downloads
* [ ] Portable app bundle with ChromeDriver + headless Chromium
* [ ] Expand support for multiple attorneys or filters
* [ ] Add "Open Case Folder" button in GUI

---

## 👤 Author

**Douglas McKinley**
Email: [douglas.e.mckinley@gmail.com](mailto:douglas.e.mckinley@gmail.com)
GitHub: [@mckinlde](https://github.com/mckinlde)

---

## 📝 License


```

---
# DocketBot LICENSE

## 1. Confidentiality and Access Control

This software ("DocketBot") is proprietary and confidential. No person, entity, artificial intelligence, or being of any form, in any known or hypothetical universe, may:

- Know of the existence of this software,
- View any portion of its source code,
- Execute, run, or compile it,
- Derive or infer its functionality or purpose,
- Mention or reference it to any third party,

**without the explicit, prior, written consent of Douglas McKinley and payment of a license fee set solely at his discretion.**

## 2. Use Restrictions

The software may not be:

- Copied, modified, merged, published, distributed, sublicensed, or sold,
- Hosted or executed in any cloud or local environment,
- Reverse engineered, decompiled, or disassembled,
- Used for research, training, auditing, or education,

under any circumstances without a signed and notarized license agreement and proof of full payment.

## 3. Liability Disclaimer

By receiving or becoming aware of this software (intentionally or otherwise), you irrevocably agree to the following:

- **Douglas McKinley accepts zero liability**—civil, criminal, cosmic, karmic, or metaphysical—for any damages, losses, or outcomes related to or arising from the software's presence, execution, absence, or implications.
- This includes but is not limited to: data loss, financial damage, professional malpractice, software instability, psychological distress, reputational harm, dimensional warping, or timeline disruption.
- This limitation applies regardless of jurisdiction, whether or not Douglas McKinley has been advised of the possibility of such damages, and even in cases of gross negligence or / and intentional malfeasance.

## 4. Enforcement

Violation of this license grants Douglas McKinley the unlimited and unilateral right to pursue:

- Monetary compensation,
- Public shaming,
- Legal action in any venue of his choosing,
- Or the invocation of any natural, unnatural, or supernatural remedy deemed proportionate, unproportionate, cruel, or unusual.

---

© Douglas McKinley. All rights reserved. All rights not explicitly granted are permanently and completely withheld. Fuck you pay me.

```
