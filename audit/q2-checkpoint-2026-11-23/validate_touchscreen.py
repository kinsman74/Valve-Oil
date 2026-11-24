from pathlib import Path
import hashlib,json
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm64_const import *
import argparse
parser=argparse.ArgumentParser(description='Offline Q2/Plus5 touchscreen comparison and ARM64 emulation; no printer access')
parser.add_argument('--q2-stock',type=Path,required=True)
parser.add_argument('--plus5-stock',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args()
r=args.output_dir;r.mkdir(parents=True,exist_ok=True)
q=args.q2_stock.read_bytes();p=args.plus5_stock.read_bytes()
assert hashlib.sha256(q).hexdigest()=='c222bb9c77df6fe714e974f915834841be96c291bb75d44cd6f4d371e174f423'
assert hashlib.sha256(p).hexdigest()=='6c09a58a636427d468b77b78149e5305f0b1182e785a0abff67aec53b3aeb855'
d=Cs(CS_ARCH_ARM64,CS_MODE_ARM);sites=[(0x227078,0x226518,0x227060,0x2270bc),(0x227220,0x2266c0,0x22720c,0x227264)]
# Compare complete length/compare/result sequences with the reviewed Plus5 implementation.
comparisons=[]
for qo,po,start,end in sites:
 a=list(d.disasm(q[start:end+4],start));ps=po-(qo-start);b=list(d.disasm(p[ps:ps+(end-start+4)],ps));assert len(a)==len(b)
 for x,y in zip(a,b):
  assert x.mnemonic==y.mnemonic,(hex(x.address),x.mnemonic,y.mnemonic)
  if x.mnemonic in ['bl','b','b.eq','b.ne','cbz']:
   # Register operands and relative targets remain identical, except external PLT relocation.
   if x.mnemonic!='bl':assert x.bytes==y.bytes,(hex(x.address),'branch encoding')
  else:assert x.bytes==y.bytes,(hex(x.address),x.op_str,y.op_str)
 comparisons.append({'q2_offset':hex(qo),'plus5_offset':hex(po),'instructions':len(a)})
patched=bytearray(q)
for qo,*_ in sites:
 assert patched[qo:qo+4]==bytes.fromhex('40020054');patched[qo:qo+4]=bytes.fromhex('49020054')
# Execute actual AArch64 length checks, compare calls, and return paths.
cases=[('02.02.01.08','02.02.01.08'),('02.02.01.08','02.02.01.08-valve-oil.1'),('02.01.01.09','02.01.01.09'),('02.01.01.09','02.01.01.10-valve-oil.1'),('02.02.01.08','02.02'),('02.02.01.08','03.02.01.08-valve-oil.1'),('02.02.01.08','02.02.01.07'),('02.02.01.08','02.02.01.08x'),('02.02.01.08','')]
results=[]
for changed,blob in [(False,q),(True,patched)]:
 for site,(_,_,start,end) in enumerate(sites):
  for manifest,reported in cases:
   u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0x220000,0x10000);u.mem_write(0x220000,bytes(blob[0x220000:0x230000]));u.mem_map(0x49000,0x1000);u.mem_map(0x2000000,0x10000);sp=0x2001000;a=0x2002000;b=0x2003000
   u.reg_write(UC_ARM64_REG_SP,sp);u.reg_write(UC_ARM64_REG_X20,a);u.reg_write(UC_ARM64_REG_X21,b)
   u.mem_write(sp+0x30,a.to_bytes(8,'little')+len(reported).to_bytes(8,'little'));u.mem_write(sp+0x50,b.to_bytes(8,'little')+len(manifest).to_bytes(8,'little'));u.mem_write(a,reported.encode()+b'\0');u.mem_write(b,manifest.encode()+b'\0')
   def hook(uc,address,size,data):
    if address==end:uc.emu_stop()
    elif address==0x49c00:
     x0=uc.reg_read(UC_ARM64_REG_X0);x1=uc.reg_read(UC_ARM64_REG_X1);n=uc.reg_read(UC_ARM64_REG_X2);v=0 if uc.mem_read(x0,n)==uc.mem_read(x1,n) else 1;uc.reg_write(UC_ARM64_REG_X0,v);uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_X30))
   u.hook_add(UC_HOOK_CODE,hook);u.emu_start(start,0x230000,count=100);got=u.reg_read(UC_ARM64_REG_X0)
   match=reported.startswith(manifest) if changed else reported==manifest
   expected=int(not match) if site==0 else int(match)
   if not manifest:expected=0
   assert got==expected,(changed,site,manifest,reported,got,expected)
   results.append({'patched':changed,'check':'show' if site==0 else 'clear','manifest':manifest,'reported':reported,'result':got})
changes=[i for i,(a,b) in enumerate(zip(q,patched)) if a!=b];assert changes==[0x227078,0x227220]
out={'stock_sha256':hashlib.sha256(q).hexdigest(),'patched_sha256':hashlib.sha256(patched).hexdigest(),'size':len(q),'changed_byte_offsets':[hex(x) for x in changes],'reference_comparisons':comparisons,'emulated_cases':len(results),'results':results};(r/'validation.json').write_text(json.dumps(out,indent=2));(r/'qidiclient.patched').write_bytes(patched);print(json.dumps({k:v for k,v in out.items() if k!='results'},indent=2))
