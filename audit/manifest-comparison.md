# Manifest comparison

Max 4 stock observations use the bundled snapshots. Q2 uses a saved factory-restore capture.

Q2 printer.cfg SHA-256: bce42786d28584f793e8b7512f831d4b36cc29d0e6c6b84654285d6d2d4dbc2e

## set_options

| Patch | Max 4 firmware | Expected → desired | Max 4 stock | Q2 stock |
|---|---|---|---|---|
| stepper_x_homing_speed | 01.01.06.03 | 50 → 65 | 50 | 50 (matches Max 4 guard) |
| stepper_x_homing_speed | 01.01.06.04 | 50 → 65 | 50 | 50 (matches Max 4 guard) |
| stepper_x_homing_speed | 01.01.06.05 | 50 → 65 | 50 | 50 (matches Max 4 guard) |
| stepper_x_homing_speed | 01.01.07.01 | 50 → 65 | 50 | 50 (matches Max 4 guard) |
| stepper_x_second_homing_speed | 01.01.06.03 | 50.0 → 55.0 | 50.0 | — |
| stepper_x_second_homing_speed | 01.01.06.04 | 50.0 → 55.0 | 50.0 | — |
| stepper_x_second_homing_speed | 01.01.06.05 | 50.0 → 55.0 | 50.0 | — |
| stepper_x_second_homing_speed | 01.01.07.01 | 50.0 → 55.0 | 50.0 | — |
| stepper_x_homing_retract_dist | 01.01.06.03 | 50.0 → 20.0 | 50.0 | 0 (differs Max 4 guard) |
| stepper_x_homing_retract_dist | 01.01.06.04 | 50.0 → 20.0 | 50.0 | 0 (differs Max 4 guard) |
| stepper_x_homing_retract_dist | 01.01.06.05 | 50.0 → 20.0 | 50.0 | 0 (differs Max 4 guard) |
| stepper_x_homing_retract_dist | 01.01.07.01 | 50.0 → 20.0 | 50.0 | 0 (differs Max 4 guard) |
| stepper_x_homing_retract_speed | 01.01.06.03 | 200.0 → 500.0 | 200.0 | — |
| stepper_x_homing_retract_speed | 01.01.06.04 | 200.0 → 500.0 | 200.0 | — |
| stepper_x_homing_retract_speed | 01.01.06.05 | 200.0 → 500.0 | 200.0 | — |
| stepper_x_homing_retract_speed | 01.01.07.01 | 200.0 → 500.0 | 200.0 | — |
| stepper_y_homing_speed | 01.01.06.03 | 50 → 65 | 50 | 50 (matches Max 4 guard) |
| stepper_y_homing_speed | 01.01.06.04 | 50 → 65 | 50 | 50 (matches Max 4 guard) |
| stepper_y_homing_speed | 01.01.06.05 | 50 → 65 | 50 | 50 (matches Max 4 guard) |
| stepper_y_homing_speed | 01.01.07.01 | 50 → 65 | 50 | 50 (matches Max 4 guard) |
| stepper_y_second_homing_speed | 01.01.06.03 | 50.0 → 55.0 | 50.0 | — |
| stepper_y_second_homing_speed | 01.01.06.04 | 50.0 → 55.0 | 50.0 | — |
| stepper_y_second_homing_speed | 01.01.06.05 | 50.0 → 55.0 | 50.0 | — |
| stepper_y_second_homing_speed | 01.01.07.01 | 50.0 → 55.0 | 50.0 | — |
| stepper_y_homing_retract_dist | 01.01.06.03 | 50.0 → 20.0 | 50.0 | 0 (differs Max 4 guard) |
| stepper_y_homing_retract_dist | 01.01.06.04 | 50.0 → 20.0 | 50.0 | 0 (differs Max 4 guard) |
| stepper_y_homing_retract_dist | 01.01.06.05 | 50.0 → 20.0 | 50.0 | 0 (differs Max 4 guard) |
| stepper_y_homing_retract_dist | 01.01.07.01 | 50.0 → 20.0 | 50.0 | 0 (differs Max 4 guard) |
| stepper_y_homing_retract_speed | 01.01.06.03 | 200.0 → 500.0 | 200.0 | — |
| stepper_y_homing_retract_speed | 01.01.06.04 | 200.0 → 500.0 | 200.0 | — |
| stepper_y_homing_retract_speed | 01.01.06.05 | 200.0 → 500.0 | 200.0 | — |
| stepper_y_homing_retract_speed | 01.01.07.01 | 200.0 → 500.0 | 200.0 | — |
| stepper_z_homing_retract_dist | 01.01.06.03 | 10.0 → 5.0 | 10.0 | 10.0 (matches Max 4 guard) |
| stepper_z_homing_retract_dist | 01.01.06.04 | 10.0 → 5.0 | 10.0 | 10.0 (matches Max 4 guard) |
| stepper_z_homing_retract_dist | 01.01.06.05 | 10.0 → 5.0 | 10.0 | 10.0 (matches Max 4 guard) |
| stepper_z_homing_retract_dist | 01.01.07.01 | 10.0 → 5.0 | 10.0 | 10.0 (matches Max 4 guard) |
| printer_max_velocity | 01.01.06.03 | 800 → 565 | 800 | 600 (differs Max 4 guard) |
| printer_max_velocity | 01.01.06.04 | 800 → 565 | 800 | 600 (differs Max 4 guard) |
| printer_max_velocity | 01.01.06.05 | 800 → 565 | 800 | 600 (differs Max 4 guard) |
| printer_max_velocity | 01.01.07.01 | 800 → 565 | 800 | 600 (differs Max 4 guard) |
| z_tilt_speed | 01.01.06.03 | 150 → 565 | 150 | 150 (matches Max 4 guard) |
| z_tilt_speed | 01.01.06.04 | 150 → 565 | 150 | 150 (matches Max 4 guard) |
| z_tilt_speed | 01.01.06.05 | 150 → 565 | 150 | 150 (matches Max 4 guard) |
| z_tilt_speed | 01.01.07.01 | 150 → 565 | 150 | 150 (matches Max 4 guard) |
| bed_mesh_speed | 01.01.06.03 | 150 → 565 | 150 | 100 (differs Max 4 guard) |
| bed_mesh_speed | 01.01.06.04 | 150 → 565 | 150 | 100 (differs Max 4 guard) |
| bed_mesh_speed | 01.01.06.05 | 150 → 565 | 150 | 100 (differs Max 4 guard) |
| bed_mesh_speed | 01.01.07.01 | 150 → 565 | 150 | 100 (differs Max 4 guard) |
| virtual_sdcard_on_error_gcode | 01.01.06.03 | CANCEL_PRINT → OPTIMIZED_CANCEL_PRINT_ON_ERROR | CANCEL_PRINT | CANCEL_PRINT (matches Max 4 guard) |
| virtual_sdcard_on_error_gcode | 01.01.06.04 | CANCEL_PRINT → OPTIMIZED_CANCEL_PRINT_ON_ERROR | CANCEL_PRINT | CANCEL_PRINT (matches Max 4 guard) |
| virtual_sdcard_on_error_gcode | 01.01.06.05 | CANCEL_PRINT → OPTIMIZED_CANCEL_PRINT_ON_ERROR | CANCEL_PRINT | CANCEL_PRINT (matches Max 4 guard) |
| virtual_sdcard_on_error_gcode | 01.01.07.01 | CANCEL_PRINT → OPTIMIZED_CANCEL_PRINT_ON_ERROR | CANCEL_PRINT | CANCEL_PRINT (matches Max 4 guard) |
| hotend_fan_tachometer_poll_interval | 01.01.06.03 | 0.0015 → 0.00075 | 0.0015 | 0.0005 (differs Max 4 guard) |
| hotend_fan_tachometer_poll_interval | 01.01.06.04 | 0.0015 → 0.00075 | 0.0015 | 0.0005 (differs Max 4 guard) |
| hotend_fan_tachometer_poll_interval | 01.01.06.05 | 0.0005 → 0.00075 | 0.0005 | 0.0005 (matches Max 4 guard) |
| hotend_fan_tachometer_poll_interval | 01.01.07.01 | 0.0005 → 0.00075 | 0.0005 | 0.0005 (matches Max 4 guard) |
| timelapse_take_frame_verbose | 01.01.06.03 | True → False | True | True (matches Max 4 guard) |
| timelapse_take_frame_verbose | 01.01.06.04 | True → False | True | True (matches Max 4 guard) |
| timelapse_take_frame_verbose | 01.01.06.05 | True → False | True | True (matches Max 4 guard) |
| timelapse_take_frame_verbose | 01.01.07.01 | True → False | True | True (matches Max 4 guard) |
| closed_loop_x_query_cycle | 01.01.06.04 | 5 → 10 | 10 | — |
| closed_loop_x_query_cycle | 01.01.06.05 | 5 → 10 | 10 | — |
| closed_loop_x_query_cycle | 01.01.07.01 | 5 → 10 | 10 | — |
| closed_loop_y_query_cycle | 01.01.06.04 | 5 → 10 | 10 | — |
| closed_loop_y_query_cycle | 01.01.06.05 | 5 → 10 | 10 | — |
| closed_loop_y_query_cycle | 01.01.07.01 | 5 → 10 | 10 | — |
| closed_loop_x_trigger_current | 01.01.06.04 | 400 → 400 | 400 | — |
| closed_loop_x_trigger_current | 01.01.06.05 | 400 → 400 | 400 | — |
| closed_loop_x_trigger_current | 01.01.07.01 | 400 → 400 | 400 | — |
| closed_loop_x_trigger_time | 01.01.06.04 | 2 → 2 | 2 | — |
| closed_loop_x_trigger_time | 01.01.06.05 | 2 → 2 | 2 | — |
| closed_loop_x_trigger_time | 01.01.07.01 | 2 → 2 | 2 | — |
| closed_loop_x_trigger_speed | 01.01.06.04 | 50 → 50 | 50 | — |
| closed_loop_x_trigger_speed | 01.01.06.05 | 50 → 50 | 50 | — |
| closed_loop_x_trigger_speed | 01.01.07.01 | 50 → 50 | 50 | — |
| closed_loop_y_trigger_current | 01.01.06.04 | 400 → 400 | 400 | — |
| closed_loop_y_trigger_current | 01.01.06.05 | 400 → 400 | 400 | — |
| closed_loop_y_trigger_current | 01.01.07.01 | 400 → 400 | 400 | — |
| closed_loop_y_trigger_time | 01.01.06.04 | 2 → 2 | 2 | — |
| closed_loop_y_trigger_time | 01.01.06.05 | 2 → 2 | 2 | — |
| closed_loop_y_trigger_time | 01.01.07.01 | 2 → 2 | 2 | — |
| closed_loop_y_trigger_speed | 01.01.06.04 | 50 → 50 | 50 | — |
| closed_loop_y_trigger_speed | 01.01.06.05 | 50 → 50 | 50 | — |
| closed_loop_y_trigger_speed | 01.01.07.01 | 50 → 50 | 50 | — |
| chamber_thermal_protection_sensor_max_temp | 01.01.06.04 | 150 → 170 | 170 | 150 (matches Max 4 guard) |
| chamber_thermal_protection_sensor_max_temp | 01.01.06.05 | 150 → 170 | 170 | 150 (matches Max 4 guard) |
| chamber_thermal_protection_sensor_max_temp | 01.01.07.01 | 150 → 170 | 170 | 150 (matches Max 4 guard) |
| official_fila25_filament | 01.01.06.04 | PA-CF → PA6-CF | PA6-CF | PA6-CF (differs Max 4 guard) |
| official_fila25_filament | 01.01.06.05 | PA-CF → PA6-CF | PA6-CF | PA6-CF (differs Max 4 guard) |
| official_fila25_filament | 01.01.07.01 | PA-CF → PA6-CF | PA6-CF | PA6-CF (differs Max 4 guard) |
| official_fila25_type | 01.01.06.04 | PA-CF → PA6-CF | PA6-CF | PA6-CF (differs Max 4 guard) |
| official_fila25_type | 01.01.06.05 | PA-CF → PA6-CF | PA6-CF | PA6-CF (differs Max 4 guard) |
| official_fila25_type | 01.01.07.01 | PA-CF → PA6-CF | PA6-CF | PA6-CF (differs Max 4 guard) |

## delete_sections

| Patch | Max 4 firmware | Expected → desired | Max 4 stock | Q2 stock |
|---|---|---|---|---|
| filament_switch_sensor | 01.01.06.03 | 4466d08166d6 → remove | matches | differs |
| filament_switch_sensor | 01.01.06.04 | 82ddb60dd799 → remove | matches | differs |
| filament_switch_sensor | 01.01.06.05 | 82ddb60dd799 → remove | matches | differs |
| filament_switch_sensor | 01.01.07.01 | 4466d08166d6 → remove | matches | differs |
| pause_resume_cancel_resume | 01.01.06.03 | b11be3af4998 → remove | matches | absent |
| pause_resume_cancel_resume | 01.01.06.04 | b11be3af4998 → remove | matches | absent |
| pause_resume_cancel_resume | 01.01.06.05 | b11be3af4998 → remove | matches | absent |
| pause_resume_cancel_resume | 01.01.07.01 | 866bc3a0ab78 → remove | matches | absent |
| filament_cut_filament_1 | 01.01.06.03 | 130d5ec6b020 → remove | matches | absent |
| filament_cut_filament_1 | 01.01.06.04 | 130d5ec6b020 → remove | matches | absent |
| filament_cut_filament_1 | 01.01.06.05 | 130d5ec6b020 → remove | matches | absent |
| filament_cut_filament_1 | 01.01.07.01 | 79234acad35e → remove | matches | absent |
| heaters_m109_0 | 01.01.06.03 | 50260f1efe09 → remove | matches | absent |
| heaters_m109_0 | 01.01.06.04 | 50260f1efe09 → remove | matches | absent |
| heaters_m109_0 | 01.01.06.05 | 50260f1efe09 → remove | matches | absent |
| heaters_m109_0 | 01.01.07.01 | 50260f1efe09 → remove | matches | absent |
| fans_m106 | 01.01.06.03 | 07741866908f → remove | matches | absent |
| fans_m106 | 01.01.06.04 | 07741866908f → remove | matches | absent |
| fans_m106 | 01.01.06.05 | 07741866908f → remove | matches | absent |
| fans_m106 | 01.01.07.01 | 07741866908f → remove | matches | absent |
| kinematics_homing_override | 01.01.06.03 | 6a924478b351 → remove | matches | absent |
| kinematics_homing_override | 01.01.06.04 | 6a924478b351 → remove | matches | absent |
| kinematics_homing_override | 01.01.06.05 | 6a924478b351 → remove | matches | absent |
| kinematics_homing_override | 01.01.07.01 | 6a924478b351 → remove | matches | absent |
| start_end_apply_print_offset | 01.01.06.03 | ea8be4dae3bc → remove | matches | absent |
| start_end_apply_print_offset | 01.01.06.04 | ea8be4dae3bc → remove | matches | absent |
| start_end_apply_print_offset | 01.01.06.05 | ea8be4dae3bc → remove | matches | absent |
| start_end_apply_print_offset | 01.01.07.01 | ea8be4dae3bc → remove | matches | absent |

## Guarded Klipper source replacements

| Patch | Max 4 firmware | Expected stock hash | Q2 capture |
|---|---|---|---|
| qidi_homing | 01.01.06.03 | 89428b465b7f3d62bd8b65b3155b8aa8e93cd917f59779e40a246b5d89ff8d71 | not captured |
| qidi_homing | 01.01.06.04 | ff0439f8b9e702537f66c16508f7b0a137b27cff51eb653aa951172d3e5184a0 | not captured |
| qidi_homing | 01.01.06.04 | 0310d9ed0a838b2a7ecff8cd2ec15488b1ae3d8f165a458addd16d8366a60761 | not captured |
| qidi_homing | 01.01.06.05 | 0310d9ed0a838b2a7ecff8cd2ec15488b1ae3d8f165a458addd16d8366a60761 | not captured |
| qidi_homing | 01.01.07.01 | 0310d9ed0a838b2a7ecff8cd2ec15488b1ae3d8f165a458addd16d8366a60761 | not captured |

Max 4 source hashes above are installer guard expectations. The bundled stock config trees do not supply these source files.

## Common Klipper modules

- `installer/klipper/tltg/background_save_config.py`
- `installer/klipper/tltg/bed_soak.py`
- `installer/klipper/tltg/box485_monitor.py`
- `installer/klipper/tltg/box_eject.py`
- `installer/klipper/tltg/box_feed_motion.py`
- `installer/klipper/tltg/box_feed_test.py`
- `installer/klipper/tltg/box_filament_guard.py`
- `installer/klipper/tltg/box_flow_recovery.py`
- `installer/klipper/tltg/box_heater_refresh.py`
- `installer/klipper/tltg/box_link_monitor.py`
- `installer/klipper/tltg/box_loaded_slot.py`
- `installer/klipper/tltg/box_mcu_temperature.py`
- `installer/klipper/tltg/box_rfid.py`
- `installer/klipper/tltg/box_slot_jog.py`
- `installer/klipper/tltg/chamber_exhaust_guard.py`
- `installer/klipper/tltg/cold_cut.py`
- `installer/klipper/tltg/filament_catalog.py`
- `installer/klipper/tltg/klipper_fixes.py`
- `installer/klipper/tltg/klipper_health.py`
- `installer/klipper/tltg/macro_status.py`
- `installer/klipper/tltg/pause_timeout.py`
- `installer/klipper/tltg/printer_warnings.py`
- `installer/klipper/tltg/probe_report.py`
- `installer/klipper/tltg/probe_test.py`
- `installer/klipper/tltg/resonance_sweep.py`
- `installer/klipper/tltg/save_variables_fast.py`
- `installer/klipper/tltg/spoolman.py`
- `installer/klipper/tltg/step_loss_monitor.py`
- `installer/klipper/tltg/velocity_limit.py`

## Common and Max 4 macro files

- `installer/klipper/printers/max4/homing.cfg`
- `installer/klipper/printers/max4/nozzle_motion.cfg`
- `installer/klipper/printers/max4/printer_profile.cfg`
- `installer/klipper/tltg-optimized-macros/background_save_config.cfg`
- `installer/klipper/tltg-optimized-macros/bed_mesh.cfg`
- `installer/klipper/tltg-optimized-macros/bed_soak.cfg`
- `installer/klipper/tltg-optimized-macros/box485_monitor.cfg`
- `installer/klipper/tltg-optimized-macros/box_eject.cfg`
- `installer/klipper/tltg-optimized-macros/box_feed_motion.cfg`
- `installer/klipper/tltg-optimized-macros/box_filament_guard.cfg`
- `installer/klipper/tltg-optimized-macros/box_flow_recovery.cfg`
- `installer/klipper/tltg-optimized-macros/box_heater_refresh.cfg`
- `installer/klipper/tltg-optimized-macros/box_link_monitor.cfg`
- `installer/klipper/tltg-optimized-macros/box_loaded_slot.cfg`
- `installer/klipper/tltg-optimized-macros/box_mcu_temperature.cfg`
- `installer/klipper/tltg-optimized-macros/box_rfid.cfg`
- `installer/klipper/tltg-optimized-macros/box_slot_jog.cfg`
- `installer/klipper/tltg-optimized-macros/cancel.cfg`
- `installer/klipper/tltg-optimized-macros/cold_cut.cfg`
- `installer/klipper/tltg-optimized-macros/cooling.cfg`
- `installer/klipper/tltg-optimized-macros/filament.cfg`
- `installer/klipper/tltg-optimized-macros/globals.cfg`
- `installer/klipper/tltg-optimized-macros/heaters.cfg`
- `installer/klipper/tltg-optimized-macros/helpers.cfg`
- `installer/klipper/tltg-optimized-macros/input_shaper.cfg`
- `installer/klipper/tltg-optimized-macros/kinematics.cfg`
- `installer/klipper/tltg-optimized-macros/klipper_fixes.cfg`
- `installer/klipper/tltg-optimized-macros/klipper_health.cfg`
- `installer/klipper/tltg-optimized-macros/macro_status.cfg`
- `installer/klipper/tltg-optimized-macros/motion.cfg`
- `installer/klipper/tltg-optimized-macros/offset.cfg`
- `installer/klipper/tltg-optimized-macros/printer_warnings.cfg`
- `installer/klipper/tltg-optimized-macros/resonance_sweep.cfg`
- `installer/klipper/tltg-optimized-macros/save_variables_fast.cfg`
- `installer/klipper/tltg-optimized-macros/spoolman.cfg`
- `installer/klipper/tltg-optimized-macros/start_end.cfg`
- `installer/klipper/tltg-optimized-macros/step_loss_monitor.cfg`
- `installer/klipper/tltg-optimized-macros/temperatures.cfg`

## Installer runtime

- `installer/runtime/__init__.py`
- `installer/runtime/__main__.py`
- `installer/runtime/addons.py`
- `installer/runtime/addons_cli.py`
- `installer/runtime/addons_service.py`
- `installer/runtime/auto_update.py`
- `installer/runtime/backup.py`
- `installer/runtime/bootstrap.py`
- `installer/runtime/box_enablement.py`
- `installer/runtime/box_firmware.py`
- `installer/runtime/cli.py`
- `installer/runtime/compatibility.py`
- `installer/runtime/config_transaction.py`
- `installer/runtime/cpu_governor.py`
- `installer/runtime/cpu_tuning.py`
- `installer/runtime/demo.py`
- `installer/runtime/ensure_lines.py`
- `installer/runtime/errors.py`
- `installer/runtime/firmware.py`
- `installer/runtime/fluidd_box_filaments.py`
- `installer/runtime/fluidd_box_motion.js`
- `installer/runtime/fluidd_filament_config.py`
- `installer/runtime/fluidd_qidibox_card.js`
- `installer/runtime/fluidd_remote_screen.js`
- `installer/runtime/fs_atomic.py`
- `installer/runtime/host_reboot.py`
- `installer/runtime/interaction.py`
- `installer/runtime/klipper_box_config.py`
- `installer/runtime/klipper_cfg.py`
- `installer/runtime/klipper_print_stats_manager.py`
- `installer/runtime/legacy_manual_install.py`
- `installer/runtime/locking.py`
- `installer/runtime/mainboard_firmware.py`
- `installer/runtime/manifest.py`
- `installer/runtime/messages.py`
- `installer/runtime/mirror.py`
- `installer/runtime/models.py`
- `installer/runtime/moonraker_allowed_services.py`
- `installer/runtime/moonraker_file_manager.py`
- `installer/runtime/moonraker_klippy_apis.py`
- `installer/runtime/moonraker_speedups.py`
- `installer/runtime/moonraker_spoolman.py`
- `installer/runtime/moonraker_used_extruders.py`
- `installer/runtime/naming.py`
- `installer/runtime/ownership.py`
- `installer/runtime/patches.py`
- `installer/runtime/path_safety.py`
- `installer/runtime/postflight.py`
- `installer/runtime/preflight.py`
- `installer/runtime/process_restart.py`
- `installer/runtime/remote_screen.py`
- `installer/runtime/reporter.py`
- `installer/runtime/restart_on_exit.py`
- `installer/runtime/restore_helper.py`
- `installer/runtime/rollback.py`
- `installer/runtime/runner.py`
- `installer/runtime/safety.py`
- `installer/runtime/service_priority.py`
- `installer/runtime/source_patches.py`
- `installer/runtime/state_file.py`
- `installer/runtime/static_build.py`
- `installer/runtime/sudo.py`
- `installer/runtime/system_optimizations.py`
- `installer/runtime/thr_firmware.py`
- `installer/runtime/uninstall.py`
- `installer/runtime/vendor_imports.py`
- `installer/runtime/webcam_id.py`
- `installer/runtime/zram_swap.py`

## Firmware manifests

- `firmware/max4-box-valve-oil-v1.json`
- `firmware/max4-mcu-closed-loop-replies-v1.json`
- `firmware/max4-thr-lis2dw-fifo-v1.json`

## Slicer packs

- `orcaslicer_gcode/change_filament.gcode`
- `orcaslicer_gcode/end.gcode`
- `orcaslicer_gcode/layer_change.gcode`
- `orcaslicer_gcode/pause.gcode`
- `orcaslicer_gcode/start.gcode`
- `orcaslicer_gcode/timelapse.gcode`
- `qidistudio_gcode/change_filament.gcode`
- `qidistudio_gcode/end.gcode`
- `qidistudio_gcode/layer_change.gcode`
- `qidistudio_gcode/pause.gcode`
- `qidistudio_gcode/start.gcode`
