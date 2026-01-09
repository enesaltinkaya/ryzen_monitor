#!/usr/bin/env python3
"""
Ryzen Monitor Qt GUI
Modern GUI interface for monitoring AMD Ryzen CPU statistics
"""

import sys
import ctypes
import os
from ctypes import Structure, c_int, c_float, c_char, POINTER
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QLabel, QGroupBox, QGridLayout, QProgressBar,
                             QMessageBox)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QPalette, QColor

# Define C structures matching the library header
class CoreData(Structure):
    _fields_ = [
        ("core_num", c_int), ("frequency", c_float), ("power", c_float),
        ("voltage", c_float), ("temp", c_float), ("c0", c_float),
        ("cc1", c_float), ("cc6", c_float), ("disabled", c_int),
        ("sleeping", c_int)
    ]

class SystemData(Structure):
    _fields_ = [
        ("cpu_name", c_char * 256), ("codename", c_char * 64),
        ("smu_fw_ver", c_char * 32), ("cores", c_int), ("ccds", c_int),
        ("ccxs", c_int), ("cores_per_ccx", c_int), ("if_ver", c_int),
        ("enabled_cores_count", c_int)
    ]

class ConstraintsData(Structure):
    _fields_ = [
        ("peak_temp", c_float), ("soc_temp", c_float), ("gfx_temp", c_float),
        ("vid_value", c_float), ("vid_limit", c_float), ("ppt_value", c_float),
        ("ppt_limit", c_float), ("ppt_apu_value", c_float), ("ppt_apu_limit", c_float),
        ("tdc_value", c_float), ("tdc_limit", c_float), ("tdc_actual", c_float),
        ("tdc_soc_value", c_float), ("tdc_soc_limit", c_float),
        ("edc_value", c_float), ("edc_limit", c_float), ("edc_soc_value", c_float),
        ("edc_soc_limit", c_float), ("thm_value", c_float), ("thm_limit", c_float),
        ("thm_soc_value", c_float), ("thm_soc_limit", c_float),
        ("thm_gfx_value", c_float), ("thm_gfx_limit", c_float),
        ("fit_value", c_float), ("fit_limit", c_float)
    ]

class MemoryData(Structure):
    _fields_ = [
        ("fclk_freq", c_float), ("fclk_freq_eff", c_float), ("uclk_freq", c_float),
        ("memclk_freq", c_float), ("v_vddm", c_float), ("v_vddp", c_float),
        ("v_vddg", c_float), ("v_vddg_iod", c_float), ("v_vddg_ccd", c_float),
        ("coupled_mode", c_int)
    ]

class PowerData(Structure):
    _fields_ = [
        ("total_core_power", c_float), ("vddcr_soc_power", c_float),
        ("io_vddcr_soc_power", c_float), ("gmi2_vddg_power", c_float),
        ("roc_power", c_float), ("l3_logic_power", c_float), ("l3_vddm_power", c_float),
        ("vddio_mem_power", c_float), ("iod_vddio_mem_power", c_float),
        ("ddr_vddp_power", c_float), ("ddr_phy_power", c_float),
        ("vdd18_power", c_float), ("io_display_power", c_float),
        ("io_usb_power", c_float), ("socket_power", c_float),
        ("package_power", c_float), ("vddcr_cpu_power", c_float),
        ("soc_telemetry_voltage", c_float), ("soc_telemetry_current", c_float),
        ("soc_telemetry_power", c_float), ("cpu_telemetry_voltage", c_float),
        ("cpu_telemetry_current", c_float), ("cpu_telemetry_power", c_float)
    ]

class GraphicsData(Structure):
    _fields_ = [
        ("gfx_voltage", c_float), ("roc_power", c_float), ("gfx_temp", c_float),
        ("gfx_freq", c_float), ("gfx_freq_eff", c_float), ("gfx_busy", c_float),
        ("gfx_edc_lim", c_float), ("gfx_edc_residency", c_float),
        ("display_count", c_float), ("fps", c_float), ("dgpu_power", c_float),
        ("dgpu_freq_target", c_float), ("dgpu_gfx_busy", c_float)
    ]

class CalculatedStats(Structure):
    _fields_ = [
        ("peak_core_frequency", c_float), ("peak_core_temp", c_float),
        ("peak_core_voltage", c_float), ("avg_core_voltage", c_float),
        ("avg_core_cc6", c_float), ("total_core_power", c_float),
        ("peak_core_voltage_smu", c_float), ("package_cc6", c_float)
    ]


class RyzenMonitorLib:
    """Wrapper for the Ryzen Monitor shared library"""
    
    def __init__(self):
        self.lib = None
        self.initialized = False
        
    def load(self, lib_path="libryzen_monitor.so"):
        """Load the shared library"""
        try:
            self.lib = ctypes.CDLL(lib_path)
            
            # Setup function signatures
            self.lib.ryzen_init.restype = c_int
            self.lib.ryzen_cleanup.restype = None
            self.lib.ryzen_get_system_info.argtypes = [POINTER(SystemData)]
            self.lib.ryzen_get_system_info.restype = c_int
            self.lib.ryzen_read_data.argtypes = [
                POINTER(CoreData), c_int,
                POINTER(ConstraintsData),
                POINTER(MemoryData),
                POINTER(PowerData),
                POINTER(GraphicsData),
                POINTER(CalculatedStats)
            ]
            self.lib.ryzen_read_data.restype = c_int
            
            return True
        except Exception as e:
            print(f"Failed to load library: {e}")
            return False
    
    def init(self):
        """Initialize the library"""
        if self.lib.ryzen_init() == 0:
            self.initialized = True
            return True
        return False
    
    def cleanup(self):
        """Cleanup"""
        if self.initialized:
            self.lib.ryzen_cleanup()
            self.initialized = False
    
    def get_system_info(self):
        """Get system information"""
        if not self.initialized:
            return None
        
        sysdata = SystemData()
        if self.lib.ryzen_get_system_info(ctypes.byref(sysdata)) == 0:
            return sysdata
        return None
    
    def read_data(self, max_cores=32):
        """Read all sensor data"""
        if not self.initialized:
            return None, None, None, None, None, None
        
        cores = (CoreData * max_cores)()
        constraints = ConstraintsData()
        memory = MemoryData()
        power = PowerData()
        graphics = GraphicsData()
        stats = CalculatedStats()

        num_cores = self.lib.ryzen_read_data(
            cores, max_cores,
            ctypes.byref(constraints),
            ctypes.byref(memory),
            ctypes.byref(power),
            ctypes.byref(graphics),
            ctypes.byref(stats)
        )
        
        if num_cores > 0:
            return cores[:num_cores], constraints, memory, power, graphics, stats
        return None, None, None, None, None, None


class RyzenMonitorGUI(QMainWindow):
    """Main GUI window"""
    
    def __init__(self):
        super().__init__()
        self.lib = RyzenMonitorLib()
        self.init_ui()
        
        # Try to load and initialize library
        script_dir = os.path.dirname(os.path.abspath(__file__))
        lib_path = os.path.join(script_dir, "libryzen_monitor.so")
        
        if not self.lib.load(lib_path):
            QMessageBox.critical(self, "Error", 
                               "Failed to load libryzen_monitor.so\n"
                               "Make sure it's built and in the same directory as the script.")
            sys.exit(1)
        
        if not self.lib.init():
            QMessageBox.critical(self, "Error",
                               "Failed to initialize Ryzen Monitor\n"
                               "Are you running as root?")
            sys.exit(1)
        
        self.sysdata = self.lib.get_system_info()
        if self.sysdata:
            self.update_system_info()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(2000)

    def init_ui(self):
        self.setWindowTitle("Ryzen Monitor")
        self.setGeometry(400, 200, 900, 810)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Top row: System Info and Calculated Stats
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)

        # System info section
        self.system_group = QGroupBox("System Information")
        system_layout = QGridLayout()
        self.system_group.setLayout(system_layout)
        self.cpu_label = QLabel("CPU: Loading...")
        self.codename_label = QLabel("Codename: Loading...")
        self.cores_label = QLabel("Cores: Loading...")
        self.smu_label = QLabel("SMU Version: Loading...")
        system_layout.addWidget(self.cpu_label, 0, 0)
        system_layout.addWidget(self.codename_label, 1, 0)
        system_layout.addWidget(self.cores_label, 2, 0)
        system_layout.addWidget(self.smu_label, 3, 0)
        top_layout.addWidget(self.system_group)

        # Calculated Core Stats
        self.calc_stats_group = QGroupBox("Core Statistics (Calculated)")
        calc_stats_layout = QGridLayout()
        self.calc_stats_group.setLayout(calc_stats_layout)
        self.peak_freq_label = QLabel("Highest Freq:")
        self.peak_freq_value = QLabel("--")
        self.peak_temp_label = QLabel("Highest Temp:")
        self.peak_temp_value = QLabel("--")
        self.peak_volt_label = QLabel("Highest Voltage:")
        self.peak_volt_value = QLabel("--")
        self.avg_volt_label = QLabel("Average Voltage:")
        self.avg_volt_value = QLabel("--")
        self.avg_cc6_label = QLabel("Average CC6:")
        self.avg_cc6_value = QLabel("--")
        self.total_core_power_label = QLabel("Total Core Power:")
        self.total_core_power_value = QLabel("--")
        self.smu_peak_volt_label = QLabel("Peak Voltage (SMU):")
        self.smu_peak_volt_value = QLabel("--")
        self.pkg_cc6_label = QLabel("Package CC6:")
        self.pkg_cc6_value = QLabel("--")
        calc_stats_layout.addWidget(self.peak_freq_label, 0, 0)
        calc_stats_layout.addWidget(self.peak_freq_value, 0, 1)
        calc_stats_layout.addWidget(self.peak_temp_label, 1, 0)
        calc_stats_layout.addWidget(self.peak_temp_value, 1, 1)
        calc_stats_layout.addWidget(self.peak_volt_label, 2, 0)
        calc_stats_layout.addWidget(self.peak_volt_value, 2, 1)
        calc_stats_layout.addWidget(self.avg_volt_label, 0, 2)
        calc_stats_layout.addWidget(self.avg_volt_value, 0, 3)
        calc_stats_layout.addWidget(self.avg_cc6_label, 1, 2)
        calc_stats_layout.addWidget(self.avg_cc6_value, 1, 3)
        calc_stats_layout.addWidget(self.total_core_power_label, 2, 2)
        calc_stats_layout.addWidget(self.total_core_power_value, 2, 3)
        calc_stats_layout.addWidget(self.smu_peak_volt_label, 3, 0)
        calc_stats_layout.addWidget(self.smu_peak_volt_value, 3, 1)
        calc_stats_layout.addWidget(self.pkg_cc6_label, 3, 2)
        calc_stats_layout.addWidget(self.pkg_cc6_value, 3, 3)
        top_layout.addWidget(self.calc_stats_group)

        # Core stats table
        self.core_group = QGroupBox("Core Statistics (Live)")
        core_layout = QVBoxLayout()
        self.core_group.setLayout(core_layout)
        self.core_table = QTableWidget()
        self.core_table.setColumnCount(8)
        self.core_table.setHorizontalHeaderLabels(["Core", "Freq (MHz)", "Power (W)", "Voltage (V)", "Temp (°C)", "C0 %", "C1 %", "C6 %"])
        core_layout.addWidget(self.core_table)
        main_layout.addWidget(self.core_group)

        # Middle row: Constraints and Memory
        middle_layout = QHBoxLayout()
        main_layout.addLayout(middle_layout)

        # Constraints section
        self.constraints_group = QGroupBox("Constraints")
        constraints_layout = QGridLayout()
        self.constraints_group.setLayout(constraints_layout)
        self.peak_temp_con_label = QLabel("Peak Temp:")
        self.peak_temp_con_value = QLabel("--")
        self.ppt_label = QLabel("PPT:")
        self.ppt_bar = QProgressBar()
        self.ppt_value = QLabel("--")
        self.tdc_label = QLabel("TDC:")
        self.tdc_bar = QProgressBar()
        self.tdc_value = QLabel("--")
        self.edc_label = QLabel("EDC:")
        self.edc_bar = QProgressBar()
        self.edc_value = QLabel("--")
        self.thm_label = QLabel("THM:")
        self.thm_bar = QProgressBar()
        self.thm_value = QLabel("--")
        constraints_layout.addWidget(self.peak_temp_con_label, 0, 0)
        constraints_layout.addWidget(self.peak_temp_con_value, 0, 1)
        constraints_layout.addWidget(self.ppt_label, 1, 0)
        constraints_layout.addWidget(self.ppt_bar, 1, 1)
        constraints_layout.addWidget(self.ppt_value, 1, 2)
        constraints_layout.addWidget(self.tdc_label, 2, 0)
        constraints_layout.addWidget(self.tdc_bar, 2, 1)
        constraints_layout.addWidget(self.tdc_value, 2, 2)
        constraints_layout.addWidget(self.edc_label, 3, 0)
        constraints_layout.addWidget(self.edc_bar, 3, 1)
        constraints_layout.addWidget(self.edc_value, 3, 2)
        constraints_layout.addWidget(self.thm_label, 4, 0)
        constraints_layout.addWidget(self.thm_bar, 4, 1)
        constraints_layout.addWidget(self.thm_value, 4, 2)
        middle_layout.addWidget(self.constraints_group)

        # Memory Interface
        self.memory_group = QGroupBox("Memory Interface")
        memory_layout = QGridLayout()
        self.memory_group.setLayout(memory_layout)
        self.fclk_label = QLabel("FCLK:")
        self.fclk_value = QLabel("--")
        self.fclk_eff_label = QLabel("FCLK (Eff):")
        self.fclk_eff_value = QLabel("--")
        self.uclk_label = QLabel("UCLK:")
        self.uclk_value = QLabel("--")
        self.memclk_label = QLabel("MEMCLK:")
        self.memclk_value = QLabel("--")
        self.coupled_label = QLabel("Coupled:")
        self.coupled_value = QLabel("--")
        # self.vddm_label = QLabel("cLDO VDDM:")
        # self.vddm_value = QLabel("--")
        # self.vddp_label = QLabel("cLDO VDDP:")
        # self.vddp_value = QLabel("--")
        # self.vddg_label = QLabel("cLDO VDDG:")
        # self.vddg_value = QLabel("--")
        memory_layout.addWidget(self.fclk_label, 0, 0)
        memory_layout.addWidget(self.fclk_value, 0, 1)
        memory_layout.addWidget(self.fclk_eff_label, 0, 2)
        memory_layout.addWidget(self.fclk_eff_value, 0, 3)
        memory_layout.addWidget(self.uclk_label, 1, 0)
        memory_layout.addWidget(self.uclk_value, 1, 1)
        memory_layout.addWidget(self.memclk_label, 1, 2)
        memory_layout.addWidget(self.memclk_value, 1, 3)
        memory_layout.addWidget(self.coupled_label, 2, 0)
        memory_layout.addWidget(self.coupled_value, 2, 1)
        # memory_layout.addWidget(self.vddm_label, 3, 0)
        # memory_layout.addWidget(self.vddm_value, 3, 1)
        # memory_layout.addWidget(self.vddp_label, 3, 2)
        # memory_layout.addWidget(self.vddp_value, 3, 3)
        # memory_layout.addWidget(self.vddg_label, 4, 0)
        # memory_layout.addWidget(self.vddg_value, 4, 1)
        middle_layout.addWidget(self.memory_group)

        # Bottom row: Power and Graphics
        bottom_layout = QHBoxLayout()
        main_layout.addLayout(bottom_layout)

        # Power Consumption
        self.power_group = QGroupBox("Power Consumption")
        power_layout = QGridLayout()
        self.power_group.setLayout(power_layout)
        self.socket_power_label = QLabel("Socket:")
        self.socket_power_value = QLabel("--")
        self.core_power_label = QLabel("Core Total:")
        self.core_power_value = QLabel("--")
        self.soc_power_label = QLabel("SoC:")
        self.soc_power_value = QLabel("--")
        # self.pkg_power_label = QLabel("Package:")
        # self.pkg_power_value = QLabel("--")
        power_layout.addWidget(self.socket_power_label, 0, 0)
        power_layout.addWidget(self.socket_power_value, 0, 1)
        power_layout.addWidget(self.core_power_label, 1, 0)
        power_layout.addWidget(self.core_power_value, 1, 1)
        power_layout.addWidget(self.soc_power_label, 2, 0)
        power_layout.addWidget(self.soc_power_value, 2, 1)
        # power_layout.addWidget(self.pkg_power_label, 3, 0)
        # power_layout.addWidget(self.pkg_power_value, 3, 1)
        bottom_layout.addWidget(self.power_group)
        
        # Graphics
        self.graphics_group = QGroupBox("Graphics")
        graphics_layout = QGridLayout()
        self.graphics_group.setLayout(graphics_layout)
        self.gfx_clk_label = QLabel("GFX Clock:")
        self.gfx_clk_value = QLabel("--")
        self.gfx_temp_label = QLabel("GFX Temp:")
        self.gfx_temp_value = QLabel("--")
        graphics_layout.addWidget(self.gfx_clk_label, 0, 0)
        graphics_layout.addWidget(self.gfx_clk_value, 0, 1)
        graphics_layout.addWidget(self.gfx_temp_label, 1, 0)
        graphics_layout.addWidget(self.gfx_temp_value, 1, 1)
        bottom_layout.addWidget(self.graphics_group)
    
    def update_system_info(self):
        if not self.sysdata: return
        self.cpu_label.setText(f"CPU: {self.sysdata.cpu_name.decode('utf-8')}")
        self.codename_label.setText(f"Codename: {self.sysdata.codename.decode('utf-8')}")
        self.cores_label.setText(f"Cores: {self.sysdata.enabled_cores_count} / CCDs: {self.sysdata.ccds}")
        self.smu_label.setText(f"SMU: v{self.sysdata.smu_fw_ver.decode('utf-8')}")
    
    def update_data(self):
        cores, constraints, memory, power, graphics, stats = self.lib.read_data()
        if not cores: return

        # Core Table
        self.core_table.setRowCount(len(cores))
        for i, core in enumerate(cores):
            status = "Disabled" if core.disabled else ("Sleeping" if core.sleeping else f"{core.frequency:.0f}")
            self.core_table.setItem(i, 0, QTableWidgetItem(f"Core {core.core_num}"))
            self.core_table.setItem(i, 1, QTableWidgetItem(status))
            self.core_table.setItem(i, 2, QTableWidgetItem(f"{core.power:.3f}"))
            self.core_table.setItem(i, 3, QTableWidgetItem(f"{core.voltage:.3f}"))
            self.core_table.setItem(i, 4, QTableWidgetItem(f"{core.temp:.1f}"))
            self.core_table.setItem(i, 5, QTableWidgetItem(f"{core.c0:.1f}"))
            self.core_table.setItem(i, 6, QTableWidgetItem(f"{core.cc1:.1f}"))
            self.core_table.setItem(i, 7, QTableWidgetItem(f"{core.cc6:.1f}"))

        # Calculated Stats
        if stats:
            self.peak_freq_value.setText(f"{stats.peak_core_frequency:.0f} MHz")
            self.peak_temp_value.setText(f"{stats.peak_core_temp:.1f} °C")
            self.peak_volt_value.setText(f"{stats.peak_core_voltage:.3f} V")
            self.avg_volt_value.setText(f"{stats.avg_core_voltage:.3f} V")
            self.avg_cc6_value.setText(f"{stats.avg_core_cc6:.1f} %")
            self.total_core_power_value.setText(f"{stats.total_core_power:.3f} W")
            self.smu_peak_volt_value.setText(f"{stats.peak_core_voltage_smu:.3f} V")
            self.pkg_cc6_value.setText(f"{stats.package_cc6:.1f} %" if not stats.package_cc6 != stats.package_cc6 else "--")


        # Constraints
        if constraints:
            self.peak_temp_con_value.setText(f"{constraints.peak_temp:.1f} °C")
            self.ppt_bar.setValue(int(constraints.ppt_value / constraints.ppt_limit * 100) if constraints.ppt_limit > 0 else 0)
            self.ppt_value.setText(f"{constraints.ppt_value:.1f} / {constraints.ppt_limit:.0f} W")
            self.tdc_bar.setValue(int(constraints.tdc_value / constraints.tdc_limit * 100) if constraints.tdc_limit > 0 else 0)
            self.tdc_value.setText(f"{constraints.tdc_value:.1f} / {constraints.tdc_limit:.0f} A")
            self.edc_bar.setValue(int(constraints.edc_value / constraints.edc_limit * 100) if constraints.edc_limit > 0 else 0)
            self.edc_value.setText(f"{constraints.edc_value:.1f} / {constraints.edc_limit:.0f} A")
            self.thm_bar.setValue(int(constraints.thm_value / constraints.thm_limit * 100) if constraints.thm_limit > 0 else 0)
            self.thm_value.setText(f"{constraints.thm_value:.1f} / {constraints.thm_limit:.0f} C")

        # Memory
        if memory:
            self.fclk_value.setText(f"{memory.fclk_freq:.0f} MHz")
            self.fclk_eff_value.setText(f"{memory.fclk_freq_eff:.0f} MHz")
            self.uclk_value.setText(f"{memory.uclk_freq:.0f} MHz")
            self.memclk_value.setText(f"{memory.memclk_freq:.0f} MHz")
            self.coupled_value.setText("ON" if memory.coupled_mode else "OFF")
            # self.vddm_value.setText(f"{memory.v_vddm:.4f} V")
            # self.vddp_value.setText(f"{memory.v_vddp:.4f} V")
            # self.vddg_value.setText(f"{memory.v_vddg:.4f} V")
        
        # Power
        if power:
            self.socket_power_value.setText(f"{power.socket_power:.3f} W")
            self.core_power_value.setText(f"{power.total_core_power:.3f} W")
            self.soc_power_value.setText(f"{power.vddcr_soc_power:.3f} W")
            # self.pkg_power_value.setText(f"{power.package_power:.3f} W")

        # Graphics
        if graphics:
            self.gfx_clk_value.setText(f"{graphics.gfx_freq:.0f} MHz")
            self.gfx_temp_value.setText(f"{graphics.gfx_temp:.1f} °C")

    def closeEvent(self, event):
        self.timer.stop()
        self.lib.cleanup()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Set dark theme
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)

    # Set font size for scaling
    font = QFont()
    font.setPointSize(8)
    app.setFont(font)
    
    if os.geteuid() != 0:
        QMessageBox.warning(None, "Warning", 
                          "This application needs root privileges to read sensor data.\n"
                          "Please run with sudo.")
    
    window = RyzenMonitorGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()