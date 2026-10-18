# PS2 Kinhank Bridge

Use a Kinhank-bundled wireless USB controller receiver with **Dragon Quest VIII from disc on a real PlayStation 2**.

The original V11 build has been tested on a modchipped silver fat PS2 with Free McBoot, a receiver reporting USB **045E:028E**, and the PAL **SLES_539.74** disc. Automatic startup and wireless play were confirmed by the owner.

[Watch the original demonstration and project announcement](https://x.com/snozcorp/status/2111611794481463541).

This grew out of not wanting to buy another controller adapter. Built with Codex through extensive console testing, using existing PS2 homebrew work credited below.

## Download and run

Download [DQ8-KINHANK-V11.ELF](releases/v11/DQ8-KINHANK-V11.ELF) using **Download raw file** on GitHub, or use the release asset. Verify it against [SHA256SUMS](releases/v11/SHA256SUMS).

1. Put the ELF on a FAT32 USB stick.
2. Connect the stick and receiver to the PS2's two USB ports and turn on one wireless controller.
3. Insert the DQ8 PAL SLES_539.74 disc.
4. Launch the ELF through LaunchELF. Use a wired controller for this initial setup.
5. Once the game starts, unplug the wired controller and test wireless input.

Your existing homebrew setup must already be able to run ELF files, and the console must be able to read the disc. No game files, BIOS, FMCB installer or modchip firmware are included.

## Automatic startup

Free McBoot can launch V11 at power-on, removing the need for the wired controller each time. See [the setup guide](docs/AUTOBOOT.md).

**Two important details:** disable FMCB **FastBoot**, and do not leave an old configuration backup named `FREEMCB.CNF` in the USB root. FMCB may load that file before the memory-card settings.

## What is tested

| Item | Confirmed setup |
| --- | --- |
| Console | Modchipped silver fat PS2; exact SCPH model not recorded |
| Homebrew | Free McBoot; LaunchELF 4.43a used during setup |
| Game | Dragon Quest VIII, PAL `SLES_539.74`, from disc |
| Receiver | Kinhank-bundled USB receiver reporting `045E:028E` |
| Controllers | One wireless pad |
| Startup | Manual launch, then FMCB automatic launch without a wired pad |

This is an **experimental, game-specific release**. Other games, other DQ8 regions, second-controller support, rumble, pressure-sensitive buttons and other receiver variants have not been established. A matching USB ID alone does not establish compatibility. The launcher intentionally checks the disc identifier.

The bridge and hooks live in RAM. After power-off, launch V11 again or use the documented autoboot setup. Changing FMCB autoboot settings is optional; the ELF itself does not install to a memory card or flash firmware.

## Source and build

[Build instructions](docs/BUILDING.md) · [How it works](docs/ARCHITECTURE.md) · [Testing and known limits](docs/TESTING.md)

The checked-in source was rebuilt with the original local toolchain and produced **the identical SHA-256** as the physically tested V11 ELF. Different toolchain versions may produce different output. The public download has debug metadata removed to exclude a local build path; its loadable segments and entry point are identical to that original. This metadata-only derivative has not been separately run on the console. Generated build output stays separate from the release.

## Credits and licenses

This project adapts existing homebrew; it does not claim to invent USB controller support on PS2.

- [RoloDeOvo's modular-PADEMU OPL branch](https://github.com/RoloDeOvo/Open-PS2-Loader/tree/f16f35435f6c4b55a4282a1ba35b32ec40e18739): PADEMU and Xbox 360 USB driver foundation, including original SIO2 hook credits to Romz and Polo.
- [PS2rd](https://github.com/mlafeldt/ps2rd/tree/b433fa34bed0edb2665d5d6bd4f45585606aed74): reset syscall trampoline approach, by jimmikaelkael and Mathias Lafeldt.
- [PS2SDK / ps2dev](https://github.com/ps2dev/ps2sdk): toolchain, USB host module, libraries and debug display code.
- snozcorp: hardware testing, project direction and release; development assisted by Codex.

The repository contains components with different licenses. Launcher/hook adaptations use GPL-3.0-or-later; vendored PADEMU components retain their AFL-3.0 and SDK-origin AFL-2.0 notices; SDK display code retains AFL-2.0. See [NOTICE](NOTICE.md), [LICENSE](LICENSE), and [licenses/](licenses/). The root license does not relicense third-party files.

## Compatibility reports

If you test another setup, open an issue with the console model, homebrew boot method, receiver VID/PID, game region/serial, and the last visible checkpoint. Report whether it works without a wired controller from a full power-on. Please do not upload game images or BIOS files.
