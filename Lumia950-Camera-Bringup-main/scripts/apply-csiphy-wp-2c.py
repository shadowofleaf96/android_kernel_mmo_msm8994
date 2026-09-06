#!/usr/bin/env python3
"""#142: WP live per-lane +0x2c is 0x70. Linux dump did not show it.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

PHY = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csiphy/msm_csiphy.c"

OLD = """			curr_lane++;
		}
		j++;
		lane_mask >>= 1;
	}
	/* 20nm lane block is 0x40, not newer 2PH 0x200+CTRL9. Dump analog. */
"""

NEW = """			msm_camera_io_w(0x70, csiphybase + 0x40*j + 0x2c);
			pr_err("talkman_csiphy wp 2c j=%d now=0x%x\\n",
				j, msm_camera_io_r(csiphybase + 0x40*j + 0x2c));
			curr_lane++;
		}
		j++;
		lane_mask >>= 1;
	}
	/* 20nm lane block is 0x40, not newer 2PH 0x200+CTRL9. Dump analog. */
"""


def main() -> None:
    t = PHY.read_text()
    if "talkman_csiphy wp 2c j=" in t:
        print("csiphy WP +0x2c=0x70 already present")
        return
    if OLD not in t:
        raise SystemExit("curr_lane++ block not found for +0x2c")
    PHY.write_text(t.replace(OLD, NEW, 1))
    print("csiphy: WP +0x2c=0x70")


if __name__ == "__main__":
    main()
