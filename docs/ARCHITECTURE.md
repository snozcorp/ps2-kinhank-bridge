# How it works

The receiver enumerates as `045E:028E` and sends Xbox 360-style USB reports. The modified OPL Xbox driver reads those reports on the PS2's IOP and caches decoded state. PADEMU hooks SIO2MAN transfers so the game's controller API receives emulated pad replies.

The frontend validates and copies a resident loader below normal game RAM, verifies the copied bytes, and starts its full C runtime through ExecPS2. Both entry paths show a PAL diagnostic screen before CRT initialization using a small temporary stack. This display uses no ROM/file/RPC calls, and its brief checkpoint delays poll the EE CP0 Count register.

The resident reads the physical disc's SYSTEM.CNF, requires `SLES_539.74`, validates the game ELF segment ranges, loads the original executable, and installs USBD, PADEMU and the Xbox driver. It then installs PS2rd-derived SifSetDma/SifSetReg syscall trampolines and starts the game.

A standard IOP reset DMA packet is detected by its attributes, size and command identifier. The hook forwards the original reset request, waits for synchronization, reloads the controller modules and returns control to the game. The disc and game executable are not patched on storage.

## Changes to the upstream controller modules

- Remove an unsupported loadcore ordinal-27 dependency for the tested environment.
- Strip debug relocations before IRX conversion.
- Add staged RAM trace mailboxes and unique patchable address markers.
- Poll USB in a driver worker; provide cached snapshots to PADEMU, avoiding duplicate blocking reads.
- Guard missing USB descriptors.
- Find multiple SIO2MAN versions and patch already-linked import stubs.

Mailbox structures and extra counters remain in the tested baseline. They are useful diagnostic data rather than a new public protocol.

## Important boundaries

The resident starts at `0x90000`, not `0x80000`: PS2SDK's alarm support uses `0x82000`. Earlier builds overwrote that payload. The loader and its 32KiB heap must stay below `0x100000`; game load segments must fit from `0x100000` to below `0x01f00000`.

This implementation handles the reset pattern checked in `syscall_hooks.S`. It does not provide a general LoadExecPS2/sub-ELF reload hook. It is not a system-wide replacement for PS2 controller hardware. The firmware, modchip, game files and memory-card installation are outside its scope.
