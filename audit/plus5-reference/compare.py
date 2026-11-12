from pathlib import Path
import argparse
import csv
import re
import sys

parser = argparse.ArgumentParser(description="Compare local Valve Oil and QIDI snapshots")
parser.add_argument("upstream", type=Path)
parser.add_argument("q2_config", type=Path)
parser.add_argument("plus5_captured_config", type=Path)
args = parser.parse_args()
u = args.upstream.resolve()
q = args.q2_config.resolve()
p=u/'installer/stock/qidi-plus5-defaults/firmwares/01.01.02.01/config'
o = Path(__file__).resolve().parent
sys.path.insert(0,str(u/'installer/runtime/vendor'))
import yaml
sys.path.insert(0, str(u))
from installer.runtime.klipper_cfg import normalized_section_sha256

def section_hash(root, file, name):
 path = root / file
 if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
  return ""
 lines = path.read_text().splitlines(keepends=True)
 start = next((i for i,l in enumerate(lines) if l.strip().casefold() == f"[{name}]".casefold()), None)
 if start is None:
  return ""
 end = next((i for i in range(start+1,len(lines)) if re.match(r"^\[[^]]+\]",lines[i])),len(lines))
 return normalized_section_sha256("".join(lines[start:end]))

def cfg(root):
 out={}
 for f in sorted(root.rglob('*.cfg')):
  if f.is_symlink() or f.name not in ('printer.cfg','box.cfg','timelapse.cfg') and f.parent.name!='klipper-macros-qd':continue
  section=''
  for line in f.read_text(errors='replace').splitlines():
   if line.startswith('#*#'):break
   h=re.fullmatch(r'\[([^]]+)\]\s*',line)
   if h:section=h[1];continue
   m=re.match(r'^([a-zA-Z_][\w-]*)\s*[:=]\s*([^#;]*)',line)
   if m and section:
    key,value=m.groups();value=value.strip()
    if re.search(r'serial|uuid|password|token|secret|device|socket|path',key,re.I):value='<redacted>'
    elif not re.fullmatch(r'[\w\s.!,+@:-]{0,160}',value):value='<expression or path>'
    out[(str(f.relative_to(root)),section,key)]=value
 return out
def write(name,head,rows):
 with (o/name).open('w',newline='') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(head);w.writerows(rows)
a,b=cfg(p),cfg(q)
write('stock-options.csv',['file','section','option','Plus5 stock','Q2 capture','comparison'],[
 (*k,a.get(k,''),b.get(k,''),'same' if k in a and k in b and a[k]==b[k] else 'different' if k in a and k in b else 'Plus5 only at path' if k in a else 'Q2 only at path') for k in sorted(a.keys()|b.keys())])
m=yaml.safe_load((u/'installer/package.yaml').read_text())
rows=[]
for group,items in m['patches'].items():
 for item in items:
  for v in item['variants']:
   if '01.01.02.01' not in v['firmwares']:continue
   key=(item['file'].removeprefix('config/'),item['section'],item.get('option',''))
   rows.append((group,item['id'],*key,v.get('expected',v.get('expected_normalized_sha256')),v.get('desired','remove section'),a.get(key,'') if group == 'set_options' else section_hash(p,*key[:2]),b.get(key,'') if group == 'set_options' else section_hash(q,*key[:2])))
write('plus5-manifest-patches.csv',['operation','id','file','section','option','expected','desired','Plus5 captured value','Q2 same-path value'],rows)
variables={}
for f in sorted((u/'installer/klipper').rglob('*.cfg')):
 if 'max4' in f.parts:continue
 for line in f.read_text().splitlines():
  match=re.match(r'^variable_(\w+):\s*(.*)',line)
  if match:variables[(str(f.relative_to(u)),match[1])]=match[2]
for key,value in sorted(m.get('install',{}).items()):
 if 'variable' in key:print(key,type(value).__name__)
write('valve-oil-macro-variables.csv',['file','variable','upstream value'],[(*k,v) for k,v in variables.items()])
saved={}
for model,root in [('plus5',args.plus5_captured_config),('q2',q)]:
 f=root/'saved_variables.cfg';saved[model]={x.group(1) for l in f.read_text(errors='replace').splitlines() if (x:=re.match(r'^([a-zA-Z_]\w*)\s*=',l))}
write('saved-variable-keys.csv',['key','Plus5 capture','Q2 capture'],[(k,k in saved['plus5'],k in saved['q2']) for k in sorted(saved['plus5']|saved['q2'])])
print(len(a),len(b),len(a.keys()|b.keys()),len(rows),len(variables),len(saved['plus5']|saved['q2']))
