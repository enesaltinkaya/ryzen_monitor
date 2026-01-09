# Ryzen Monitor Qt GUI

A modern Qt-based GUI for monitoring AMD Ryzen CPU statistics, replacing the terminal interface with a user-friendly graphical application.

## Features

- Real-time CPU core monitoring (frequency, power, voltage, temperature)
- Per-core C-state statistics (C0, C1, C6)
- Power limits monitoring (PPT, TDC, EDC)
- Temperature tracking
- Memory interface statistics (FCLK, MEMCLK, coupled mode)
- Power consumption breakdown
- Dark theme interface
- Auto-refresh (1 second interval)

## Architecture

This project consists of three components:

1. **libryzen_monitor.so** - Shared library wrapping the original C code
2. **ryzen_monitor_lib.h** - Header file with public API
3. **ryzen_monitor_gui.py** - Python Qt6 GUI application

## Requirements

### System Requirements
- AMD Ryzen processor
- Linux kernel with SMU support
- Root privileges (for SMU access)

### Software Requirements
- GCC compiler
- libsmu development files
- Python 3.7+
- PyQt6

## Installation

### 1. Prepare your environment

The project should already have the original ryzen_monitor files in the `src/` directory.

You need to add these new files:
- `src/ryzen_monitor_lib.c` (library wrapper)
- `src/ryzen_monitor_lib.h` (library header)
- `ryzen_monitor_gui.py` (Qt GUI - in project root)
- `build.sh` (build script - in project root)

And modify the root `Makefile` to support library building.

### 2. Build and install

```bash
# Build everything (original binary + library)
make all

# Install library (requires root)
sudo make install

# Install Python dependencies
make install-python
```

Or use the build script:

```bash
# Make it executable
chmod +x build.sh

# Build and install everything
sudo ./build.sh install

# Install Python dependencies
./build.sh python
```

### 3. Alternative: Manual compilation

If you prefer to compile manually:

```bash
# Build the original project first (builds required .o files)
make -C src

# Build the library
gcc -c -fPIC -O2 -I./src src/ryzen_monitor_lib.c -o src/ryzen_monitor_lib.o
gcc -shared -o libryzen_monitor.so src/ryzen_monitor_lib.o src/readinfo.o src/pm_tables.o -lsmu -lm

# Install
sudo install -m 755 libryzen_monitor.so /usr/local/lib/
sudo install -m 644 src/ryzen_monitor_lib.h /usr/local/include/
sudo ldconfig

# Install Python requirements
pip3 install PyQt6
```

## Usage

### Running the GUI

```bash
sudo python3 ryzen_monitor_gui.py
```

**Note:** Root privileges are required to access the SMU interface.

### Optional: Create a desktop launcher

Create `/usr/share/applications/ryzen-monitor.desktop`:

```ini
[Desktop Entry]
Name=Ryzen Monitor
Comment=Monitor AMD Ryzen CPU statistics
Exec=sudo python3 /path/to/ryzen_monitor_gui.py
Icon=utilities-system-monitor
Terminal=false
Type=Application
Categories=System;Monitor;
```

## Project Structure

```
.
├── Makefile                      # Combined build system (modified)
├── build.sh                      # Build script (new)
├── ryzen_monitor_gui.py          # Qt GUI application (new)
├── README.md                     # This file (new)
├── src/
│   ├── Makefile                  # Original src Makefile
│   ├── ryzen_monitor.c           # Original terminal app
│   ├── ryzen_monitor_lib.c       # Library wrapper (new)
│   ├── ryzen_monitor_lib.h       # Library header (new)
│   ├── readinfo.c                # From original project
│   ├── readinfo.h                # From original project
│   ├── pm_tables.c               # From original project
│   └── pm_tables.h               # From original project
└── libryzen_monitor.so           # Built library (generated)
```

## API Reference

The library exposes the following functions:

```c
int ryzen_init(void);
void ryzen_cleanup(void);
int ryzen_get_system_info(system_data_t *sysdata);
int ryzen_read_data(core_data_t *cores, int max_cores,
                    constraints_data_t *constraints,
                    memory_data_t *memory,
                    power_data_t *power);
```

See `ryzen_monitor_lib.h` for complete structure definitions.

## Troubleshooting

### "Failed to load libryzen_monitor.so"
- Ensure the library is in `/usr/local/lib/` or in your `LD_LIBRARY_PATH`
- Run `sudo ldconfig` after installation

### "Failed to initialize Ryzen Monitor"
- Make sure you're running as root: `sudo python3 ryzen_monitor_gui.py`
- Verify that your CPU is supported by the original ryzen_monitor
- Check that the ryzen_smu kernel module is loaded: `lsmod | grep ryzen`

### "This PM Table version is currently not supported"
- Your CPU's PM table version isn't in the library yet
- Check the original ryzen_monitor for updates
- The version can be found in the error message

### GUI doesn't update
- Check system logs: `journalctl -xe`
- Verify SMU access is working with the original terminal tool first

## Supported CPUs

The same CPUs supported by the original ryzen_monitor:
- Ryzen 3000 series (Zen 2)
- Ryzen 5000 series (Zen 3)
- Some Ryzen 4000 series APUs (Zen 2)
- Check pm_tables.c for the complete list of supported PM table versions

## Performance

- Library overhead: Minimal (simple C wrapper)
- GUI refresh rate: 1 second (configurable in code)
- Memory footprint: ~20-30 MB (mostly Qt)

## Credits

Based on the original [Ryzen SMU Userspace Sensor Monitor](https://gitlab.com/leogx9r/ryzen_smu) by:
- Florian Huehn (hattedsquirrel)
- Leonardo Gates (leogatesx9r)

Qt GUI wrapper by: [Your Name]

## License

GPL v3 (same as the original project)

## Contributing

Contributions welcome! Areas for improvement:
- Support for additional PM table versions
- Historical data graphing
- Export to CSV
- System tray integration
- Configurable refresh rates
- Additional visualizations