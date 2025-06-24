# DocketBot.spec — Onefile Build
# Run with: pyinstaller DocketBot.spec

from PyInstaller.utils.hooks import collect_submodules, collect_dynamic_libs, collect_data_files
import os

# === Paths ===
project_path = os.path.abspath(".")
config_path = os.path.join(project_path, "config.json")

# === lxml dynamic assets ===
lxml_binaries = collect_dynamic_libs('lxml')
lxml_datas = collect_data_files('lxml')

# === Data and Binaries ===
datas = [
    ('chrome-win64/*', 'chrome-win64'),
    ('chromedriver-win64/*', 'chromedriver-win64'),
    (config_path, '.'),
] + lxml_datas

binaries = lxml_binaries
hiddenimports = collect_submodules('bs4') + collect_submodules('selenium')

# === Build ===
a = Analysis(
    ['main.py'],
    pathex=[project_path],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='DocketBot',
    icon='assets/DocketBot.ico',
    debug=False,
    strip=False,
    upx=True,
    console=False,  # Set to True if you want to see stdout in a terminal
    onefile=False,
    distpath='dist'
)
