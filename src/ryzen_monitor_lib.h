/**
 * Ryzen Monitor Library
 * Header file
 */

#ifndef RYZEN_MONITOR_LIB_H
#define RYZEN_MONITOR_LIB_H

// Data structures for exporting
typedef struct {
  int core_num;
  float frequency;
  float power;
  float voltage;
  float temp;
  float c0;
  float cc1;
  float cc6;
  int disabled;
  int sleeping;
} core_data_t;

typedef struct {
  char cpu_name[256];
  char codename[64];
  char smu_fw_ver[32];
  int cores;
  int ccds;
  int ccxs;
  int cores_per_ccx;
  int if_ver;
  int enabled_cores_count;
} system_data_t;

typedef struct {
  float peak_temp;
  float soc_temp;
  float gfx_temp;
  float vid_value;
  float vid_limit;
  float ppt_value;
  float ppt_limit;
  float ppt_apu_value;
  float ppt_apu_limit;
  float tdc_value;
  float tdc_limit;
  float tdc_actual;
  float tdc_soc_value;
  float tdc_soc_limit;
  float edc_value;
  float edc_limit;
  float edc_soc_value;
  float edc_soc_limit;
  float thm_value;
  float thm_limit;
  float thm_soc_value;
  float thm_soc_limit;
  float thm_gfx_value;
  float thm_gfx_limit;
  float fit_value;
  float fit_limit;
} constraints_data_t;

typedef struct {
  float fclk_freq;
  float fclk_freq_eff;
  float uclk_freq;
  float memclk_freq;
  float v_vddm;
  float v_vddp;
  float v_vddg;
  float v_vddg_iod;
  float v_vddg_ccd;
  int coupled_mode;
} memory_data_t;

typedef struct {
  float total_core_power;
  float vddcr_soc_power;
  float io_vddcr_soc_power;
  float gmi2_vddg_power;
  float roc_power;
  float l3_logic_power;
  float l3_vddm_power;
  float vddio_mem_power;
  float iod_vddio_mem_power;
  float ddr_vddp_power;
  float ddr_phy_power;
  float vdd18_power;
  float io_display_power;
  float io_usb_power;
  float socket_power;
  float package_power;
  float vddcr_cpu_power;
  float soc_telemetry_voltage;
  float soc_telemetry_current;
  float soc_telemetry_power;
  float cpu_telemetry_voltage;
  float cpu_telemetry_current;
  float cpu_telemetry_power;
} power_data_t;

typedef struct {
    float gfx_voltage;
    float roc_power;
    float gfx_temp;
    float gfx_freq;
    float gfx_freq_eff;
    float gfx_busy;
    float gfx_edc_lim;
    float gfx_edc_residency;
    float display_count;
    float fps;
    float dgpu_power;
    float dgpu_freq_target;
    float dgpu_gfx_busy;
} graphics_data_t;

typedef struct {
    float peak_core_frequency;
    float peak_core_temp;
    float peak_core_voltage;
    float avg_core_voltage;
    float avg_core_cc6;
    float total_core_power;
    float peak_core_voltage_smu;
    float package_cc6;
} calculated_stats_t;


// Library functions
int ryzen_init(void);
void ryzen_cleanup(void);
int ryzen_get_system_info(system_data_t *sysdata);
int ryzen_read_data(core_data_t *cores, int max_cores,
                    constraints_data_t *constraints, 
                    memory_data_t *memory,
                    power_data_t *power,
                    graphics_data_t *graphics,
                    calculated_stats_t *stats);

#endif // RYZEN_MONITOR_LIB_H