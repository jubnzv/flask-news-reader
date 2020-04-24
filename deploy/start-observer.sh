#!/usr/bin/env bash
set -eoxu pipefail
python3 /app/deploy/setup_dependencies.py
cd /app
rm -rf /app/migrations/versions/*
alembic revision --autogenerate -m 'Init'
alembic upgrade head
python3 /app/main.py --observer=1
