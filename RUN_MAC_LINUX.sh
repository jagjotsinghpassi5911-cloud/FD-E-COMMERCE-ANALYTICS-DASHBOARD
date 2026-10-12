#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
test -f .env || cp .env.example .env
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -c 'from dotenv import load_dotenv;load_dotenv();from core.repository import get_repository;import sys;sys.exit(0 if get_repository().has_data() else 1)' || .venv/bin/python seed.py
.venv/bin/python -m streamlit run app.py
