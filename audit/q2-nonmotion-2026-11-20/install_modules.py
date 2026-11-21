from pathlib import Path
import json,hashlib,shutil,os,urllib.request,urllib.parse,subprocess
r=Path(__file__).resolve().parent;h=Path('/home/qidi');cfg=h/'printer_data/config/printer.cfg';extras=h/'klipper/klippy/extras';m=json.loads((r/'expected.json').read_text());names=json.loads((r/'modules.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def api(p):return json.load(urllib.request.urlopen('http://127.0.0.1:7125/'+p,timeout=10))['result']
s=api('printer/objects/query?print_stats&multi_color_controller')['status'];assert s['print_stats']['state'] in ('standby','complete');t=s['multi_color_controller']['task'];assert not t.get('flow_id') and not t.get('current_step') and not t.get('current_queue') and not t.get('is_paused');assert not any(v==1 for k,v in s['multi_color_controller']['box'].items() if k.endswith('_read_rfid_state'))
for n in api('printer/objects/query?heaters')['status']['heaters']['available_heaters']:assert api('printer/objects/query?'+urllib.parse.quote(n))['status'][n].get('target',0)==0
assert sha(cfg)==m['config'];text=cfg.read_text();marker='#*# <---------------------- SAVE_CONFIG';assert marker in text
for n in names:assert '[tltg_'+n+']' not in text
new=text.replace(marker,'\n# Q2 Valve Oil non-motion services, 2026-11-20.\n'+''.join('[tltg_'+n+']\n\n' for n in names)+marker,1);assert text.split(marker,1)[1]==new.split(marker,1)[1]
b=r/'before';assert not b.exists();b.mkdir();shutil.copy2(cfg,b/'printer.cfg');records={}
def replace(p,data):
 mode=p.stat().st_mode if p.exists() else 0o644;tmp=p.with_name(p.name+'.nonmotion-tmp');tmp.write_bytes(data);os.chmod(tmp,mode);os.replace(tmp,p)
installed=[]
try:
 for n,d in m['modules'].items():
  p=extras/n;assert not p.exists();assert sha(r/'modules'/n)==d;replace(p,(r/'modules'/n).read_bytes());installed.append(p);records[str(p)]={'before':None,'after':d}
 replace(cfg,new.encode());records[str(cfg)]={'before':m['config'],'after':sha(cfg)};(r/'installed.json').write_text(json.dumps(records,indent=2))
 subprocess.run(['systemctl','--no-ask-password','stop','qidi-client'],check=True);subprocess.run(['systemctl','--no-ask-password','restart','klipper'],check=True);subprocess.run(['systemctl','--no-ask-password','start','qidi-client'],check=True)
except BaseException:
 replace(cfg,(b/'printer.cfg').read_bytes())
 for p in installed:p.unlink()
 subprocess.run(['systemctl','--no-ask-password','restart','klipper']);subprocess.run(['systemctl','--no-ask-password','start','qidi-client']);raise
print('Installed '+str(len(names))+' non-motion modules; original config backed up. No macros/calibration edited.')
