"""Assemble a Q2 non-motion preview from pinned, locally reviewed sources."""
import argparse,hashlib,importlib.util,json,shutil,sys
from pathlib import Path

UPSTREAM='fea34e996f1ab64c646dd02846d1bb47ad93c272'
NONMOTION=['background_save_config','save_variables_fast','klipper_health','macro_status','printer_warnings','spoolman','probe_test','probe_report','box_heater_refresh','update_lights','box_mcu_temperature']
CORE=['box_rfid','box485_monitor','box_link_monitor','box_slot_jog']
EXCLUDED=['box_feed_motion','box_eject','box_filament_guard','box_loaded_slot','box_spool_roll','box_flow_recovery','cold_cut','klipper_fixes','step_loss_monitor','velocity_limit','resonance_sweep','pause_timeout','bed_soak','chamber_exhaust_guard']

def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--upstream',type=Path,required=True);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--firmware',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();w=a.workspace;out=a.output
 if out.exists():raise ValueError('Output exists; choose a new destination')
 out.mkdir(parents=True);(out/'payload').mkdir();ops=[];blocked=[]
 def add(target,data,kind='file',feature='core',metadata=None):
  rel=Path(target)
  if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe target')
  dst=out/'payload'/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data);before=a.snapshot/rel
  ops.append({'target':target,'payload':'payload/'+target,'before_sha256':sha(before.read_bytes()) if before.is_file() else None,'after_sha256':sha(data),'kind':kind,'feature':feature,**(metadata or {})})
 upstream=a.upstream/'installer/klipper/tltg';local=w/'work/q2-nonmotion-2026-11-20/package/modules'
 for n in NONMOTION+CORE:
  source=local/f'tltg_{n}.py'
  if not source.exists():source=upstream/f'{n}.py'
  add(f'home/qidi/klipper/klippy/extras/tltg_{n}.py',source.read_bytes(),feature=n,metadata={'carried_forward_motion_exception':n=='box_slot_jog'})
 add('home/qidi/klipper/klippy/extras/tltg_filament_catalog.py',(upstream/'filament_catalog.py').read_bytes(),feature='filament_catalog')
 add('home/qidi/klipper/klippy/extras/inventory_rfid_read_guard.py',(w/'work/q2-box-firmware-port/src/inventory_rfid_read_guard.py').read_bytes(),feature='read_guard')
 # Config is rendered from the operator's existing file by the dry-run planner, never embedded in the bundle.
 ops.append({'target':'home/qidi/printer_data/config/printer.cfg','kind':'config_sections','before_sha256':sha((a.snapshot/'home/qidi/printer_data/config/printer.cfg').read_bytes()),'sections':['tltg_'+n for n in CORE+NONMOTION]+['inventory_rfid_read_guard'],'feature':'minimal_include_wiring'})
 # Use upstream guarded source transforms rather than copying another model's host files.
 sys.path.insert(0,str(a.upstream.resolve()));from installer.runtime.errors import InstallerError
 from installer.runtime import moonraker_klippy_apis,moonraker_allowed_services,moonraker_spoolman,moonraker_used_extruders,moonraker_fixes
 for mod,fun in [(moonraker_klippy_apis,'patch_klippy_apis'),(moonraker_allowed_services,'patch_allowed_services'),(moonraker_spoolman,'patch_spoolman'),(moonraker_used_extruders,'patch_used_extruders')]:
  target=mod.FILE.lstrip('/');src=a.snapshot/target
  try:
   new=getattr(mod,fun)(src.read_text());add(target,new.encode(),feature=mod.__name__.rsplit('.',1)[-1])
  except (OSError,ValueError,RuntimeError,InstallerError) as e:blocked.append({'feature':mod.__name__,'reason':str(e)})
 add(moonraker_fixes.MODULE_FILE.lstrip('/'),moonraker_fixes.module_source().encode(),feature='moonraker_runtime_fixes');add(moonraker_fixes.PATH_FILE.lstrip('/'),moonraker_fixes.PATH_CONTENT.encode(),feature='moonraker_runtime_fixes')
 # Complete static web artifacts; no installer or updater entry point is enabled.
 for src,target in [(w/'work/q2-valve-align-26.11.18.1/fluidd/dist','home/qidi/fluidd/q2-bundle-preview'),(w/'work/q2-nonmotion-2026-11-20/ui/dist','home/qidi/valve-oil-ui-q2')]:
  if not (src/'index.html').is_file():raise ValueError('Missing verified web build: '+str(src))
  for f in sorted(src.rglob('*')):
   if f.is_file():add(target+'/'+f.relative_to(src).as_posix(),f.read_bytes(),feature='static_web')
 add('home/qidi/fluidd/index.html',b'<!doctype html><meta charset="utf-8"><script>location.replace("/q2-bundle-preview/index.html"+location.search+location.hash)</script>',feature='web_entry')
 for source,target in [(w/'work/q2-screen-2026-11-20/package/tltg_remote_screen.py','usr/local/lib/tltg_remote_screen.py'),(w/'work/q2-screen-2026-11-20/package/tltg-remote-screen.service','etc/systemd/system/tltg-remote-screen.service'),(w/'work/q2-nonmotion-2026-11-20/package/tltg_status.py','usr/local/lib/tltg_status.py'),(w/'work/q2-nonmotion-2026-11-20/package/tltg-status.service','etc/systemd/system/tltg-status.service')]:add(target,source.read_bytes(),feature='web_backends')
 # Routing is transformed from its current site, preserving camera routes, roots and authorization.
 ops.append({'target':'etc/nginx/sites-available/fluidd','kind':'nginx_routes','before_sha256':sha((a.snapshot/'etc/nginx/sites-available/fluidd').read_bytes()),'feature':'web_routing'})
 for source in [w/'work/q2-screen-2026-11-20/package/screen-routes.conf',w/'work/q2-nonmotion-2026-11-20/package/status-routes.conf',w/'work/q2-nonmotion-2026-11-20/package/ui-routes.conf']:
  shutil.copy2(source,out/source.name)
 # Catalog overlay is data, not a personal spool inventory or replacement of QIDI entries.
 shutil.copy2(upstream/'filament_catalog.py',out/'filament_catalog.py')
 for nozzle in ('0.2','0.4','0.6','0.8'):
  target=f'home/qidi/QIDI_Client/resource/filament_config/filament-{nozzle}.json';ops.append({'target':target,'kind':'catalog_merge','nozzle':nozzle,'before_sha256':sha((a.snapshot/target).read_bytes()),'feature':'catalog_merge'})
 shutil.copytree(a.firmware,out/'firmware')
 shutil.copy2(w/'valve-oil-q2/q2_port/plan.py',out/'plan.py')
 shutil.copy2(a.upstream/'LICENSE',out/'LICENSE');shutil.copy2(a.upstream/'THIRD_PARTY_NOTICES.md',out/'THIRD_PARTY_NOTICES.md')
 # Retain every remaining non-motion recipe for audit without pretending it passed Q2 admission.
 recipes=out/'review-recipes';recipes.mkdir();recipe_names=['addons','addons_cli','addons_service','addons_launcher','auto_update','status_service','cpu_tuning','service_priority','restart_on_exit','moonraker_speedups','zram_swap','rockchip_root_sync']
 for name in recipe_names:
  f=a.upstream/'installer/runtime'/f'{name}.py'
  if f.exists():shutil.copy2(f,recipes/f.name)
 feature_status={'host_and_web':'assembled','box_firmware':'exact reproduced deployed dev1','thr_fifo':'exact input match, new standalone candidate; not flashed','box_mcu_temperature':'standard debug_read verified in emulation; physical sensor untested','addons':'source recipe retained; Q2 privilege/installer integration not enabled','automatic_updates':'blocked by Q2 selective-port guard; no board/update takeover','os_tuning':'review recipe only; no Q2 kernel/IRQ/storage admission bypass','camera':'pre-existing separate fault; experimental power trial is NOT a firmware fix','spoolman':'slot integration only; operator must provide server/spool assignments','movement':'excluded; existing tag-writing slot-jog carried forward unchanged'}
 manifest={'schema':1,'name':'Q2 non-motion preview','version':'2026.11.20-preview1','upstream_commit':UPSTREAM,'supported_soc':'01.01.03.02','mode':'dry-run-only','operations':ops,'blocked_transforms':blocked,'feature_status':feature_status,'excluded_modules':EXCLUDED,'no_live_flash':True};(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
 sums={f.relative_to(out).as_posix():sha(f.read_bytes()) for f in sorted(out.rglob('*')) if f.is_file()};(out/'SHA256SUMS.json').write_text(json.dumps(sums,indent=2));print(json.dumps({'operations':len(ops),'blocked_source_transforms':blocked,'output':str(out)},indent=2))
if __name__=='__main__':main()
