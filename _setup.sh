#!/bin/bash
# Agentic AI Research Solution - Setup Script (Unix/Linux/Mac)
# This script sets up the environment for first-time use

echo "============================================================"
echo "Agentic AI Research Solution - Setup"
echo "============================================================"
echo ""

echo "[1/4] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.11 or higher"
    exit 1
fi
python3 --version
echo ""

echo "[2/4] Creating virtual environment..."
cd backend
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping creation"
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
    echo "Virtual environment created successfully"
fi
echo ""

echo "[3/4] Activating virtual environment and installing dependencies..."
source venv/bin/activate
echo "Installing Python packages (this may take a few minutes)..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    deactivate
    exit 1
fi
echo "Dependencies installed successfully"
deactivate
cd ..
echo ""

echo "[4/4] Setting up configuration..."
if [ -f ".env" ]; then
    echo ".env file already exists, skipping"
else
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Please edit .env and add your API keys!"
    echo "At minimum, you need ONE of the following:"
    echo "  - OPENAI_API_KEY"
    echo "  - GOOGLE_API_KEY"
    echo "  - OPENROUTER_API_KEY"
    echo ""
fi

echo ""
echo "============================================================"
echo "Setup completed successfully!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Run ./start.sh to begin research (you may need to: chmod +x start.sh)"
echo ""
