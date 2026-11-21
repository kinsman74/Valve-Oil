from pathlib import Path
import hashlib,json,os,urllib.request
r=Path(__file__).resolve().parent;h=Path('/home/qidi');records=json.loads((r/'installed.json').read_text())
s=json.load(urllib.request.urlopen('http://127.0.0.1:7125/printer/objects/query?print_stats&multi_color_controller'))['result']['status'];assert s['print_stats']['state'] in ('standby','complete');t=s['multi_color_controller'].get('task',{});assert not t.get('flow_id') and not t.get('current_step') and not t.get('current_queue') and not t.get('is_paused');assert not any(v==1 for k,v in s['multi_color_controller'].get('box',{}).items() if k.endswith('_read_rfid_state'))
for n,v in records['files'].items():
 p=h/('printer_data/config/printer.cfg' if n=='printer.cfg' else 'klipper/klippy/extras/'+n);assert hashlib.sha256(p.read_bytes()).hexdigest()==v['after'], 'Changed since install: '+n
for n,v in records['files'].items():
 p=h/('printer_data/config/printer.cfg' if n=='printer.cfg' else 'klipper/klippy/extras/'+n)
 if v['before'] is None:p.unlink()
 else:
  data=(r/'before'/n).read_bytes();assert hashlib.sha256(data).hexdigest()==v['before'];tmp=p.with_name(p.name+'.rollback-tmp');tmp.write_bytes(data);os.chmod(tmp,p.stat().st_mode);os.replace(tmp,p)
print('Previous configuration/modules restored. Reboot to activate; saved link-monitor flag is inert without its module.')
