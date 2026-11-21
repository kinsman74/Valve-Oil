from pathlib import Path
import hashlib,json,os,shutil,subprocess,datetime
r=Path(__file__).resolve().parent;n=Path('/etc/nginx/sites-available/fluidd');server=Path('/usr/local/lib/tltg_status.py');unit=Path('/etc/systemd/system/tltg-status.service');web=Path('/home/qidi/valve-oil-ui-q2');meta=Path('/home/qidi/printer_data/.q2_valve_oil_status.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(n)=='92f2284c44a3c70f1f7c60e2f958a2520c340cadf60c158c661b6bc6d8aba189'
for p in (server,unit,web,meta):assert not p.exists(),'Existing target: '+str(p)
b=r/'web-before';assert not b.exists();b.mkdir();shutil.copy2(n,b/'fluidd-nginx');old=n.read_bytes();text=old.decode();nl='\r\n' if b'\r\n' in old else '\n';anchor=nl+'    location /webcam/ {'+nl;assert text.count(anchor)==1
blocks=(r/'status-routes.conf').read_text()+'\n'+(r/'ui-routes.conf').read_text();text=text.replace(anchor,nl+blocks.replace('\n',nl)+anchor,1)
def replace(p,data):
 tmp=p.with_name(p.name+'.nonmotion-tmp');tmp.write_bytes(data);os.chmod(tmp,p.stat().st_mode if p.exists() else 0o644);os.replace(tmp,p)
try:
 shutil.copytree(r/'web',web)
 for f in (r/'web').rglob('*'):
  if f.is_file():assert sha(f)==sha(web/f.relative_to(r/'web'))
 replace(server,(r/'tltg_status.py').read_bytes());replace(unit,(r/'tltg-status.service').read_bytes());replace(n,text.encode())
 meta.write_text(json.dumps({'schema':1,'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'release':{'installed':'26.11.18.1-q2'},'printer':{'id':'q2','name':'QIDI Q2 selective port'},'pending':[],'boards':[],'run':None},indent=2));os.chmod(meta,0o644)
 subprocess.run(['nginx','-t'],check=True);subprocess.run(['systemctl','daemon-reload'],check=True);subprocess.run(['systemctl','enable','--now','tltg-status'],check=True);subprocess.run(['systemctl','reload','nginx'],check=True)
 (r/'web-installed.json').write_text(json.dumps({str(p):sha(p) for p in (n,server,unit,meta)},indent=2))
except BaseException:
 subprocess.run(['systemctl','disable','--now','tltg-status']);replace(n,old)
 for p in (server,unit,meta):
  if p.exists():p.unlink()
 if web.exists():shutil.rmtree(web)
 subprocess.run(['systemctl','daemon-reload']);subprocess.run(['nginx','-t']);subprocess.run(['systemctl','reload','nginx']);raise
print('Companion UI and Q2 status installed; unsupported updater/enrollment actions disabled.')
