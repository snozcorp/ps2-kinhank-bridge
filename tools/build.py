#!/usr/bin/env python3
"""Build the V11 launcher from checked-in sources and an installed ps2dev SDK."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'
TESTED_USBD = '79d7e20f18801233fc0b8ccde42e784c263c0506c60343f5ea7ca83b02e05c05'

def run(args):
    subprocess.run([str(x) for x in args], check=True)

def tool(name, folder):
    for suffix in ('', '.exe'):
        candidate = folder / (name + suffix)
        if candidate.is_file():
            return candidate
    found = shutil.which(name)
    if found:
        return Path(found)
    raise SystemExit(f'Missing tool {name}; install ps2dev and set PS2DEV/PS2SDK.')

def build_iop(name, folder, sources, sdk, dev):
    out = BUILD / 'iop' / name
    out.mkdir(parents=True, exist_ok=True)
    gcc = tool('mipsel-none-elf-gcc', dev / 'iop/bin')
    flags = ['-D_IOP', '-G0', '-Os', '-fno-builtin', '-msoft-float',
             '-mno-explicit-relocs', '-fno-toplevel-reorder', '-std=gnu99',
             '-Wno-error', '-I'+str(sdk/'iop/include'), '-I'+str(sdk/'common/include')]
    if name == 'xbox360usb':
        flags.append('-DKINHANK_MONITOR')
    objects = []
    for filename in sources:
        obj = out / (Path(filename).stem + '.o')
        run([gcc, *flags, '-I'+str(folder), '-c', folder/filename, '-o', obj])
        objects.append(obj)
    for stem, header, suffix in [('exports', 'irx.h', 'tab'), ('imports', 'irx_imports.h', 'lst')]:
        listing = folder / (stem+'.'+suffix)
        if not listing.exists():
            continue
        generated = out / (stem+'.c')
        generated.write_text('#include "'+header+'"\n'+listing.read_text().replace('I_strncmp', 'I_strncmp\nI_strcmp'))
        obj = out / (stem+'.o')
        run([gcc, *flags, '-I'+str(folder), '-c', generated, '-o', obj])
        if stem == 'exports':
            objects.insert(0, obj)
        else:
            objects.append(obj)
    linked, stripped, irx = (out/(name+ext) for ext in ('.elf', '.stripped.elf', '.irx'))
    run([gcc, '-nostdlib', '-T'+str(sdk/'iop/startup/linkfile'), '-Wl,-r', '-Wl,-d', *objects, '-o', linked])
    # Essential: IOP loadcore applies debug relocations too if .pdr survives.
    run([tool('mipsel-none-elf-strip', dev/'iop/bin'), '--strip-unneeded',
         '--remove-section=.pdr', '--remove-section=.comment',
         '--remove-section=.mdebug.abi32', '--remove-section=.gnu.attributes',
         '-o', stripped, linked])
    run([tool('srxfixup', sdk/'bin'), '--rb', '--irx1',
         *(['--allow-zero-text'] if name != 'pademu' else []), '-o', irx, stripped])
    return irx

def embed(path, blobs):
    with path.open('w') as f:
        for name, source in blobs:
            data = source.read_bytes()
            f.write('unsigned char '+name+'_data[] __attribute__((aligned(64)))={'+','.join(map(str,data))+'};\n')
            f.write('unsigned int '+name+'_size='+str(len(data))+';\n')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ps2dev', default=os.environ.get('PS2DEV'))
    parser.add_argument('--ps2sdk', default=os.environ.get('PS2SDK'))
    parser.add_argument('--allow-sdk-usbd-change', action='store_true', help='Allow an untested SDK USBD binary.')
    args = parser.parse_args()
    if not args.ps2dev:
        parser.error('Set PS2DEV or pass --ps2dev.')
    dev = Path(args.ps2dev).resolve()
    sdk = Path(args.ps2sdk).resolve() if args.ps2sdk else dev/'ps2sdk'
    os.environ['PATH'] = os.pathsep.join(map(str,[dev/'ee/bin',dev/'iop/bin',sdk/'bin']))+os.pathsep+os.environ['PATH']
    usbd = sdk/'iop/irx/usbd.irx'
    if not usbd.is_file():
        parser.error(f'Missing {usbd}')
    digest = hashlib.sha256(usbd.read_bytes()).hexdigest()
    if digest != TESTED_USBD and not args.allow_sdk_usbd_change:
        parser.error('SDK USBD differs from the tested build; see docs/BUILDING.md, or explicitly use --allow-sdk-usbd-change.')
    BUILD.mkdir(exist_ok=True)
    pademu = build_iop('pademu', ROOT/'vendor/pademu', ['pademu.c','sys_utils.c'], sdk, dev)
    xbox = build_iop('xbox360usb', ROOT/'vendor/pademu/xbox360usb', ['xbox360usb.c'], sdk, dev)
    embed(BUILD/'modules.c', [('usbd',usbd),('pademu',pademu),('xbox',xbox)])
    gcc = tool('mips64r5900el-ps2-elf-gcc', dev/'ee/bin')
    flags = ['-D_EE','-DNEWLIB_PORT_AWARE','-G0','-O2','-fno-builtin',
             '-I'+str(sdk/'ee/include'),'-I'+str(sdk/'common/include')]
    def compile_sources(folder, sources, resident=False):
        out = BUILD/folder
        out.mkdir(exist_ok=True)
        objects = []
        for source in sources:
            obj = out/(source.stem+'-'+source.suffix[1:]+'.o')
            run([gcc,*flags,*(['-DBOOT_RESIDENT'] if resident else []),'-c',source,'-o',obj])
            objects.append(obj)
        return objects
    src = ROOT/'src'
    sources = [src/'main.c',BUILD/'modules.c',src/'syscall_hooks.S',src/'safe_screen.c',src/'early.c',src/'early.S']
    objects = compile_sources('resident',sources,True)
    resident = BUILD/'resident.elf'
    run([gcc,'-T'+str(src/'linkfile'),'-O2','-o',resident,*objects,'-L'+str(sdk/'ee/lib'),
         '-Wl,-zmax-page-size=128','-Wl,-e,checked_entry','-Wl,-Map='+str(BUILD/'resident.map'),'-lpatches','-ldebug','-lcdvd'])
    image = bytearray(resident.read_bytes())
    entry, phoff = struct.unpack_from('<II',image,24)
    phsize, phnum = struct.unpack_from('<HH',image,42)
    loads = [struct.unpack_from('<8I',image,phoff+i*phsize) for i in range(phnum)]
    loads = [p for p in loads if p[0] == 1]
    if not loads or any(p[2]<0x90000 or p[2]+p[5]+32768>0x100000 for p in loads):
        raise SystemExit('Resident/heap overlaps reserved SDK memory or game RAM.')
    image = image[:max(p[1]+p[4] for p in loads)]
    struct.pack_into('<I',image,32,0)
    struct.pack_into('<HHH',image,46,0,0,0)
    (BUILD/'resident-runtime.elf').write_bytes(image)
    (BUILD/'resident.c').write_text('unsigned char resident_elf[] __attribute__((aligned(64)))={'+','.join(map(str,image))+'};\nunsigned int resident_size='+str(len(image))+';\nunsigned int resident_main='+str(entry)+';\nunsigned int resident_gp=0;\n')
    objects = compile_sources('frontend',[src/'frontend.c',BUILD/'resident.c',src/'safe_screen.c',src/'early.c',src/'early.S'])
    output = BUILD/'DQ8-KINHANK-V11.ELF'
    run([gcc,'-T'+str(sdk/'ee/startup/linkfile'),'-O2','-o',output,*objects,'-L'+str(sdk/'ee/lib'),
         '-Wl,-zmax-page-size=128','-Wl,-e,checked_entry','-Wl,-Map='+str(BUILD/'frontend.map'),'-ldebug','-lcdvd'])
    print(f'Built {output}\nSHA256 {hashlib.sha256(output.read_bytes()).hexdigest()}')
    print('Source rebuild; the public metadata-stripped release remains in releases/v11/.')

if __name__ == '__main__':
    main()
