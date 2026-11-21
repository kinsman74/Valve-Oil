from pathlib import Path
import hashlib,json,os,subprocess
r=Path(__file__).resolve().parent;records=json.loads((r/'installed.json').read_text());n=Path('/etc/nginx/sites-available/fluidd')
for name,digest in records.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,'Changed after install: '+name
subprocess.run(['systemctl','disable','--now','tltg-remote-screen.service'],check=True)
tmp=n.with_name(n.name+'.screen-rollback');tmp.write_bytes((r/'before/fluidd-nginx').read_bytes());os.chmod(tmp,n.stat().st_mode);os.replace(tmp,n)
for name in records:
 if name!=str(n):Path(name).unlink()
subprocess.run(['systemctl','daemon-reload'],check=True);subprocess.run(['nginx','-t'],check=True);subprocess.run(['systemctl','reload','nginx'],check=True)
print('Screen mirroring removed; previous web routing restored. Printer and camera services untouched.')
