#!/bin/bash

# Create tables from models
echo "Initialising database tables..."
export PYTHONPATH=$PYTHONPATH:.
python -m backend.db.init_db

# Start application
echo "Starting FastAPI server..."
exec uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
