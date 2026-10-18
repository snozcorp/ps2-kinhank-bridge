# Copyright, attribution and component licenses

This is a collection of launcher sources, separately loaded IOP modules and a tested executable. Preserve upstream notices when redistributing it. No blanket relicensing of third-party components is intended.

| Component | Origin | License/notices |
| --- | --- | --- |
| Launcher and reset-hook adaptations (`src/main.c`, `src/syscall_hooks.S`) | This project, using PS2rd's debugger/reset trampoline work by jimmikaelkael and Mathias Lafeldt | GPL-3.0-or-later; see LICENSE |
| Frontend, entry helpers and project scripts | This project | GPL-3.0-or-later |
| `vendor/pademu/` | RoloDeOvo modular-pademu OPL branch, commit f16f35435f6c4b55a4282a1ba35b32ec40e18739 | AFL-3.0; individual SDK-origin files retain AFL-2.0 notices |
| SIO2 hook foundation | Romz (2006-2008), Polo (2010), as credited upstream | AFL-3.0 |
| `src/safe_screen.c`, `src/linkfile` and SDK headers/libraries/USBD used at build time | PS2SDK contributors | AFL-2.0; retained file notices; external toolchain contains further component notices |
| Bundled ELF | Compiled from the above components and the documented external ps2dev toolchain | Accompany it with these sources, build instructions and upstream license notices |

Full upstream licenses are in `licenses/`. Exact imported repository revisions are recorded in `vendor/PROVENANCE.json`. The PS2SDK commit within the historical prebuilt toolchain was not recorded; the distribution and exact tested USBD artifact checksum are documented instead.

The modular OPL repository's LICENSE applies to the imported driver files lacking their own header. This project modifies module initialization, tracing, polling/caching, descriptor checks and SIO2 hook handling. The SDK screen source is modified to select PAL without ROM/RPC queries.

PS2rd source: https://github.com/mlafeldt/ps2rd/tree/b433fa34bed0edb2665d5d6bd4f45585606aed74

The C toolchain links its standard runtime libraries under their upstream terms; those libraries are provided by the external ps2dev distribution, not copied here as a replacement SDK. Do not treat the root GPL license as changing their licenses.

Game trademarks belong to their respective owners. Kinhank, Sony, Square Enix and the upstream homebrew projects do not endorse this project.
