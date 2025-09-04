# -*- mode: python ; coding: utf-8 -*-

"""
ZSim API PyInstaller 配置文件
用于将 zsim/api.py 打包为独立的可执行文件
"""

import os
from pathlib import Path
import toml

# 获取项目根目录
project_root = Path(os.getcwd())

# 基础配置
block_cipher = None

# 数据文件配置
datas = []
binaries = []

# 添加数据目录
data_dir = project_root / "zsim" / "data"
if data_dir.exists():
    datas.append((str(data_dir), "zsim/data"))
    print(f"添加数据目录: {data_dir} -> zsim/data")

# 添加配置文件
config_file = project_root / "zsim" / "config_example.json"
if config_file.exists():
    datas.append((str(config_file), "zsim/config_example.json"))
    print(f"添加配置文件: {config_file} -> zsim/config_example.json")

# 添加其他必要的配置文件
config_json = project_root / "zsim" / "config.json"
if config_json.exists():
    datas.append((str(config_json), "zsim/config.json"))
    print(f"添加配置文件: {config_json} -> zsim/config.json")

# 添加buff配置文件
buff_config_json = project_root / "zsim" / "sim_progress" / "Buff" / "buff_config.json"
if buff_config_json.exists():
    datas.append((str(buff_config_json), "zsim/sim_progress/Buff/buff_config.json"))
    print(f"添加配置文件: {buff_config_json} -> zsim/sim_progress/Buff/buff_config.json")

# 隐藏导入（防止PyInstaller无法自动检测）
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

# 排除的模块
excludes = [
    "tkinter",
    "unittest",
    "ipykernel",
    "pytest",
    "matplotlib",
    "jupyter",
    "streamlit",
]

# 分析配置
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

# 打包配置
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 可执行文件配置
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='zsim_api',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 创建目录结构的打包
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

# 在打包时动态创建版本文件
import shutil
import os
import tempfile

# 读取版本号
def get_version():
    try:
        with open("pyproject.toml", "r", encoding="utf-8") as f:
            pyproject_config = toml.load(f)
            return pyproject_config.get("project", {}).get("version", "0.0.0")
    except FileNotFoundError:
        return "1.0.0"

# 创建临时define.py文件，注入版本号
version_str = get_version()
with open("zsim/define.py", "r", encoding="utf-8") as f:
    define_content = f.read()

# 替换版本号行
define_content = define_content.replace(
    '__version__ = "1.0.0"  # 默认值，打包时会被替换',
    f'__version__ = "{version_str}"  # 打包时注入的版本号'
)

# 写入临时文件
temp_define_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
temp_define_file.write(define_content)
temp_define_file.close()

# 添加修改后的define.py文件
datas.append((temp_define_file.name, "zsim/define.py"))

# 手动复制数据文件到根目录
dist_path = os.path.join("dist", "zsim_api")

# 复制zsim目录中的配置文件
import glob

zsim_dir = project_root / "zsim"
if zsim_dir.exists():
    # 确保目标目录存在
    target_zsim_dir = os.path.join(dist_path, "zsim")
    os.makedirs(target_zsim_dir, exist_ok=True)
    
    # 复制所有.json, .toml, .md, .csv文件
    for ext in ["*.json", "*.toml", "*.md", "*.csv"]:
        for file_path in zsim_dir.rglob(ext):
            # 计算相对路径
            rel_path = file_path.relative_to(zsim_dir)
            target_path = os.path.join(target_zsim_dir, rel_path)
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # 复制文件
            shutil.copy2(str(file_path), target_path)
            print(f"复制配置文件: {file_path} -> {target_path}")