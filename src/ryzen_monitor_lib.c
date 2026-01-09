/**
 * Ryzen Monitor Library
 * Shared library wrapper for ryzen_monitor
 */

#define _GNU_SOURCE

#include "ryzen_monitor_lib.h"
#include "lib/libsmu.h"
#include "pm_tables.h"
#include "readinfo.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

smu_obj_t obj;
static int g_initialized = 0;

#define pmta(elem) ((pmt.elem) ? (*(pmt.elem)) : NAN)
#define pmta0(elem) ((pmt.elem) ? (*(pmt.elem)) : 0)

// Initialize the library
int ryzen_init(void) {
  if (g_initialized)
    return 0;

  smu_return_val ret = smu_init(&obj);
  if (ret != SMU_Return_OK) {
    return -1;
  }

  if (!smu_pm_tables_supported(&obj)) {
    return -2;
  }

  g_initialized = 1;
  return 0;
}

// Cleanup
void ryzen_cleanup(void) { g_initialized = 0; }

// Get system information
int ryzen_get_system_info(system_data_t *sysdata) {
  if (!g_initialized)
    return -1;

  system_info sysinfo;
  pm_table pmt;
  unsigned char *pm_buf;

  pm_buf = calloc(obj.pm_table_size, sizeof(unsigned char));
  if (!pm_buf)
    return -1;

  memset(&pmt, 0, sizeof(pm_table));

  // Select PM table version
  switch (obj.pm_table_version) {
  case 0x380904:
    pm_table_0x380904(&pmt, pm_buf);
    break;
  case 0x380905:
    pm_table_0x380905(&pmt, pm_buf);
    break;
  case 0x380804:
    pm_table_0x380804(&pmt, pm_buf);
    break;
  case 0x380805:
    pm_table_0x380805(&pmt, pm_buf);
    break;
  case 0x400005:
    pm_table_0x400005(&pmt, pm_buf);
    break;
  case 0x240903:
    pm_table_0x240903(&pmt, pm_buf);
    break;
  case 0x240803:
    pm_table_0x240803(&pmt, pm_buf);
    break;
  default:
    free(pm_buf);
    return -1;
  }

  sysinfo.cpu_name = get_processor_name();
  sysinfo.codename = smu_codename_to_str(&obj);
  sysinfo.smu_fw_ver = smu_get_fw_version(&obj);
  sysinfo.enabled_cores_count = pmt.max_cores;

  get_processor_topology(&sysinfo, pmt.zen_version);

  strncpy(sysdata->cpu_name, sysinfo.cpu_name, 255);
  strncpy(sysdata->codename, sysinfo.codename, 63);
  strncpy(sysdata->smu_fw_ver, sysinfo.smu_fw_ver, 31);
  sysdata->cores = sysinfo.cores;
  sysdata->ccds = sysinfo.ccds;
  sysdata->ccxs = sysinfo.ccxs;
  sysdata->cores_per_ccx = sysinfo.cores_per_ccx;
  sysdata->enabled_cores_count = sysinfo.enabled_cores_count;

  switch (obj.smu_if_version) {
  case IF_VERSION_9:
    sysdata->if_ver = 9;
    break;
  case IF_VERSION_10:
    sysdata->if_ver = 10;
    break;
  case IF_VERSION_11:
    sysdata->if_ver = 11;
    break;
  case IF_VERSION_12:
    sysdata->if_ver = 12;
    break;
  case IF_VERSION_13:
    sysdata->if_ver = 13;
    break;
  default:
    sysdata->if_ver = 0;
    break;
  }

  free(pm_buf);
  return 0;
}

// Read all data at once
int ryzen_read_data(core_data_t *cores, int max_cores,
                    constraints_data_t *constraints, memory_data_t *memory,
                    power_data_t *power, graphics_data_t *graphics,
                    calculated_stats_t *stats) {
  if (!g_initialized)
    return -1;

  unsigned char *pm_buf;
  pm_table pmt;
  system_info sysinfo;

  pm_buf = calloc(obj.pm_table_size, sizeof(unsigned char));
  if (!pm_buf)
    return -1;

  memset(&pmt, 0, sizeof(pm_table));

  // Select PM table
  switch (obj.pm_table_version) {
  case 0x380904:
    pm_table_0x380904(&pmt, pm_buf);
    break;
  case 0x380905:
    pm_table_0x380905(&pmt, pm_buf);
    break;
  case 0x380804:
    pm_table_0x380804(&pmt, pm_buf);
    break;
  case 0x380805:
    pm_table_0x380805(&pmt, pm_buf);
    break;
  case 0x400005:
    pm_table_0x400005(&pmt, pm_buf);
    break;
  case 0x240903:
    pm_table_0x240903(&pmt, pm_buf);
    break;
  case 0x240803:
    pm_table_0x240803(&pmt, pm_buf);
    break;
  default:
    free(pm_buf);
    return -1;
  }

  get_processor_topology(&sysinfo, pmt.zen_version);

  // Read PM table
  if (smu_read_pm_table(&obj, pm_buf, obj.pm_table_size) != SMU_Return_OK) {
    free(pm_buf);
    return -1;
  }

  // Calculated values
  float peak_core_frequency = 0, peak_core_temp = 0, peak_core_voltage = 0;
  float total_core_voltage = 0, total_core_power = 0, total_usage = 0, total_core_CC6 = 0;

  // Fill core data
  float package_sleep_time, average_voltage;
  if (pmt.PC6) {
    package_sleep_time = pmta(PC6) / 100.f;
    average_voltage =
        (pmta(CPU_TELEMETRY_VOLTAGE) - (0.2 * package_sleep_time)) /
        (1.0 - package_sleep_time);
  } else {
    average_voltage = pmta(CPU_TELEMETRY_VOLTAGE);
  }

  int core_count = (pmt.max_cores < max_cores) ? pmt.max_cores : max_cores;

  for (int i = 0; i < core_count; i++) {
    int core_disabled = (sysinfo.core_disable_map >> i) & 0x01;
    float core_frequency = pmta(CORE_FREQEFF[i]) * 1000.f;
    float core_sleep_time = pmta(CORE_CC6[i]) / 100.f;
    float core_voltage =
        ((1.0 - core_sleep_time) * average_voltage) + (0.2 * core_sleep_time);

    cores[i].core_num = i;
    cores[i].frequency = core_frequency;
    cores[i].power = pmta(CORE_POWER[i]);
    cores[i].voltage = core_voltage;
    cores[i].temp = pmta(CORE_TEMP[i]);
    cores[i].c0 = pmta(CORE_C0[i]);
    cores[i].cc1 = pmta(CORE_CC1[i]);
    cores[i].cc6 = pmta(CORE_CC6[i]);
    cores[i].disabled = core_disabled;
    cores[i].sleeping = (pmta(CORE_C0[i]) < 6.f);

    if (!core_disabled) {
      if (peak_core_frequency < core_frequency) peak_core_frequency = core_frequency;
      if (peak_core_temp < pmta(CORE_TEMP[i])) peak_core_temp = pmta(CORE_TEMP[i]);
      if (peak_core_voltage < core_voltage) peak_core_voltage = core_voltage;
      total_core_voltage += core_voltage;
      total_core_power += pmta(CORE_POWER[i]);
      total_usage += pmta(CORE_C0[i]);
      total_core_CC6 += pmta(CORE_CC6[i]);
    }
  }
  
  // Fill calculated stats
  stats->peak_core_frequency = peak_core_frequency;
  stats->peak_core_temp = peak_core_temp;
  stats->peak_core_voltage = peak_core_voltage;
  stats->avg_core_voltage = total_core_voltage / sysinfo.enabled_cores_count;
  stats->avg_core_cc6 = total_core_CC6 / sysinfo.enabled_cores_count;
  stats->total_core_power = total_core_power;
  stats->peak_core_voltage_smu = pmta(CPU_TELEMETRY_VOLTAGE);
  stats->package_cc6 = pmt.PC6 ? pmta(PC6) : NAN;

  // Fill constraints
  float edc = pmta(EDC_VALUE) * (total_usage / sysinfo.cores / 100);
  if (edc < pmta(TDC_VALUE))
    edc = pmta(TDC_VALUE);

  constraints->peak_temp = pmta(PEAK_TEMP);
  constraints->soc_temp = pmta(SOC_TEMP);
  constraints->gfx_temp = pmta(GFX_TEMP);
  constraints->vid_value = pmta(VID_VALUE);
  constraints->vid_limit = pmta(VID_LIMIT);
  constraints->ppt_value = pmta(PPT_VALUE);
  constraints->ppt_limit = pmta(PPT_LIMIT);
  constraints->ppt_apu_value = pmta(PPT_VALUE_APU);
  constraints->ppt_apu_limit = pmta(PPT_LIMIT_APU);
  constraints->tdc_value = pmta(TDC_VALUE);
  constraints->tdc_limit = pmta(TDC_LIMIT);
  constraints->tdc_actual = pmta(TDC_ACTUAL);
  constraints->tdc_soc_value = pmta(TDC_VALUE_SOC);
  constraints->tdc_soc_limit = pmta(TDC_LIMIT_SOC);
  constraints->edc_value = edc;
  constraints->edc_limit = pmta(EDC_LIMIT);
  constraints->edc_soc_value = pmta(EDC_VALUE_SOC);
  constraints->edc_soc_limit = pmta(EDC_LIMIT_SOC);
  constraints->thm_value = pmta(THM_VALUE);
  constraints->thm_limit = pmta(THM_LIMIT);
  constraints->thm_soc_value = pmta(THM_VALUE_SOC);
  constraints->thm_soc_limit = pmta(THM_LIMIT_SOC);
  constraints->thm_gfx_value = pmta(THM_VALUE_GFX);
  constraints->thm_gfx_limit = pmta(THM_LIMIT_GFX);
  constraints->fit_value = pmta(FIT_VALUE);
  constraints->fit_limit = pmta(FIT_LIMIT);

  // Fill memory
  memory->fclk_freq = pmta(FCLK_FREQ);
  memory->fclk_freq_eff = pmta(FCLK_FREQ_EFF);
  memory->uclk_freq = pmta(UCLK_FREQ);
  memory->memclk_freq = pmta(MEMCLK_FREQ);
  memory->v_vddm = pmta(V_VDDM);
  memory->v_vddp = pmta(V_VDDP);
  memory->v_vddg = pmta(V_VDDG);
  memory->v_vddg_iod = pmta(V_VDDG_IOD);
  memory->v_vddg_ccd = pmta(V_VDDG_CCD);
  memory->coupled_mode = (pmta(UCLK_FREQ) == pmta(MEMCLK_FREQ));

  // Fill power
  power->total_core_power = total_core_power;
  power->vddcr_soc_power = pmta(VDDCR_SOC_POWER);
  power->io_vddcr_soc_power = pmta(IO_VDDCR_SOC_POWER);
  power->gmi2_vddg_power = pmta(GMI2_VDDG_POWER);
  power->roc_power = pmta(ROC_POWER);
  power->l3_logic_power = 0;
  power->l3_vddm_power = 0;
  for (int i=0; i<pmt.max_l3; i++) {
    power->l3_logic_power += pmta0(L3_LOGIC_POWER[i]);
    power->l3_vddm_power += pmta0(L3_VDDM_POWER[i]);
  }
  power->vddio_mem_power = pmta(VDDIO_MEM_POWER);
  power->iod_vddio_mem_power = pmta(IOD_VDDIO_MEM_POWER);
  power->ddr_vddp_power = pmta(DDR_VDDP_POWER);
  power->ddr_phy_power = pmta(DDR_PHY_POWER);
  power->vdd18_power = pmta(VDD18_POWER);
  power->io_display_power = pmta(IO_DISPLAY_POWER);
  power->io_usb_power = pmta(IO_USB_POWER);
  power->socket_power = pmta(SOCKET_POWER);
  power->package_power = pmta(PACKAGE_POWER);
  power->vddcr_cpu_power = pmta(VDDCR_CPU_POWER);
  power->soc_telemetry_voltage = pmta(SOC_TELEMETRY_VOLTAGE);
  power->soc_telemetry_current = pmta(SOC_TELEMETRY_CURRENT);
  power->soc_telemetry_power = pmta(SOC_TELEMETRY_POWER);
  power->cpu_telemetry_voltage = pmta(CPU_TELEMETRY_VOLTAGE);
  power->cpu_telemetry_current = pmta(CPU_TELEMETRY_CURRENT);
  power->cpu_telemetry_power = pmta(CPU_TELEMETRY_POWER);
  
  // Fill graphics
  if(pmt.has_graphics) {
    graphics->gfx_voltage = pmta(GFX_VOLTAGE);
    graphics->roc_power = pmta(ROC_POWER);
    graphics->gfx_temp = pmta(GFX_TEMP);
    graphics->gfx_freq = pmta(GFX_FREQ);
    graphics->gfx_freq_eff = pmta(GFX_FREQEFF);
    graphics->gfx_busy = pmta(GFX_BUSY);
    graphics->gfx_edc_lim = pmta(GFX_EDC_LIM);
    graphics->gfx_edc_residency = pmta(GFX_EDC_RESIDENCY);
    graphics->display_count = pmta(DISPLAY_COUNT);
    graphics->fps = pmta(FPS);
    graphics->dgpu_power = pmta(DGPU_POWER);
    graphics->dgpu_freq_target = pmta(DGPU_FREQ_TARGET);
    graphics->dgpu_gfx_busy = pmta(DGPU_GFX_BUSY);
  }


  free(pm_buf);
  return core_count;
}