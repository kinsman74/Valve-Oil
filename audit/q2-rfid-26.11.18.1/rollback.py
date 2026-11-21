import hashlib,json,os,shutil,subprocess,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parent;home=Path('/home/qidi')
s=json.load(urllib.request.urlopen('http://127.0.0.1:7125/printer/objects/query?print_stats&multi_color_controller'))['result']['status']
assert s['print_stats']['state']=='standby'
t=s['multi_color_controller'].get('task',{});assert not t.get('flow_id') and not t.get('current_step') and not t.get('current_queue') and not t.get('is_paused')
box=s['multi_color_controller'].get('box',{})
assert not any(v==1 for k,v in box.items() if k.endswith('_read_rfid_state')), 'RFID scan active'
heaters=json.load(urllib.request.urlopen('http://127.0.0.1:7125/printer/objects/query?heaters'))['result']['status']['heaters']['available_heaters']
for name in heaters:
 h=json.load(urllib.request.urlopen('http://127.0.0.1:7125/printer/objects/query?'+urllib.parse.quote(name)))['result']['status'][name]
 assert h.get('target',0)==0, 'Heater active: '+name
manifest=json.loads((root/'manifest.json').read_text());installed=json.loads((root/'installed.json').read_text())
for n,d in installed.items(): assert hashlib.sha256((home/n).read_bytes()).hexdigest()==d, 'Changed after install: '+n
for n,r in manifest.items(): assert hashlib.sha256((root/'before'/n).read_bytes()).hexdigest()==r['before']
for service in ('qidi-client','klipper'):subprocess.run(['systemctl','--no-ask-password','stop',service+'.service'],check=True)
for n in manifest:
 p=home/n;st=p.stat();tmp=p.with_name(p.name+'.rollback-tmp');shutil.copyfile(root/'before'/n,tmp);os.chmod(tmp,st.st_mode);os.chown(tmp,st.st_uid,st.st_gid);os.replace(tmp,p)
for service in ('klipper','qidi-client'):subprocess.run(['systemctl','--no-ask-password','start',service+'.service'],check=True)
print('Previous reader, catalogs and web entry restored')
