# Validation and limits

## Physical validation

The owner confirmed V11 launched DQ8 PAL SLES_539.74 from disc with wireless input on a real modchipped fat PS2. They later confirmed a full automatic boot without a wired controller, after disabling FMCB FastBoot and renaming a USB-root configuration backup that overrode the memory-card configuration.

This is one known setup. It is not a compatibility survey, extended endurance test, or verification of every button/feature.

## Repeatable local checks

`python tools/verify.py` checks public release integrity, source/build packaging, ELF segment/entry bounds, embedded resident bytes and IRX relocation targets. After building, it compares the output hash to the hardware-tested original and compares all runtime load segments with the debug-stripped public release. The public metadata-only derivative has not been separately run on the console.

Optional instruction-level tests:

```sh
python -m pip install -r tests/requirements.txt
python tests/verify_hooks.py build/resident.elf
```

These execute the actual linked reset syscall trampolines with synthetic DMA packets. They verify the matching reset packet, four nonmatching variants and the saved EPC register hook. They do not emulate a full EE kernel, IOP, USB receiver or disc boot.

Earlier development also exercised PADEMU initialization and emulated pad replies at several IOP relocation bases, and physical USB packet/PS2-controller API diagnostics succeeded before V11. The repository includes the focused checks relevant to the release rather than the entire exploratory test history.

## Not established

- Other disc regions/serials or games.
- Other PS2 models, firmware/modchip combinations or receiver variants.
- Two simultaneous wireless controllers, rumble or pressure sensitivity.
- Persistence through arbitrary EE executable reloads or nonstandard IOP reset flows.

Do not mark a source rebuild as hardware-tested simply because static or Unicorn checks pass.
