#!/bin/bash
# Agentic AI Research Solution - Start Script (Unix/Linux/Mac)
# This script starts the research system

echo "============================================================"
echo "Agentic AI Research Solution - Starting..."
echo "============================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run: cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    echo ""
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found!"
    echo "Please copy .env.example to .env and configure your API keys"
    echo ""
    exit 1
fi

# Activate virtual environment and run
echo "Activating virtual environment..."
cd backend
source venv/bin/activate

echo ""
echo "Starting research system..."
echo ""
python main.py

# Deactivate when done
deactivate
cd ..

echo ""
echo "============================================================"
echo "Research session completed"
echo "============================================================"
