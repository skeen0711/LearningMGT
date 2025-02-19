#!/bin/bash

# Define the main directory
MAIN_DIR="/Users/user/PycharmProjects/LearningMGT"

# Check if the main directory exists
if [ ! -d "$MAIN_DIR" ]; then
    echo "Directory $MAIN_DIR does not exist. Please ensure you are in the correct location."
    exit 1
fi

# Create subdirectories
mkdir -p "$MAIN_DIR/app/routes"
mkdir -p "$MAIN_DIR/tests"

# Create empty __init__.py files for Python packages
touch "$MAIN_DIR/app/__init__.py"
touch "$MAIN_DIR/app/routes/__init__.py"

# Create new Python files
touch "$MAIN_DIR/app/models.py"
touch "$MAIN_DIR/app/schemas.py"
touch "$MAIN_DIR/app/crud.py"
touch "$MAIN_DIR/app/routes/users.py"
touch "$MAIN_DIR/app/routes/courses.py"
touch "$MAIN_DIR/database.py"
touch "$MAIN_DIR/config.py"
touch "$MAIN_DIR/tests/test_main.py"

# Create requirements.txt
echo "fastapi==0.85.0
uvicorn==0.18.3
sqlalchemy==1.4.39
pydantic==1.9.1" > "$MAIN_DIR/requirements.txt"

# Create README.md
echo "# Learning Management System for Lumber Company

This is a learning management system built with FastAPI, tailored for a lumber company." > "$MAIN_DIR/README.md"

# Modify main.py to reflect the new structure
echo "from fastapi import FastAPI
from app.routes import users, courses

app = FastAPI()

app.include_router(users.router)
app.include_router(courses.router)

@app.get('/')
async def root():
    return {'message': 'Welcome to Lumber LMS'}
" > "$MAIN_DIR/main.py"

echo "File structure setup completed!"
