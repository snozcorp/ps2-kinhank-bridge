#!/usr/bin/env python3
"""Check release integrity and compiled artifact boundaries; no console emulation."""
import hashlib
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = '0af4a5b34230c73bf2f733a1634bf8659cacab1e0a8914e0a5c03d761c6f5079'

def elf(path):
    data = path.read_bytes()
    assert data[:6] == b'\x7fELF\x01\x01', path
    po = struct.unpack_from('<I',data,28)[0]
    ps,pn = struct.unpack_from('<HH',data,42)
    segments = [struct.unpack_from('<8I',data,po+i*ps) for i in range(pn)]
    so = struct.unpack_from('<I',data,32)[0]
    ss,sn,ns = struct.unpack_from('<HHH',data,46)
    sections = [struct.unpack_from('<10I',data,so+i*ss) for i in range(sn)]
    symbols = {}
    for s in sections:
        if s[1] != 2:
            continue
        st = sections[s[6]]
        names = data[st[4]:st[4]+st[5]]
        for off in range(s[4],s[4]+s[5],s[9]):
            n,a,size,*_ = struct.unpack_from('<IIIBBH',data,off)
            if n:
                symbols[names[n:].split(b'\0')[0].decode()] = (a,size)
    def content(name):
        address,size = symbols[name]
        for p in segments:
            if p[0]==1 and p[2]<=address and address+size<=p[2]+p[4]:
                return data[p[1]+address-p[2]:p[1]+address-p[2]+size]
        raise AssertionError(f'No file data for {name}')
    return data,segments,sections,symbols,content

def check_launcher(path):
    data,segments,_,symbols,content = elf(path)
    assert all(p[2]>=0x100000 for p in segments if p[0]==1)
    assert struct.unpack_from('<I',data,24)[0] == symbols['checked_entry'][0]
    resident = content('resident_elf')
    entry = struct.unpack('<I',content('resident_main'))[0]
    assert struct.unpack_from('<I',resident,24)[0] == entry
    po = struct.unpack_from('<I',resident,28)[0]
    ps,pn = struct.unpack_from('<HH',resident,42)
    loads = [struct.unpack_from('<8I',resident,po+i*ps) for i in range(pn)]
    loads = [p for p in loads if p[0]==1]
    assert loads and all(0x90000<=p[2] and p[2]+p[5]+32768<=0x100000 for p in loads)
    assert any(p[2]<=entry<p[2]+p[4] for p in loads)
    for p in loads:
        assert p[4]<=p[5] and p[1]+p[4]<=len(resident)
    print('PASS',path.name,': frontend/resident entry, reserved memory and heap bounds')

def main():
    release = ROOT/'releases/v11/DQ8-KINHANK-V11.ELF'
    assert hashlib.sha256(release.read_bytes()).hexdigest() == EXPECTED
    assert (ROOT/'releases/v11/SHA256SUMS').read_text().split()[0] == EXPECTED
    print('PASS original physically tested release SHA256')
    check_launcher(release)
    rebuilt = ROOT/'build/DQ8-KINHANK-V11.ELF'
    if not rebuilt.exists():
        print('No local build yet; release checks complete.')
        return
    check_launcher(rebuilt)
    _,_,_,_,fc = elf(rebuilt)
    resident,segments,_,_,rc = elf(ROOT/'build/resident.elf')
    embedded = fc('resident_elf')
    for p in segments:
        if p[0]==1:
            assert embedded[p[1]:p[1]+p[4]] == resident[p[1]:p[1]+p[4]]
    for name in ('pademu','xbox360usb'):
        path = ROOT/f'build/iop/{name}/{name}.irx'
        data,_,sections,_,_ = elf(path)
        for section in sections:
            if section[1]==9:
                assert sections[section[7]][2]&2, f'{name}: relocation targets a non-runtime section'
        assert rc(name.replace('xbox360usb','xbox')+'_data') == data
        print('PASS',name,': embedded module and runtime relocation targets')
    identical = rebuilt.read_bytes() == release.read_bytes()
    print('Rebuild is byte-identical to tested V11.' if identical else 'Rebuild differs from tested V11; hardware compatibility is not established by these checks.')
    print('These checks do not emulate the EE kernel, IOP, USB receiver or disc boot.')

if __name__ == '__main__':
    main()
