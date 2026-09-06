# Live SMIA++ register dump (kernel #5, 2026-08-18)

Bring-up status: [`bring-up.md`](bring-up.md). These reads prove the
modules can talk CCI. Kernel ident (#11 / uname #29) still NACKs.

Read as CCI WORD after successful match_id. 8-bit regs include the next byte.

## Rear camera@0 / CCI1 / 7-bit 0x10 / model 0xEACA (Sharp)

| Reg | Value | Meaning |
|---|---|---|
| 0x0000 | 0xEACA | model |
| 0x0002 | 0x050A | rev 5, manufacturer Sharp (0x0A) |
| 0x0112 | 0x0A0A | CSI RAW10 |
| 0x0114 | 0x0330 | lane_mode 0x03 = 4 lanes |
| 0x0340 | 0x100A | frame_length 4106 |
| 0x0342 | 0x1788 | line_length 6024 |
| 0x0348 / 0x034A | 0x14DF / 0x0FAF | window end 5343 x 4015 |
| 0x034C / 0x034E | 0x14E0 / 0x0FB0 | **5344 x 4016** (20.5 MP) |
| 0x118C / 0x118E | 0x14E0 / 0x0FB0 | max output same |

PLL @ 9.6 MHz MCLK: pre=4, mult=177, vt_sys=2, vt_pix=4 → vt≈53.1 MHz → ~2.1 fps full-size.

## Front camera@1 / CCI0 / 7-bit 0x10 / model 0x2140 (Sharp)

| Reg | Value | Meaning |
|---|---|---|
| 0x0000 | 0x2140 | model |
| 0x0002 | 0x000A | rev 0, Sharp |
| 0x0112 | 0x0A0A | CSI RAW10 |
| 0x0114 | 0x0130 | lane_mode 0x01 = 2 lanes |
| 0x0340 | 0x0824 | frame_length 2084 |
| 0x0342 | 0x0ABE | line_length 2750 |
| 0x034C / 0x034E | 0x0A28 / 0x07A0 | **2600 x 1952** (5.1 MP) |

`smia65pp.c` comments had these IDs swapped vs ACPI wiring.

## Userspace status

- smia2 (BYTE reset/stream only): both cameras listed; Open Camera connects; `VIDIOC_STREAMON` fails; `getSensorOutputSize` = 0x0.
- smia3 (WORD window in init): `sensor_write_i2c_array` fails (CCI NACK / endian). Reverted to smia2.
