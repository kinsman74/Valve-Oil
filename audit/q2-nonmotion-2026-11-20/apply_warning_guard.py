import json,hashlib,os,subprocess,urllib.request
from pathlib import Path
r=Path(__file__).parent;p=Path('/home/qidi/klipper/klippy/extras/tltg_printer_warnings.py');m=json.loads((r/'installed.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=json.load(urllib.request.urlopen('http://127.0.0.1:7125/printer/objects/query?print_stats&multi_color_controller'))['result']['status'];assert s['print_stats']['state']=='standby';assert not s['multi_color_controller']['task'].get('flow_id');assert not any(v==1 for k,v in s['multi_color_controller']['box'].items() if k.endswith('_read_rfid_state'));assert sha(p)==m[str(p)]['after']
tmp=p.with_name(p.name+'.q2compat');tmp.write_bytes((r/'q2_printer_warnings.py').read_bytes());os.chmod(tmp,p.stat().st_mode);os.replace(tmp,p);m[str(p)]['after']=sha(p);(r/'installed.json').write_text(json.dumps(m,indent=2))
subprocess.run(['systemctl','--no-ask-password','stop','qidi-client'],check=True);subprocess.run(['systemctl','--no-ask-password','restart','klipper'],check=True);subprocess.run(['systemctl','--no-ask-password','start','qidi-client'],check=True)
print('Q2 warning gate installed; original warning wording unchanged and no motion macros introduced.')
