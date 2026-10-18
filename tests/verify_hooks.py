"""Execute the actual linked PS2rd syscall trampolines against reset/DMA cases.
Does not emulate EE kernel syscalls or a complete console.
"""
from pathlib import Path
import struct,sys

from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn.mips_const import *
w=Path(__file__).parent
target=Path(sys.argv[1]) if len(sys.argv)>1 else w.parent/'build/resident.elf'
d=target.read_bytes()
shoff=struct.unpack_from('<I',d,32)[0];shsize,shnum,shstr=struct.unpack_from('<HHH',d,46)
sections=[struct.unpack_from('<10I',d,shoff+i*shsize) for i in range(shnum)]
symbols={}
for s in sections:
 if s[1]!=2:continue
 st=sections[s[6]];strings=d[st[4]:st[4]+st[5]]
 for o in range(s[4],s[4]+s[5],s[9]):
  name,addr,size,info,other,index=struct.unpack_from('<IIIBBH',d,o)
  if name:symbols[strings[name:].split(b'\0')[0].decode()]=addr
phoff=struct.unpack_from('<I',d,28)[0];phsize,phnum=struct.unpack_from('<HH',d,42)
segments=[struct.unpack_from('<8I',d,phoff+i*phsize) for i in range(phnum)]
for attr,size,psize,cid,match in [(0x44,0x68,0x68,0x80000003,True),(0,0x68,0x68,0x80000003,False),(0x44,0x40,0x68,0x80000003,False),(0x44,0x68,0x67,0x80000003,False),(0x44,0x68,0x68,0x8000000a,False)]:
 uc=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);uc.mem_map(0x80000,0x80000);uc.mem_map(0x180000,0x80000)
 for p in segments:
  if p[0]==1:uc.mem_write(p[2],d[p[1]:p[1]+p[4]])
 stack=0x180000;dma=0x190000;packet=0x191000;old=0x1a0000;ret=0x1e0000
 uc.mem_write(symbols['OldSifSetDma'],struct.pack('<I',old))
 uc.mem_write(dma,struct.pack('<4I',packet,0,size,attr));uc.mem_write(packet,struct.pack('<4I',psize,0,cid,0))
 oldcalls=[]
 def hook(u,pc,length,user):
  if pc==old:oldcalls.append(pc);u.reg_write(UC_MIPS_REG_PC,u.reg_read(UC_MIPS_REG_RA))
 uc.hook_add(UC_HOOK_CODE,hook)
 uc.reg_write(UC_MIPS_REG_SP,stack);uc.reg_write(UC_MIPS_REG_A0,dma);uc.reg_write(UC_MIPS_REG_A1,1);uc.reg_write(UC_MIPS_REG_RA,ret)
 uc.emu_start(symbols['HookSifSetDma'],ret,count=100)
 epc=struct.unpack('<I',uc.mem_read(stack+8,4))[0]
 assert uc.reg_read(UC_MIPS_REG_PC)==ret
 assert (epc==symbols['NewSifSetDma'])==match
 assert bool(oldcalls)==(not match)
 print('PASS DMA classifier',hex(attr),hex(size),hex(psize),hex(cid),'reset' if match else 'forwarded unchanged')
 # Register trampoline always changes saved EPC to its user-context helper.
 uc.mem_write(stack+8,bytes(4));uc.reg_write(UC_MIPS_REG_RA,ret)
 uc.emu_start(symbols['HookSifSetReg'],ret,count=30)
 assert struct.unpack('<I',uc.mem_read(stack+8,4))[0]==symbols['NewSifSetReg']
print('PASS actual linked DMA and register trampolines')
