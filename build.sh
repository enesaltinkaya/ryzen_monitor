#!/bin/bash

# Build script for Ryzen Monitor Library and Qt GUI
# Works with the existing project structure

set -e

echo "=== Ryzen Monitor Build Script ==="
echo ""

# Check if running as root for installation
if [ "$1" == "install" ] && [ "$EUID" -ne 0 ]; then
    echo "Installation requires root privileges"
    echo "Usage: sudo ./build.sh install"
    exit 1
fi

# Detect project structure
if [ ! -f "Makefile" ]; then
    echo "Error: Makefile not found. Run this script from project root."
    exit 1
fi

# Check if library source files exist
if [ ! -f "src/ryzen_monitor_lib.c" ]; then
    echo "Warning: src/ryzen_monitor_lib.c not found"
    echo "Please place the library wrapper files in src/ directory:"
    echo "  - src/ryzen_monitor_lib.c"
    echo "  - src/ryzen_monitor_lib.h"
    exit 1
fi

# Parse command line arguments
COMMAND=${1:-"all"}

case "$COMMAND" in
    "all")
        echo "Building original binary and library..."
        make all
        echo ""
        echo "=== Build complete ==="
        echo "Original binary: src/ryzen_monitor"
        echo "Library: libryzen_monitor.so"
        ;;
    
    "lib"|"library")
        echo "Building library only..."
        make library
        echo ""
        echo "=== Library built ==="
        echo "File: libryzen_monitor.so"
        ;;
    
    "install")
        echo "Building and installing..."
        make all
        echo ""
        make install
        echo ""
        echo "=== Installation complete ==="
        echo ""
        echo "Next steps:"
        echo "1. Install Python dependencies:"
        echo "   make install-python"
        echo "   (or: pip3 install PyQt6)"
        echo ""
        echo "2. Run the GUI:"
        echo "   sudo python3 ryzen_monitor_gui.py"
        ;;
    
    "python")
        echo "Installing Python dependencies..."
        make install-python
        ;;
    
    "clean")
        echo "Cleaning build files..."
        make clean
        echo "=== Clean complete ==="
        ;;
    
    "uninstall")
        if [ "$EUID" -ne 0 ]; then
            echo "Uninstall requires root privileges"
            echo "Usage: sudo ./build.sh uninstall"
            exit 1
        fi
        echo "Uninstalling library..."
        make uninstall
        echo "=== Uninstall complete ==="
        ;;
    
    "help"|"-h"|"--help")
        echo "Ryzen Monitor Build Script"
        echo ""
        echo "Usage: ./build.sh [command]"
        echo ""
        echo "Commands:"
        echo "  all        - Build everything (default)"
        echo "  library    - Build only the shared library"
        echo "  install    - Build and install (requires sudo)"
        echo "  python     - Install Python dependencies"
        echo "  clean      - Clean build files"
        echo "  uninstall  - Remove installed library (requires sudo)"
        echo "  help       - Show this help"
        echo ""
        echo "Examples:"
        echo "  ./build.sh                # Build everything"
        echo "  sudo ./build.sh install   # Build and install"
        echo "  ./build.sh python         # Setup Python"
        echo "  ./build.sh clean          # Clean up"
        echo ""
        echo "After installation, run the GUI with:"
        echo "  sudo python3 ryzen_monitor_gui.py"
        ;;
    
    *)
        echo "Error: Unknown command '$COMMAND'"
        echo "Run './build.sh help' for usage information"
        exit 1
        ;;
esac