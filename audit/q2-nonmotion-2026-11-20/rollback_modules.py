from pathlib import Path
import hashlib,json,os,subprocess,urllib.request,urllib.parse
r=Path(__file__).resolve().parent;records=json.loads((r/'installed.json').read_text())
def api(p):return json.load(urllib.request.urlopen('http://127.0.0.1:7125/'+p,timeout=10))['result']
s=api('printer/objects/query?print_stats&multi_color_controller')['status'];assert s['print_stats']['state'] in ('standby','complete');t=s['multi_color_controller']['task'];assert not t.get('flow_id') and not t.get('current_step') and not t.get('current_queue') and not t.get('is_paused');assert not any(v==1 for k,v in s['multi_color_controller']['box'].items() if k.endswith('_read_rfid_state'))
for n in api('printer/objects/query?heaters')['status']['heaters']['available_heaters']:assert api('printer/objects/query?'+urllib.parse.quote(n))['status'][n].get('target',0)==0
for n,v in records.items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==v['after'],'Changed after install: '+n
cfg=Path('/home/qidi/printer_data/config/printer.cfg');data=(r/'before/printer.cfg').read_bytes();assert hashlib.sha256(data).hexdigest()==records[str(cfg)]['before']
subprocess.run(['systemctl','--no-ask-password','stop','qidi-client'],check=True);subprocess.run(['systemctl','--no-ask-password','stop','klipper'],check=True)
tmp=cfg.with_name(cfg.name+'.rollback');tmp.write_bytes(data);os.chmod(tmp,cfg.stat().st_mode);os.replace(tmp,cfg)
for n,v in records.items():
 if v['before'] is None:Path(n).unlink()
subprocess.run(['systemctl','--no-ask-password','start','klipper'],check=True);subprocess.run(['systemctl','--no-ask-password','start','qidi-client'],check=True)
print('Non-motion host additions rolled back; camera untouched.')
