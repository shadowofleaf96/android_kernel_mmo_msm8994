# Talkman VFE44 CAMIF (keep; do not rediscover)

ISPIF PIX0 SOF is live (~37 fps, `st0=0x7`, no bit12 overflow).
HAL1 paints CSID TG (pink scanlines). Live Hill CSI still has no PIX SOF
without TG (`0x20000dd`). Talkman DT is `compatible = "qcom,vfe44"`.
`persist.camera.HAL3.enabled` must stay **0**.

## Register map (CAF `msm_isp44.c` / mainline camss-vfe-4-1)

| Off | Name | Live (#85 dump / #86 log) |
|---|---|---|
| 0x1C | CORE mux/pattern | `mux<<16 \| pat` → **0** (CAMIF + RGGB) |
| 0x2E8 | RDI0 / camif_input | **0x7** (MIPI enum 3 ORed) |
| 0x2F4 | CAMIF_CMD | **1** (enable at frame boundary) |
| 0x2F8 | CAMIF_CFG | **0x40** bit6 VFE_OUTPUT_EN; bus_en=0 |
| 0x300 | FRAME_CFG | `lpF<<16 \| ppl`. HAL **4080×3028** (`0x0bd40ff0`) |
| 0x304 | WINDOW_W | `first_pix<<16 \| last_pix`. HAL **48..4079** |
| 0x308 | WINDOW_H | `first_line<<16 \| last_line`. HAL **2..3025** |
| 0x31C | CAMIF_STATUS | error IRQ1 bit0. **Halt = bit31**. Count below. |

HAL: mux=0 CAMIF, pat=0 RGGB, in=3 MIPI, hbi=0. INPUT_CFG pixclk is
**424.8 MHz** (#92); #86 logged 480 MHz after `set_clk_rate` rounding.

**WP live VF (KD 2026-08-22):** FRAME **2496×1872**, window
**0..2495 × 0..1871**, CFG **`0x001d0040`**, input **`0x17`**, mux 0,
EFS 0, status 0, VFE0 RCG **320 MHz**. Linux **#144** writes that
window (`camif ff0b`) but TG was still 4080×3028 @ 600 → overflow
**`0xff8`**. **#145** TG 2496×1872: overflow gone; TG-on CSID
**`0x2000200 ECC`**. Do not keep #93 320 MHz until CSI works.

## CAMIF_STATUS decode (from QCOM iface dumps)

`status = (lines << 16) \| pixels` of the frame that failed:

| Kernel | status | meaning |
|---|---|---|
| #85/#86 ppl=4080 | **0x00000ff8** | 0 lines, **4088** pixels (overflow on line 0) |
| #144 CAMIF 2496 / TG 4080 | **0xff8** then **`0xbd40ff8`** | TG still 4080×3028 into 2496 window |
| #145 CAMIF+TG 2496 | **0x0** | overflow gone; error IRQ still fires with 0 |
| #87 ppl=4088 | *(no error IRQ)* | overflow gone; **still no EOF** |
| #88 lpf=1 | **0x0bd40000** | **3028** lines, 0 pixels (TG is full height) |
| #90 no error | **0x00000000 at SOF** | 0x31C is an error latch; 0 at SOF is normal. |
| #91 mid-frame | **st=0x0** cmd=1 cfg=0x40 extra=`0xaadc0000` | Live 0x31C stays 0 unless erroring. |
| #92 pixclk 200 MHz | **0x000015f8** = 0 lines, **5624** px | **Pixels reach CAMIF.** 200 MHz too slow. HAL asked **424.8 MHz**. Do not keep. |
| #93 pixclk 320 MHz | **0x00001a48** = 0 lines, **6728** px | Still too slow (TG ~458 Mpix/s). ISPIF `st0=0x5`. Do not keep. |
| #94 pixclk 600 MHz | no error IRQ | No overflow. SOF + **EPOCH0** (`s0=0x5`). Still **never EOF**. Clock table done. |
| #98 last_line=3026 | no error IRQ | Window `0..3026`. Epoch 3027 still fires. **Still no EOF.** Extra TG line is not overflow. |

EOF is irq0 **bit1**. SOF is bit0. First SOF often `s0=0x11` (bit4 extra).
Later SOF `s0=0x1` only. **#102 unmasked bit1:** EOF fires **with EPOCH0**
(`s0=0x6`) every frame. CAF `val |= 0xF5` hid it. Black preview is AXI.

`process_input_irq` mask `0x1000003` = SOF/EOF/FE.

## What this means

- ISPIF PIX SOF ⇄ CAMIF SOF lockstep. Frames reach VFE.
- TG **does** emit ~3028 line valids per SOF (#88).
- Line 0 has **4088** pixels, 8 more than HAL 4080 (#86). ppl **4088**
  clears overflow (#87). Keep that; do not go back to 4080.
- Matching ppl + full window **does not** produce EOF. Not the IMX377
  dummy crop. Not “TG is 1 line”.
- **#96: epoch0 at last_line 3027 fires every frame** (~26 ms after SOF).
  CAMIF **does count all 3028 lines.** Next SOF ~0.5 ms later, **no EOF**.
  Missing EOF is FE/V-blank, not pixclk, not line count, not EFS 0x2FC.
- **#98 last_line=3026**: extra TG line is not overflow; still no EOF.
- **#99 0x2E8=0x3**: RDI_EN was not the blocker. HAL **SOF freeze**.
- **#102: CAMIF EOF was always there.** CAF irq_mask0 `0xF5` omits bit1.
  Unmask `0xF7` → `eof=1` with EPOCH0 (`s0=0x6`).
- **#104: AXI framedrop pattern was 0** (drop all). ping/pong IOVAs live.
- **#107: AXI composite irq every frame** (viewfinder). Encoder drop-all
  avoids IOMMU. Preview still black (TG 0x55 vs black level).
- **#108: TG ALL_ONES still black.** HAL `SOF freeze` at 5s. Kernel
  EPOCH0+AXI live. Black is not chromatix.
- **#109: epoch0 line 20** still SOF freeze. Not the epoch line.
- 0x31C is an **error latch**, not a live counter (#90/#91 read 0).

## Do not repeat

- CAMIF 1-line window (`boot-smia70.img`) — overflow 3028 lines.
- Pixclk **200 MHz** (`boot-smia74.img`) — overflow 5624 px; revert.
- Pixclk **320 MHz** (`boot-smia75.img`) — overflow 6728 px; revert.
- Pixel-width TG DT0 (`boot-smia65.img` #83) — TG uncorrectable.
- CFG4=0, WOA 1/66, re-enable `0x0100` until CAMIF EOF exists.
- Treating CSID `long=0 map=0` as “no frames” (ISPIF SOF is the metric).
- last_line=3026 / 0x2E8=0x3 as EOF fixes (#98/#99).
- CAMIF_CFG **syncMode=EFS** (`boot-smia82.img` #100) — **killed CAMIF SOF**.

## Next (ordered)

1. Live CSI still has no PIX SOF without TG. 4-lane irq is **ECC**.
   WP pixel CID is DT **`0x30` DPCM**, not RAW10 `0x2B` (#146 wrote it;
   still ECC). **#148** CGC/TCSR/CSI0/phytimer already matched WP VF.
   Not a CGC mux lottery. Do **not** early-`0x0100`.
2. Do **not** leave TG auto-off daily. **#145** 2496 TG ECC's on enable;
   **#149** 4080 TG headers are valid (`unmap` DT `0x2B`).

Phone: `boot-smia113.img` (**#131**) daily. Do not flash `boot-smia93/96/97/98/105/106/107/110/111/112/114-145`.
`boot-smia131.img` is uname **#149**, not the daily #131.
`boot-smia144.img` is uname **#162**. `boot-smia145.img` is uname **#163**.
CSI restore: `boot-smia44.img`. First HAL1 viewfinder: `boot-smia101.img`.
