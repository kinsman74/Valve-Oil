from pathlib import Path
import hashlib,json,os,subprocess,shutil
r=Path(__file__).resolve().parent;records=json.loads((r/'web-installed.json').read_text());n=Path('/etc/nginx/sites-available/fluidd');web=Path('/home/qidi/valve-oil-ui-q2')
for p,digest in records.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest,'Changed after install: '+p
for f in (r/'web').rglob('*'):
 if f.is_file():assert hashlib.sha256(f.read_bytes()).digest()==hashlib.sha256((web/f.relative_to(r/'web')).read_bytes()).digest()
subprocess.run(['systemctl','disable','--now','tltg-status'],check=True)
tmp=n.with_name(n.name+'.nonmotion-rollback');tmp.write_bytes((r/'web-before/fluidd-nginx').read_bytes());os.chmod(tmp,n.stat().st_mode);os.replace(tmp,n)
for p in records:
 if p!=str(n):Path(p).unlink()
shutil.rmtree(web);subprocess.run(['systemctl','daemon-reload'],check=True);subprocess.run(['nginx','-t'],check=True);subprocess.run(['systemctl','reload','nginx'],check=True)
print('Companion UI/status removed; screen mirror and original routing preserved.')
