#!/usr/bin/env python3
"""TG payload. Mode 2 = 0x55/0xAA (clips under black). Mode 4 = ALL_ONES
still painted black once HAL dequeued BUF_DIVERT (#118). Mode 1 =
incrementing (3-bit field); should show a ramp if display is alive.

HAL never reaches START_STREAM without CSID SOF (102/103 froze at I2C
table 5). Keep TG on so HAL completes, then 0x0100=1 can go out.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

CSID = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csid/msm_csid.c"


def main() -> None:
    t = CSID.read_text()
    if "static int talkman_tg = 1;" in t:
        print("csid TG already on")
    elif "static int talkman_tg = 0;" in t:
        t = t.replace("static int talkman_tg = 0;",
                      "static int talkman_tg = 1;", 1)
        CSID.write_text(t)
        print("csid: talkman_tg=1 (HAL SOF + live 0x0100)")
    else:
        raise SystemExit("talkman_tg not found")
    t = CSID.read_text()
    if "static int talkman_tg_mode = 1;" in t and "static int talkman_tg_mode = 4;" not in t:
        print("csid TG incrementing already present")
        return
    if "static int talkman_tg_mode = 4;" in t:
        t = t.replace(
            "static int talkman_tg_mode = 4;",
            "static int talkman_tg_mode = 1;",
            1,
        )
        CSID.write_text(t)
        print("csid: TG payload 1 = incrementing")
        return
    if "static int talkman_tg_mode = 2;" in t:
        t = t.replace(
            "static int talkman_tg_mode = 2;",
            "static int talkman_tg_mode = 1;",
            1,
        )
        CSID.write_text(t)
        print("csid: TG payload 1 = incrementing")



if __name__ == "__main__":
    main()
