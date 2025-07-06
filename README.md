# ZZZ_Simulator

English | [中文](./docs/README_CN.md)

![zsim](./docs/img/zsim成图.svg)

![zsim项目组](./docs/img/横板logo成图.png)

## Introduction

`ZZZ_Calculator` is a damage calculator for Zenless Zone Zero.

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

```bash
# Using pip:
pip install uv
```

Or check the official installation guide: [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)

### Install ZZZ-Simulator

Open terminal in the directory of this project, then:

```bash
uv venv
uv pip install .  # there is a '.' refer to relative path
```

## Run

Open terminal anywhere in your device:

```bash
zsim run
```

If you don't want to install `ZZZ-Simulator`, you can also run it directly:

```bash
uv run ./zsim/run.py run
```

```bash
# or also:
uv run zsim run
```

## TODO LIST

Go check [develop guide](https://github.com/ZZZSimulator/ZSim/wiki/%E8%B4%A1%E7%8C%AE%E6%8C%87%E5%8D%97-Develop-Guide) for more details.
