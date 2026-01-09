# Combined Makefile for Ryzen Monitor
# Builds both original binary and new shared library

# Top-level targets
TOPTARGETS := all clean install

# Original subdirectories (builds the terminal app)
SUBDIRS := src

# Library build configuration
CC = gcc
CFLAGS = -Wall -fPIC -O2
LDFLAGS = -shared
LIBS = -lm

# Library files
LIB_TARGET = libryzen_monitor.so

# ALL sources needed for the library (including the ones from src/)
LIB_SOURCES = src/ryzen_monitor_lib.c \
              src/lib/libsmu.c \
              src/readinfo.c \
              src/pm_tables.c

# Create distinct object filenames (.pic.o) so we don't mix them up 
# with the non-PIC objects created by the original src/Makefile
LIB_OBJECTS = $(LIB_SOURCES:.c=.pic.o)
LIB_HEADER = src/ryzen_monitor_lib.h

# Include path
INCLUDES = -I./src

# Default target - build everything
all: library $(SUBDIRS)

# Build subdirectories (original project)
$(SUBDIRS):
	$(MAKE) -C $@ $(filter-out library install-lib install-python,$(MAKECMDGOALS))

# Pattern rule for Library Objects (compiles with -fPIC)
# We output to .pic.o to avoid conflict with src/Makefile's .o files
%.pic.o: %.c $(LIB_HEADER)
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

# Build the shared library
library: $(LIB_OBJECTS)
	@echo "Linking shared library..."
	$(CC) $(LDFLAGS) -o $(LIB_TARGET) $(LIB_OBJECTS) $(LIBS)
	@echo "Library built successfully: $(LIB_TARGET)"

# Install everything
install: all
	@echo "Installing library..."
	install -m 755 $(LIB_TARGET) /usr/local/lib/
	install -m 644 $(LIB_HEADER) /usr/local/include/
	ldconfig
	@echo "Library installed to /usr/local/lib/"
	@echo ""
	@echo "Note: Original binary is in src/ directory"
	@echo "To install Python dependencies: pip3 install PyQt6"

# Install only the library (not the original binary)
install-lib: library
	@echo "Installing library only..."
	install -m 755 $(LIB_TARGET) /usr/local/lib/
	install -m 644 $(LIB_HEADER) /usr/local/include/
	ldconfig
	@echo "Library installed to /usr/local/lib/"

# Install Python GUI dependencies
install-python:
	@echo "Installing Python dependencies..."
	pip3 install PyQt6
	@echo "Python dependencies installed"
	@echo "Run with: sudo python3 ryzen_monitor_gui.py"

# Clean everything
clean:
	$(MAKE) -C src clean
	rm -f $(LIB_OBJECTS) $(LIB_TARGET)
	@echo "Cleaned library files"

# Uninstall the library
uninstall:
	rm -f /usr/local/lib/$(LIB_TARGET)
	rm -f /usr/local/include/$(LIB_HEADER)
	ldconfig
	@echo "Library uninstalled"

# Help target
help:
	@echo "Ryzen Monitor Build System"
	@echo ""
	@echo "Targets:"
	@echo "  all            - Build original binary and shared library (default)"
	@echo "  library        - Build only the shared library"
	@echo "  install        - Install library to system"
	@echo "  clean          - Clean build files"
	@echo "  help           - Show this help"

.PHONY: $(TOPTARGETS) $(SUBDIRS) library install-lib install-python uninstall help