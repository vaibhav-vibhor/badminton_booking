#!/bin/bash
# Quick launcher for Badminton Slot Checker
# This script makes it easy to run the checker on Linux/Mac

echo ""
echo "🏸 Badminton Slot Checker Launcher"
echo "======================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    echo "Please install Python 3.7+ from your package manager"
    exit 1
fi

# Check if we're in the right directory
if [[ ! -f "src/main.py" ]]; then
    echo "❌ main.py not found. Please run this from the project root directory."
    exit 1
fi

# Install dependencies if needed
if [[ ! -d ".venv" ]]; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
    if [[ $? -ne 0 ]]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

# Show menu
echo ""
echo "Choose an option:"
echo "1. Run setup (first time)"
echo "2. Test configuration"
echo "3. Check slots once"
echo "4. Start continuous monitoring"
echo "5. Exit"
echo ""
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🔧 Running setup..."
        python3 setup.py
        read -p "Press Enter to continue..."
        ;;
    2)
        echo ""
        echo "🧪 Testing configuration..."
        cd src
        python3 main.py --mode test
        cd ..
        read -p "Press Enter to continue..."
        ;;
    3)
        echo ""
        echo "🔍 Checking slots once..."
        cd src
        python3 main.py --mode single
        cd ..
        read -p "Press Enter to continue..."
        ;;
    4)
        echo ""
        echo "🔄 Starting continuous monitoring..."
        echo "Press Ctrl+C to stop"
        cd src
        python3 main.py --mode continuous
        cd ..
        read -p "Press Enter to continue..."
        ;;
    5)
        echo ""
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo ""
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "Press Enter to exit..."
read
