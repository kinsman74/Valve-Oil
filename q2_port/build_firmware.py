"""Offline Q2 firmware build. No device access or flashing operations."""
import argparse,hashlib,importlib.util,json,shutil,subprocess,sys,tempfile
from pathlib import Path

def sha(data): return hashlib.sha256(data).hexdigest()
def build(a):
 sys.path.insert(0,str(a.upstream.resolve()/'scripts'));from build_thr_firmware import patch_thr
 m=json.loads((a.upstream/'firmware/max4-thr-valve-oil-v1.json').read_text());stock=a.thr.read_bytes();assert sha(stock)==m['thr']['stock_sha256'];thr=patch_thr(stock,m);assert sha(thr)==m['thr']['patched_sha256']
 (a.output/'q2-thr-valve-oil-fifo.bin').write_bytes(thr)
 with tempfile.TemporaryDirectory() as td:
  t=Path(td);shutil.copy2(a.q2_port/'build.py',t/'build.py');shutil.copytree(a.q2_port/'src',t/'src');shutil.copy2(a.q2_port/'QD_Q2_BOX_02.03.01.13_20251127.bin',t/'QD_Q2_BOX_02.03.01.13_20251127.bin');subprocess.run([sys.executable,'-B',str(t/'build.py')],check=True)
  box=(t/'q2-box-valve-rfid-dev1.bin').read_bytes();assert sha(box)=='50e1b2d76a64d3ef7a0c8f79eb4a84be9eafd93cb0912e55d994c8245d93f903';(a.output/'q2-box-valve-rfid-dev1.bin').write_bytes(box)
  report=json.loads((t/'build-report.json').read_text());report['status']='reproduced existing Q2 dev1; hardware readback/Anycubic evidence recorded separately';
  for patch in report['patches']:
   patch['description']=patch['description'].replace('Retire debug handler','Retire legacy RFID diagnostic handler')
  (a.output/'box-build-report.json').write_text(json.dumps(report,indent=2))
 (a.output/'firmware.json').write_text(json.dumps({'mode':'offline-build-only','upstream_commit':'fea34e996f1ab64c646dd02846d1bb47ad93c272','box':{'stock_sha256':report['stock_sha256'],'output_sha256':sha(box),'size':len(box),'scope':'Q2 adaptation of Tuba RFID transport; host guard supplies zero/malformed/conflict handling'},'thr':{'stock_sha256':sha(stock),'output_sha256':sha(thr),'size':len(thr),'scope':'Exact Q2 cached image matches upstream Max4/Plus5 THR preimage; sensor FIFO fix only'},'mainboard':'stock, no motion/closed-loop patch','shutdown':'Q2 dispatcher retained; MCB-specific patch not applicable','deployment':'Not authorized by this dry run; new THR needs installed-image/bootloader readback and recovery qualification while idle'},indent=2))
 print('Offline Box and THR images built and hash-verified.')

def main():
 p=argparse.ArgumentParser();p.add_argument('--upstream',type=Path,required=True);p.add_argument('--q2-port',type=Path,required=True);p.add_argument('--thr',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 destination=a.output
 if destination.exists():raise ValueError('Output exists; choose a new destination')
 destination.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='.q2-firmware-',dir=destination.parent) as temporary:
  a.output=Path(temporary)/'payload';a.output.mkdir();build(a);a.output.rename(destination)
if __name__=='__main__':main()
