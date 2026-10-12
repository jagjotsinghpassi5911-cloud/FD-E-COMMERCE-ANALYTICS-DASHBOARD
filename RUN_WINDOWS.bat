@echo off
cd /d "%~dp0"
echo FD Analytics — Starting local offline demonstration
if not exist .env copy .env.example .env >nul
if not exist .venv (py -3 -m venv .venv || python -m venv .venv)
if not exist .venv\Scripts\python.exe (echo Python is missing. Install Python 3.11+ & retry. & pause & exit /b 1)
.venv\Scripts\python.exe -m pip install -r requirements.txt || (pause & exit /b 1)
.venv\Scripts\python.exe -c "from dotenv import load_dotenv;load_dotenv();from core.repository import get_repository;import sys;sys.exit(0 if get_repository().has_data() else 1)"
if errorlevel 1 .venv\Scripts\python.exe seed.py || (pause & exit /b 1)
.venv\Scripts\python.exe -m streamlit run app.py
pause
