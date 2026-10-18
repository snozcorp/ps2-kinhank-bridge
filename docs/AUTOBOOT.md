# Free McBoot automatic startup

First confirm that V11 works when launched manually. The procedure below changes FMCB settings; it does not change the working ELF.

1. Start LaunchELF using your existing shortcut and a wired controller.
2. Find the active FMCB card's `SYS-CONF/FREEMCB.CNF`. It can be on `mc0:` (slot 1) or `mc1:` (slot 2).
3. Back up that file inside a dedicated USB folder, for example `mass:/backups/FREEMCB.CNF`, or give the root copy a distinct name such as `FMCB-BACKUP.CNF`.
4. Run `FMCB_CFG.ELF` from that card's `SYS-CONF` folder. Select your preferred confirmation-button layout.
5. Confirm the configurator loaded the intended card configuration. Under **Configure E1 launch keys**, set **AUTO** to `mass:/DQ8-KINHANK-V11.ELF` by browsing to the file. Preserve the existing LaunchELF recovery shortcut (R1 on the tested setup).
6. Return to the main configurator screen and set **FastBoot: OFF**. FastBoot can start a disc before AUTO is used.
7. Save CNF to the same memory card you loaded. In the tested setup this was **MC1**, not MC0. Wait for the save confirmation.
8. Power off normally. Leave the stick, receiver and game disc connected; turn on the wireless pad. Boot without holding buttons.

V11's frontend and resident startup messages should appear before the game. If you only see the FMCB/PS2 logos and the game, that does not establish that V11 ran.

## USB configuration precedence

**Do not leave the backup at `mass:/FREEMCB.CNF`.** FMCB checks that exact root filename before the memory-card configuration on the tested boot path. An old copy there can restore the old OPL AUTO path and FastBoot setting on every boot, even after saving changes to the card.

Rename that backup to `FMCB-BACKUP.CNF` or keep it in `backups/`. Keep it available for recovery.

## Recovery

Use the wired controller and the preserved LaunchELF shortcut. On the tested setup this is R1 held from power-on; START did not reliably open the configurator, so this guide does not depend on it. If LaunchELF cannot be reached, try powering off and ejecting the disc before using that existing shortcut. Restore the backed-up configuration or use the configurator to restore the original AUTO path if needed.

[Primary FMCB source showing USB-first config lookup and FastBoot before AUTO](https://github.com/TnA-Plastic/FreeMcBoot/blob/master/launcher2/launcher2.c).
