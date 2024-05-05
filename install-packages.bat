@echo off
setlocal enabledelayedexpansion

REM Set the venv directory
set VENV_DIR=.venv

REM Upgrade dependencies in the virtual environment
python -m venv --upgrade-deps !VENV_DIR!

REM Activate the virtual environment and install/uprade packages
call !VENV_DIR!\Scripts\activate
python -m pip install -U --disable-pip-version-check --editable .[non-termux]