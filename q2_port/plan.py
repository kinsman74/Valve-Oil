"""Read-only Q2 package planner. This program cannot install or flash anything."""
import argparse,ast,hashlib,json,re
from pathlib import Path

def sha(data):return hashlib.sha256(data).hexdigest()
def safe(root,name):
 p=Path(name)
 if p.is_absolute() or '..' in p.parts or not p.parts:raise ValueError('Unsafe relative path: '+name)
 root=root.resolve();dest=root/p
 for part in [dest,*dest.parents]:
  if part==root:break
  if part.is_symlink():raise ValueError('Symlink target refused: '+name)
 if not dest.resolve().is_relative_to(root):raise ValueError('Escaping path: '+name)
 return dest

def overlay_config(data,sections):
 s=data.decode();marker='#*# <---------------------- SAVE_CONFIG'
 if marker not in s:raise ValueError('Missing calibration marker')
 found=re.findall(r'^\[([^\]\r\n]+)\]',s,re.M)
 if len(found)!=len(set(found)):raise ValueError('Duplicate config section')
 missing=[name for name in sections if name not in found]
 if not missing:return data
 newline='\r\n' if b'\r\n' in data else '\n';block=newline+'# Q2 non-motion bundle sections'+newline+''.join('['+n+']'+newline+newline for n in missing)
 result=s.replace(marker,block+marker,1).encode()
 if result.decode().split(marker,1)[1]!=s.split(marker,1)[1]:raise ValueError('Calibration changed')
 return result

def desired(bundle,op,before):
 kind=op['kind']
 if kind=='file':
  data=safe(bundle,op['payload']).read_bytes()
  if sha(data)!=op['after_sha256']:raise ValueError('Corrupt payload: '+op['payload'])
  return data
 if kind=='config_sections':return overlay_config(before,op['sections'])
 if kind=='nginx_routes':
  text=before.decode();newline='\r\n' if b'\r\n' in before else '\n'
  for name in ('screen-routes.conf','status-routes.conf','ui-routes.conf'):
   block=safe(bundle,name).read_text();start=block.splitlines()[0].strip();end=block.splitlines()[-1].strip();pattern=r'^[ \t]*'+re.escape(start)+r'\r?\n.*?^[ \t]*'+re.escape(end)+r'\r?\n';matches=list(re.finditer(pattern,text,re.M|re.S))
   if len(matches)>1:raise ValueError('Ambiguous managed nginx block')
   replacement=block.replace('\n',newline)
   if matches:text=text[:matches[0].start()]+replacement+text[matches[0].end():]
   else:
    anchor='    location /webcam/ {'
    if text.count(anchor)!=1:raise ValueError('Unknown nginx route structure')
    text=text.replace(anchor,replacement+newline+anchor,1)
  return text.encode()
 if kind=='catalog_merge':
  tree=ast.parse(safe(bundle,'filament_catalog.py').read_text());assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CATALOG' for t in n.targets));literal=assignment.value.args[0];
  if not isinstance(literal,ast.Constant) or not isinstance(literal.value,str):raise ValueError('Catalog must contain literal JSON')
  catalog=json.loads(literal.value);entries=json.loads(before);used={e.get('filament_id') for e in entries.values() if isinstance(e,dict)};new={n:dict(i['entry']) for n,i in catalog['filaments'].items() if op['nozzle'] in i['nozzles'] and n not in entries and i['entry']['filament_id'] not in used}
  if not new:return before
  return (json.dumps({**entries,**new},ensure_ascii=False,indent=2)+'\n').encode()
 raise ValueError('Unknown operation type: '+kind)

def plan(bundle,snapshot):
 sums=json.loads((bundle/'SHA256SUMS.json').read_text())
 actual={p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file() and p.name!='SHA256SUMS.json'}
 if actual!=set(sums):raise ValueError('Bundle file inventory mismatch')
 for name,digest in sums.items():
  if sha(safe(bundle,name).read_bytes())!=digest:raise ValueError('Bundle checksum mismatch: '+name)
 m=json.loads((bundle/'manifest.json').read_text());fw=json.loads(safe(snapshot,'home/qidi/update/firmware_manifest.json').read_text())
 if fw.get('SOC',{}).get('version')!=m['supported_soc']:raise ValueError('Unsupported SOC version')
 if 'Q2' not in fw.get('SOC',{}).get('file',''):raise ValueError('Wrong printer model')
 actions=[];seen=set()
 for op in m['operations']:
  if op['target'] in seen:raise ValueError('Duplicate operation target')
  seen.add(op['target']);p=safe(snapshot,op['target']);before=p.read_bytes() if p.exists() else b'';result=desired(bundle,op,before)
  # Desired bytes are accepted for repeat runs; unknown divergent preimages fail closed.
  state='unchanged' if p.exists() and before==result else 'create' if not p.exists() else 'replace'
  if state!='unchanged' and (sha(before) if p.exists() else None)!=op.get('before_sha256'):raise ValueError('Target drift: '+op['target'])
  actions.append({'target':op['target'],'action':state,'before_sha256':sha(before) if p.exists() else None,'after_sha256':sha(result),'feature':op['feature']})
 return {'mode':'dry-run','read_only':True,'model':'Q2','soc':m['supported_soc'],'upstream_commit':m['upstream_commit'],'actions':actions,'counts':{k:sum(a['action']==k for a in actions) for k in ('create','replace','unchanged')},'blocked_source_transforms':m['blocked_transforms'],'feature_status':m['feature_status'],'live_flash':'not attempted; requires idle physical board admission and verified rollback','complete_upstream_parity':False}

def main():
 p=argparse.ArgumentParser();p.add_argument('--dry-run',action='store_true',required=True);p.add_argument('--bundle',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--snapshot',type=Path,required=True);a=p.parse_args();print(json.dumps(plan(a.bundle,a.snapshot),indent=2))
if __name__=='__main__':main()
