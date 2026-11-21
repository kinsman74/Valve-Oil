from pathlib import Path
import hashlib,json,shutil,os,subprocess
r=Path(__file__).resolve().parent;n=Path('/etc/nginx/sites-available/fluidd');server=Path('/usr/local/lib/tltg_remote_screen.py');unit=Path('/etc/systemd/system/tltg-remote-screen.service')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(n)=='688e033394f2ccf749df72be7be58edd5712f2e887d24f72f59b0b22534da785'
assert not server.exists() and not unit.exists()
assert not (r/'before').exists();(r/'before').mkdir();shutil.copy2(n,r/'before/fluidd-nginx')
raw=n.read_bytes();newline='\r\n' if b'\r\n' in raw else '\n';s=raw.decode();anchor=newline+'    location /webcam/ {'+newline;assert s.count(anchor)==1
block=(r/'screen-routes.conf').read_text().replace('\n',newline);new=s.replace(anchor,newline+block+anchor,1)
def replace(p,data):
 tmp=p.with_name(p.name+'.q2-screen-tmp');tmp.write_bytes(data);os.chmod(tmp,p.stat().st_mode if p.exists() else 0o644);os.replace(tmp,p)
try:
 replace(server,(r/'tltg_remote_screen.py').read_bytes());replace(unit,(r/'tltg-remote-screen.service').read_bytes());replace(n,new.encode());subprocess.run(['nginx','-t'],check=True)
 subprocess.run(['systemctl','daemon-reload'],check=True);subprocess.run(['systemctl','enable','--now','tltg-remote-screen.service'],check=True);subprocess.run(['systemctl','reload','nginx'],check=True)
 (r/'installed.json').write_text(json.dumps({str(p):sha(p) for p in (n,server,unit)},indent=2))
except BaseException:
 subprocess.run(['systemctl','disable','--now','tltg-remote-screen.service'])
 replace(n,raw)
 for p in (server,unit):
  if p.exists():p.unlink()
 subprocess.run(['systemctl','daemon-reload']);subprocess.run(['nginx','-t']);subprocess.run(['systemctl','reload','nginx']);raise
print('Screen mirror installed, Moonraker authorization preserved. Printer/camera services untouched.')
