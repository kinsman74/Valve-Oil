"""Offline emulation of the exact candidate bytes; no hardware access."""
import argparse,hashlib,json,struct,sys,zlib
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--upstream',type=Path,required=True);p.add_argument('--q2-port',type=Path,required=True);p.add_argument('--thr-stock',type=Path,required=True);p.add_argument('--firmware',type=Path,required=True);a=p.parse_args()
 sys.path.insert(0,str(a.upstream.resolve()/'scripts'));from check_thr_firmware import check_fifo_execution,emulate_identify
 m=json.loads((a.upstream/'firmware/max4-thr-valve-oil-v1.json').read_text());stock=a.thr_stock.read_bytes();thr=(a.firmware/'q2-thr-valve-oil-fifo.bin').read_bytes();check_fifo_execution(stock,thr,m)
 old=json.loads(zlib.decompress(emulate_identify(stock,m)));new=json.loads(zlib.decompress(emulate_identify(thr,m)));old['version']=new['version'];assert old==new
 from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_MODE_MCLASS,UC_HOOK_CODE
 from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_SP,UC_ARM_REG_LR
 box=(a.firmware/'q2-box-valve-rfid-dev1.bin').read_bytes();original=(a.q2_port/'QD_Q2_BOX_02.03.01.13_20251127.bin').read_bytes();d=json.loads(zlib.decompress(box[0x6efc:]));assert d['commands']['debug_read order=%c addr=%u']==12 and d['responses']['debug_result val=%u']==90
 assert original[0x14ac:0x14f0]==box[0x14ac:0x14f0]
 cases=0
 for addr,value in [(0x1fff7a2c,0x345),(0x1fff7a2e,0x567)]:
  u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS);u.mem_map(0x08000000,0x30000);u.mem_map(0x20000000,0x10000);u.mem_map(0x1fff7000,0x1000);u.mem_write(0x08008000,box);u.mem_write(addr,struct.pack('<H',value));u.mem_write(0x20001000,struct.pack('<II',1,addr));u.reg_write(UC_ARM_REG_R0,0x20001000);u.reg_write(UC_ARM_REG_SP,0x2000ff00);u.reg_write(UC_ARM_REG_LR,0x08020001);captured=[]
  def hook(machine,pc,size,data):
   if pc==0x080083a4:captured.append((machine.reg_read(UC_ARM_REG_R0),machine.reg_read(UC_ARM_REG_R1)));machine.emu_stop()
  u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x080094ad,0x08020000,count=100);assert len(captured)==1 and captured[0][1]==value;assert struct.unpack_from('<H',box,captured[0][0]-0x08008000)[0]==90;cases+=1
 result={'thr_fifo':'all upstream status/buffer cases passed','thr_identify':'version-only dictionary difference','box_standard_debug_read':'unchanged handler and command; both STM32F4 calibration halfwords emulated','box_calibration_cases':cases,'physical_temperature_sensor':'not exercised','physical_new_thr':'not flashed or qualified','mode':'offline-only'};(a.firmware/'emulation-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
