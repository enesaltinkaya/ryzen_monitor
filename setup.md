# Quick Setup Guide

This guide shows you how to integrate the Qt GUI into your existing ryzen_monitor project.

## Current Structure (What You Have)

```
ryzen_monitor/
├── Makefile              # Top-level makefile with SUBDIRS
├── src/
│   ├── Makefile          # Builds the terminal app
│   ├── ryzen_monitor.c   # Main terminal app
│   ├── readinfo.c/h      # System info functions
│   ├── pm_tables.c/h     # PM table definitions
│   └── libsmu.h          # SMU library header
└── (other files...)
```

## What to Add

### 1. New Files in `src/` Directory

Create these two files in your `src/` directory:

- **`src/ryzen_monitor_lib.c`** - The library wrapper (from artifact "ryzen_lib")
- **`src/ryzen_monitor_lib.h`** - The library header (from artifact "ryzen_header")

### 2. New Files in Project Root

Add these files to your project root directory:

- **`ryzen_monitor_gui.py`** - The Qt GUI application (from artifact "qt_gui")
- **`build.sh`** - Build helper script (from artifact "build_script")

### 3. Replace Root Makefile

Replace your root `Makefile` with the combined version (from artifact "makefile")

## Step-by-Step Integration

### Step 1: Add Library Files

```bash
cd /path/to/ryzen_monitor
cd src

# Create the library wrapper
nano ryzen_monitor_lib.c
# Paste content from the "ryzen_lib" artifact

# Create the library header
nano ryzen_monitor_lib.h
# Paste content from the "ryzen_header" artifact
```

### Step 2: Add GUI and Build Files

```bash
cd /path/to/ryzen_monitor

# Create the Python GUI
nano ryzen_monitor_gui.py
# Paste content from the "qt_gui" artifact

# Create build script
nano build.sh
# Paste content from the "build_script" artifact
chmod +x build.sh
```

### Step 3: Update Root Makefile

```bash
# Backup your current Makefile
cp Makefile Makefile.backup

# Replace with the combined version
nano Makefile
# Paste content from the "makefile" artifact
```

## Final Directory Structure

After adding all files:

```
ryzen_monitor/
├── Makefile                    # ← REPLACED (combined build system)
├── Makefile.backup             # ← Your original (backup)
├── build.sh                    # ← NEW (build helper)
├── ryzen_monitor_gui.py        # ← NEW (Qt GUI)
├── README.md                   # ← OPTIONAL (documentation)
├── src/
│   ├── Makefile                # ← UNCHANGED (original)
│   ├── ryzen_monitor.c         # ← UNCHANGED (original)
│   ├── ryzen_monitor_lib.c     # ← NEW (library wrapper)
│   ├── ryzen_monitor_lib.h     # ← NEW (library header)
│   ├── readinfo.c              # ← UNCHANGED (original)
│   ├── readinfo.h              # ← UNCHANGED (original)
│   ├── pm_tables.c             # ← UNCHANGED (original)
│   └── pm_tables.h             # ← UNCHANGED (original)
└── libryzen_monitor.so         # ← GENERATED (after build)
```

## Build and Run

### Quick Build (Using Build Script)

```bash
# Build everything
./build.sh all

# Install library
sudo ./build.sh install

# Install Python dependencies
./build.sh python

# Run the GUI
sudo python3 ryzen_monitor_gui.py
```

### Manual Build (Using Makefile)

```bash
# Build everything (terminal app + library)
make all

# Install library system-wide
sudo make install

# Install Python dependencies
make install-python

# Run the GUI
sudo python3 ryzen_monitor_gui.py
```

## Verify Installation

Check that everything built correctly:

```bash
# Check library is installed
ls -l /usr/local/lib/libryzen_monitor.so
ls -l /usr/local/include/ryzen_monitor_lib.h

# Check Python can import PyQt6
python3 -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')"

# Test the library loads
python3 -c "import ctypes; lib = ctypes.CDLL('/usr/local/lib/libryzen_monitor.so'); print('Library OK')"
```

## What Gets Built

1. **`src/ryzen_monitor`** - Original terminal application (still works!)
2. **`libryzen_monitor.so`** - Shared library for Qt GUI and other tools
3. **Qt GUI app** - Run with `sudo python3 ryzen_monitor_gui.py`

## Troubleshooting

### "Makefile:XX: *** missing separator"
Make sure you use **tabs** not spaces for indentation in Makefiles.

### "Cannot find -lsmu"
Install libsmu: `sudo apt-get install ryzen-smu-dkms` or build from source.

### Library not found when running GUI
Run `sudo ldconfig` after installation.

### Python ModuleNotFoundError: No module named 'PyQt6'
Install PyQt6: `pip3 install PyQt6` or `make install-python`

### Permission denied when running GUI
The GUI needs root to access SMU: `sudo python3 ryzen_monitor_gui.py`

## Original App Still Works!

The original terminal application is unchanged and still works:

```bash
cd src
sudo ./ryzen_monitor
```

## Need Help?

Check these files for more details:
- `README.md` - Full documentation
- `./build.sh help` - Build script options
- `make help` - Makefile targets