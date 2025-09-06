# ZZZ_Simulator

English | [中文](./docs/README_CN.md)

![zsim项目组](./docs/img/横板logo成图.png)

## Introduction

`ZSim` is a battle simulator and damage calculator for Zenless Zone Zero (An ACT game from Hoyoverse).

It is **fully automatically**, no need to manually set skill sequence (if sequence mode needed, let us know)

All you need to do is edit equipment of your agents, select a proper APL, then click run.

It provides a user-friendly interface to calculate the total damage output of a team composition, taking into account the characteristics of each character's weapon and equipment. Based on the preset APL (Action Priority List), it **automatically simulates** the actions in the team, triggers buffs, records and analyzes the results, and generates report in visual charts and tables.

## Features

- Calculate total damage based on team composition
- Generate visual charts
- Provide detailed damage information for each character
- Edit agents equipment
- Edit APL code

## Install

Download the latest source code in release page or use `git clone`

### Install UV (if you haven't already)

Open terminal anywhere in your device:

```bash
# Using pip if you have python installed:
pip install uv
```

```bash
# On macOS or Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
# On Windows11 24H2 or later:
winget install --id=astral-sh.uv  -e
```

```bash
# On lower version of Windows:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```



Or check the official installation guide: [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)

### Install and run ZZZ-Simulator

Open terminal in the directory of this project, then:

```bash
uv sync

uv run zsim run
```

## Development

### Key Components
1. **Simulation Engine** - Core logic in `zsim/simulator/` handles the battle simulation
2. **Web API** - FastAPI-based REST API in `zsim/api_src/` for programmatic access
3. **Web UI** - Streamlit-based interface in `zsim/webui.py` and new Vue.js + Electron desktop application in `electron-app/`
4. **CLI** - Command-line interface via `zsim/run.py`
5. **Database** - SQLite-based storage for character/enemy configurations
6. **Electron App** - Desktop application built with Vue.js and Electron that communicates with the FastAPI backend

### Build System

The project uses a comprehensive Make-based build system for managing development, building, and release processes.

#### Available Make Targets

```bash
# Build components
make build              # Full build (clean + backend + electron)
make backend            # Build backend API only
make electron-build     # Build Electron desktop application only

# Development
make dev                # Start frontend development server
make clean              # Clean all build files
make check              # Check dependencies

# Utilities
make help                # Display help information
```

### Setup and Installation
```bash
# Install UV package manager first
uv sync

# For WebUI develop
uv run zsim run 
# For FastAPI backend
uv run zsim api

# For Electron App development, also install Node.js dependencies
cd electron-app
pnpm install
```

### Running the Application

#### Quick Start (Recommended)
```bash
# One-click development server with both frontend and backend
cd electron-app
pnpm dev
```

#### Individual Components
```bash
# Streamlit WebUI
uv run zsim run

# FastAPI Backend
uv run zsim api

# Electron Desktop App (production build)
cd electron-app
pnpm build
```

**Note**: The `pnpm dev` command provides the most convenient development experience by:
- Automatically starting both the Vue.js frontend and FastAPI backend
- Forwarding all backend console output to the development terminal
- Providing hot reload for the frontend
- Enabling full debugging capabilities

### Testing Structure
- Unit tests in `tests/` directory
- API tests in `tests/api/`
- Fixtures defined in `tests/conftest.py`
- Uses pytest with asyncio support

```bash
# Run the tests
uv run pytest
# Run the tests with coverage report
uv run pytest -v --cov=zsim --cov-report=html
```

## TODO LIST

Go check [develop guide](https://github.com/ZZZSimulator/ZSim/wiki/%E8%B4%A1%E7%8C%AE%E6%8C%87%E5%8D%97-Develop-Guide) for more details.

## Environment Variables

### FastAPI Backend
- `ZSIM_DISABLE_ROUTES` - Set to "1" to disable API routes (default: enabled)
- `ZSIM_IPC_MODE` - IPC communication mode: "auto", "uds", or "http" (default: "auto")
- `ZSIM_UDS_PATH` - UDS socket file path when using UDS mode (default: "/tmp/zsim_api.sock")
- `ZSIM_API_PORT` - API server port, set to 0 for automatic port selection (default: 0)
- `ZSIM_API_HOST` - API server host address (default: "127.0.0.1")

### IPC Mode Behavior
- **auto**: Uses uds on Unix like OS, and http on windows
- **uds**: Uses Unix Domain Socket for local communication (Unix like only)
- **http**: Uses HTTP/TCP for communication (default mode)
