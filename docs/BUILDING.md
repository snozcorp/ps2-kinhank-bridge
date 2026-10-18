# Building V11

Requirements: Python 3.9+ and an installed [ps2dev toolchain](https://github.com/ps2dev/ps2dev/releases/tag/v2.0.0), including EE/IOP GCC, PS2SDK and `srxfixup`. No earlier project workspace or generated C files are required.

```sh
export PS2DEV=/path/to/ps2dev
export PS2SDK="$PS2DEV/ps2sdk"
python3 tools/build.py
python3 tools/verify.py
```

PowerShell:

```powershell
$env:PS2DEV = 'C:\path\to\ps2dev'
$env:PS2SDK = "$env:PS2DEV\ps2sdk"
python tools/build.py
python tools/verify.py
```

Paths can also be passed with `--ps2dev` and `--ps2sdk`. Windows builds may need the 32-bit runtime DLLs used by the official Windows toolchain on PATH. Keep those dependencies outside this repository.

Output: `build/DQ8-KINHANK-V11.ELF`. The public release under `releases/v11/` is never overwritten. It has non-runtime debug metadata removed; all runtime load segments match the hardware-tested original.

## Toolchain provenance

The original environment used the official ps2dev v2.0.0 Windows distribution and EE GCC 15.2. The exact PS2SDK source commit embedded in that prebuilt distribution was not recorded. We therefore record the precise USBD artifact checksum instead of guessing a source commit from the release date.

Expected SDK `iop/irx/usbd.irx` SHA256:

```text
79d7e20f18801233fc0b8ccde42e784c263c0506c60343f5ea7ca83b02e05c05
```

The build fails if this differs, unless `--allow-sdk-usbd-change` is explicitly passed. That option allows experimentation; it does not establish hardware compatibility with another USB stack. Use the original release if you want the hardware-tested artifact.

The release source rebuild was verified byte-for-byte against:

```text
0af4a5b34230c73bf2f733a1634bf8659cacab1e0a8914e0a5c03d761c6f5079  DQ8-KINHANK-V11.ELF
```

## Build stages

1. Build the vendored PADEMU and modified Xbox USB driver as IRX modules.
2. Strip debug relocation sections **before** IRX conversion. PS2 IOP loadcore otherwise applies `.rel.pdr` entries to runtime memory.
3. Embed those modules and the SDK USBD module into the resident loader.
4. Link the resident at `0x90000`, preserving SDK memory below it and a 32KiB heap below `0x100000`.
5. Embed the resident ELF into a normal frontend ELF linked at `0x100000`.

The output retains the V11 diagnostics and game check. Build cleanup or broader compatibility work should be done separately from this baseline.

## Public binary metadata

The public release is created with `mips64r5900el-ps2-elf-strip --strip-debug`, removing a local build path from `.debug_str`. Verification compares every PT_LOAD segment and entry point with the original. This changes the file checksum, not runtime code/data. The metadata-only public derivative has not been separately run on the console.
