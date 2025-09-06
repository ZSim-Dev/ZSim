# -*- mode: python ; coding: utf-8 -*-

"""
ZSim API PyInstaller configuration file
Used to package zsim/api.py into a standalone executable

Supports both current platform builds and cross-compilation:
- Current platform: uv run pyinstaller zsim_api.spec
- Cross-platform: TARGET_PLATFORM=windows/linux/macos uv run pyinstaller zsim_api.spec
"""

import os
import platform
from pathlib import Path
import toml

# Get target platform from environment variable or detect current platform
TARGET_PLATFORM = os.environ.get('TARGET_PLATFORM', platform.system().lower())
if TARGET_PLATFORM == 'darwin':
    TARGET_PLATFORM = 'macos'

print(f"Building for target platform: {TARGET_PLATFORM}")

# Get project root directory
project_root = Path(os.getcwd())

# Basic configuration
block_cipher = None

# Data file configuration
datas = []
binaries = []

# Add data directory
data_dir = project_root / "zsim" / "data"
if data_dir.exists():
    datas.append((str(data_dir), "zsim/data"))
    print(f"Added data directory: {data_dir} -> zsim/data")

# Add configuration file
config_file = project_root / "zsim" / "config_example.json"
if config_file.exists():
    datas.append((str(config_file), "zsim/config_example.json"))
    print(f"Added configuration file: {config_file} -> zsim/config_example.json")

# Add other necessary configuration files
config_json = project_root / "zsim" / "config.json"
if config_json.exists():
    datas.append((str(config_json), "zsim/config.json"))
    print(f"Added configuration file: {config_json} -> zsim/config.json")

# Add buff configuration file
buff_config_json = project_root / "zsim" / "sim_progress" / "Buff" / "buff_config.json"
if buff_config_json.exists():
    datas.append((str(buff_config_json), "zsim/sim_progress/Buff/buff_config.json"))
    print(f"Added configuration file: {buff_config_json} -> zsim/sim_progress/Buff/buff_config.json")

# Hidden imports (to prevent PyInstaller from failing to detect automatically)
hiddenimports = [
    "pandas",
    "tqdm",
    "numpy",
    "dash",
    "setuptools",
    "toml",
    "aiofiles",
    "pydantic",
    "psutil",
    "streamlit_ace",
    "polars",
    "pywebview",
    "fastapi",
    "uvicorn",
    "aiosqlite",
    "httpx",
    "zsim",
    "plotly",
]

# Excluded modules
excludes = [
    "tkinter",
    "unittest",
    "ipykernel",
    "pytest",
    "matplotlib",
    "jupyter",
    "streamlit",
    "viztracer",
]

# Analysis configuration
a = Analysis(
    ['zsim/api.py'],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Packaging configuration
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Platform-specific executable configuration
exe_kwargs = {
    'pyz': pyz,
    'a.scripts': a.scripts,
    'exclude_binaries': True,
    'name': 'zsim_api',
    'debug': False,
    'bootloader_ignore_signals': False,
    'strip': False,
    'upx': True,
    'upx_exclude': [],
    'runtime_tmpdir': None,
    'console': True,
    'disable_windowed_traceback': False,
    'argv_emulation': False,
    'target_arch': None,
    'codesign_identity': None,
    'entitlements_file': None,
}

# Platform-specific adjustments
if TARGET_PLATFORM == 'windows':
    exe_kwargs.update({
        'win_no_prefer_redirects': False,
        'win_private_assemblies': False,
    })
elif TARGET_PLATFORM == 'macos':
    exe_kwargs.update({
        'argv_emulation': False,
    })
elif TARGET_PLATFORM == 'linux':
    pass  # Linux uses default settings

exe = EXE(**exe_kwargs)

# Create collection with directory structure
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='zsim_api',
)

# Dynamically create version file during packaging
import shutil
import os
import tempfile

# Read version number
def get_version():
    try:
        with open("pyproject.toml", "r", encoding="utf-8") as f:
            pyproject_config = toml.load(f)
            return pyproject_config.get("project", {}).get("version", "0.0.0")
    except FileNotFoundError:
        return "1.0.0"

# Create temporary define.py file and inject version number
version_str = get_version()
with open("zsim/define.py", "r", encoding="utf-8") as f:
    define_content = f.read()

# Replace version line
define_content = define_content.replace(
    '__version__ = "1.0.0"  # Default value, will be replaced during packaging',
    f'__version__ = "{version_str}"  # Version injected during packaging'
)

# Write to temporary file
temp_define_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
temp_define_file.write(define_content)
temp_define_file.close()

# Add modified define.py file
datas.append((temp_define_file.name, "zsim/define.py"))

# Manually copy data files to root directory
dist_path = os.path.join("dist", "zsim_api")

import glob

zsim_dir = project_root / "zsim"
if zsim_dir.exists():
    # Ensure target directory exists
    target_zsim_dir = os.path.join(dist_path, "zsim")
    os.makedirs(target_zsim_dir, exist_ok=True)
    
    # Copy all .json, .toml, .md, .csv files
    for ext in ["*.json", "*.toml", "*.md", "*.csv"]:
        for file_path in zsim_dir.rglob(ext):
            # Calculate relative path
            rel_path = file_path.relative_to(zsim_dir)
            target_path = os.path.join(target_zsim_dir, rel_path)
            
            # Ensure target directory exists
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # Copy file
            shutil.copy2(str(file_path), target_path)
            print(f"Copied configuration file: {file_path} -> {target_path}")

print(f"✅ Successfully configured build for {TARGET_PLATFORM}")
print(f"📦 Executable will be created in: dist/zsim_api/")