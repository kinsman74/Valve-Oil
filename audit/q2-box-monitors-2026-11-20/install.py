from pathlib import Path
import hashlib,json,os,shutil,urllib.request,urllib.parse
root=Path(__file__).resolve().parent;home=Path('/home/qidi');cfg=home/'printer_data/config/printer.cfg';extras=home/'klipper/klippy/extras'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def api(path):return json.load(urllib.request.urlopen('http://127.0.0.1:7125/'+path,timeout=15))['result']
s=api('printer/objects/query?print_stats&multi_color_controller&save_variables')['status'];assert s['print_stats']['state'] in ('standby','complete')
t=s['multi_color_controller'].get('task',{});assert not t.get('flow_id') and not t.get('current_step') and not t.get('current_queue') and not t.get('is_paused')
box=s['multi_color_controller'].get('box',{});assert not any(v==1 for k,v in box.items() if k.endswith('_read_rfid_state'))
for name in api('printer/objects/query?heaters')['status']['heaters']['available_heaters']:
 h=api('printer/objects/query?'+urllib.parse.quote(name))['status'][name];assert h.get('target',0)==0, 'Heater active: '+name
expected=json.loads((root/'expected.json').read_text());assert sha(cfg)==expected['printer_sha256']
text=cfg.read_text();names=('box485_monitor','box_link_monitor','box_slot_jog')
for n in names:assert '[tltg_'+n+']' not in text
marker='#*# <---------------------- SAVE_CONFIG';assert marker in text
addition='\n# Q2 Valve Oil Box monitoring and tag-writing rotation, 2026-11-20.\n'+''.join('[tltg_'+n+']\n\n' for n in names)
new=text.replace(marker,addition+marker,1)
assert new.split(marker,1)[1]==text.split(marker,1)[1]
before=root/'before';assert not before.exists();before.mkdir();shutil.copy2(cfg,before/'printer.cfg');shutil.copy2(home/'printer_data/config/saved_variables.cfg',before/'saved_variables.cfg')
records={};done=[]
def replace(p,data):
 st=p.stat() if p.exists() else None;tmp=p.with_name(p.name+'.q2-monitor-tmp');tmp.write_bytes(data);os.chmod(tmp,st.st_mode if st else 0o644);os.replace(tmp,p)
try:
 for n,digest in expected['modules'].items():
  source=root/n;assert sha(source)==digest;dest=extras/n
  if dest.exists():shutil.copy2(dest,before/n)
  records[n]={'before':sha(dest) if dest.exists() else None,'after':digest};replace(dest,source.read_bytes());done.append(dest)
 replace(cfg,new.encode());done.append(cfg)
 request=urllib.request.Request('http://127.0.0.1:7125/printer/gcode/script',data=json.dumps({'script':'SAVE_VARIABLE VARIABLE=tltg_box_link_monitor VALUE=1'}).encode(),headers={'Content-Type':'application/json'})
 response=json.load(urllib.request.urlopen(request,timeout=20));assert 'error' not in response,response
 for n,digest in expected['modules'].items():assert sha(extras/n)==digest
 records['printer.cfg']={'before':expected['printer_sha256'],'after':sha(cfg)}
 (root/'installed.json').write_text(json.dumps({'files':records,'prior_link_monitor':s['save_variables']['variables'].get('tltg_box_link_monitor'),'upstream':'fea34e996f1ab64c646dd02846d1bb47ad93c272'},indent=2))
except BaseException:
 for p in reversed(done):
  b=before/('printer.cfg' if p==cfg else p.name)
  if b.exists():replace(p,b.read_bytes())
  else:p.unlink()
 raise
print('Installed three modules, link monitor enabled; exact originals saved in '+str(before)+'. Reboot required.')
