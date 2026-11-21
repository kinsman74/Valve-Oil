import hashlib,json,os,shutil,subprocess,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parent
home=Path('/home/qidi')
manifest=json.loads((root/'manifest.json').read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def api(path): return json.load(urllib.request.urlopen('http://127.0.0.1:7125/'+path,timeout=10))['result']
status=api('printer/objects/query?print_stats&multi_color_controller&toolhead')['status']
assert status['print_stats']['state']=='standby', 'Printer not idle'
task=status['multi_color_controller'].get('task',{})
assert not task.get('flow_id') and not task.get('current_queue') and not task.get('current_step') and not task.get('is_paused'), 'Box task active'
heaters=api('printer/objects/query?heaters')['status']['heaters']['available_heaters']
for name in heaters:
 h=api('printer/objects/query?'+urllib.parse.quote(name))['status'][name]
 assert h.get('target',0)==0, 'Heater active: '+name
before=root/'before';assert not before.exists(), 'Already applied'
for name,record in manifest.items(): assert sha(home/name)==record['before'], 'Changed since snapshot: '+name
cfg=home/'printer_data/config/printer.cfg'; guard=home/'klipper/klippy/extras/inventory_rfid_read_guard.py'
unchanged={str(p):sha(p) for p in (cfg,guard)}
(root/'preflight.json').write_text(json.dumps({'status':status,'unchanged':unchanged},indent=2))
for name in manifest:
 dest=before/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(home/name,dest)
web=home/'fluidd/q2-valve-26.11.18.1';assert not web.exists(), 'Web target exists'
shutil.copytree(root/'web',web)
for f in (root/'web').rglob('*'):
 if f.is_file(): assert sha(f)==sha(web/f.relative_to(root/'web'))
def replace(dest,source):
 st=dest.stat();tmp=dest.with_name(dest.name+'.q2-align-tmp');shutil.copyfile(source,tmp);os.chmod(tmp,st.st_mode);os.chown(tmp,st.st_uid,st.st_gid);os.replace(tmp,dest)
def services(action):
 for service in (('qidi-client','klipper') if action=='stop' else ('klipper','qidi-client')):subprocess.run(['systemctl','--no-ask-password',action,service+'.service'],check=True)
changed=[]
try:
 services('stop')
 for name in manifest:
  if name=='fluidd/index.html':continue
  replace(home/name,root/name);changed.append(name);assert sha(home/name)==manifest[name]['after']
 entry=root/'entry.html';entry.write_text("<!doctype html><meta charset=utf-8><title>Q2 Valve Oil</title><script>location.replace('/q2-valve-26.11.18.1/index.html'+location.search+location.hash)</script><a href='/q2-valve-26.11.18.1/index.html'>Open Q2 Valve Oil</a>")
 replace(home/'fluidd/index.html',entry);changed.append('fluidd/index.html')
 for name,digest in unchanged.items():assert sha(Path(name))==digest
 (root/'installed.json').write_text(json.dumps({name:sha(home/name) for name in manifest},indent=2))
 services('start')
except BaseException:
 for name in reversed(changed):replace(home/name,before/name)
 services('start')
 raise
print('Installed new reader/catalog/web; stock config and read guard unchanged. Backup: '+str(before))
