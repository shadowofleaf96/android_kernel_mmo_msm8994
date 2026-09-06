#!/usr/bin/env python3
"""Kernel #10: make CSI programming visible and keep the PHY/CSID clocks alive.

SOF freeze with a successful ISP/CPP stream-on means CAMIF never sees a
frame. CSIPHY/CSID cfg is CDBG-only, SMIA 0x0100/0x0111 were never dumped
after stream-on, and smia7's 53.1 MHz pixclk can be reused as csiphy_clk
which then divides settle_cnt toward 0.

This does not change lane maps. It logs, clamps clocks/settle, forces
CSI-2 signalling, and verifies mode_select after HAL stream-on.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

ROOT = KERNEL_TREE
CSIPHY = ROOT / "drivers/media/platform/msm/camera_v2/sensor/csiphy/msm_csiphy.c"
CSID = ROOT / "drivers/media/platform/msm/camera_v2/sensor/csid/msm_csid.c"
SENSOR = ROOT / "drivers/media/platform/msm/camera_v2/sensor/msm_sensor.c"
ISPIF = ROOT / "drivers/media/platform/msm/camera_v2/ispif/msm_ispif.c"


def must_replace(path: Path, old: str, new: str, label: str) -> str:
    t = path.read_text() if isinstance(path, Path) else path
    if isinstance(path, Path):
        t = path.read_text()
    if new.strip()[:40] in t and old not in t:
        print(f"{label}: already applied")
        return t
    if old not in t:
        raise SystemExit(f"{label}: pattern not found in {path}")
    print(label)
    return t.replace(old, new, 1)


def patch_csiphy():
    t = CSIPHY.read_text()
    old = """	clk_rate = (csiphy_params->csiphy_clk > 0)
			? csiphy_params->csiphy_clk :
			csiphy_dev->csiphy_max_clk;
	round_rate = clk_round_rate(
			csid_phy_clk_ptr[csiphy_dev->csiphy_clk_index],
			clk_rate);
	if (round_rate >= csiphy_dev->csiphy_max_clk)
		round_rate = csiphy_dev->csiphy_max_clk;
	else {
		ratio = csiphy_dev->csiphy_max_clk/round_rate;
		csiphy_params->settle_cnt = csiphy_params->settle_cnt/ratio;
	}

	CDBG("set from usr csiphy_clk clk_rate = %u round_rate = %u\\n",
			clk_rate, round_rate);
"""
    new = """	clk_rate = (csiphy_params->csiphy_clk > 0)
			? csiphy_params->csiphy_clk :
			csiphy_dev->csiphy_max_clk;
	/* smia7 advertises 53.1 MHz vt. That is below CSIPHY timer min. */
	if (clk_rate < 100000000)
		clk_rate = csiphy_dev->csiphy_max_clk;
	round_rate = clk_round_rate(
			csid_phy_clk_ptr[csiphy_dev->csiphy_clk_index],
			clk_rate);
	if (round_rate >= csiphy_dev->csiphy_max_clk)
		round_rate = csiphy_dev->csiphy_max_clk;
	else if (round_rate) {
		ratio = csiphy_dev->csiphy_max_clk/round_rate;
		if (ratio > 1)
			csiphy_params->settle_cnt =
				csiphy_params->settle_cnt / ratio;
	}
	if (csiphy_params->settle_cnt < 8)
		csiphy_params->settle_cnt = 0x0E;

	pr_err("talkman_csiphy id=%d lanes=%u mask=0x%x settle=0x%x combo=%u csid=%u usr_clk=%u use=%u round=%u\\n",
		csiphy_id, csiphy_params->lane_cnt,
		csiphy_params->lane_mask, csiphy_params->settle_cnt,
		csiphy_params->combo_mode, csiphy_params->csid_core,
		csiphy_params->csiphy_clk, clk_rate, round_rate);
"""
    if "talkman_csiphy id=" in t:
        print("csiphy log already present")
    else:
        if old not in t:
            raise SystemExit("csiphy clk_rate block not found")
        t = t.replace(old, new, 1)
        print("csiphy: log + clk/settle clamp")

    if "talkman_settle" not in t:
        if "#define DBG_CSIPHY 0\n" not in t:
            raise SystemExit("DBG_CSIPHY 0 not found for settle param")
        t = t.replace(
            "#define DBG_CSIPHY 0\n",
            """#define DBG_CSIPHY 0

/* #49: 0x0234 == 0x4320 (pkts+ECC). Try longer HS-settle. HAL 0x1b is 135ns
 * @ 200 MHz; 0x28 is 200ns. echo -1 leaves the HAL value. */
static int talkman_settle = 0x28;
module_param_named(settle, talkman_settle, int, 0644);
MODULE_PARM_DESC(settle, "CSIPHY settle_cnt; -1 = leave HAL value");

/* 20nm lnn_misc1 lane-id uses 0x4 (clk) / 0x8|n (data). Bit 0 is unused.
 * OR 1 on every enabled lane = try P/N invert. echo 0 to disable. */
static int talkman_pn_invert = 1;
module_param_named(pn_invert, talkman_pn_invert, int, 0644);
MODULE_PARM_DESC(pn_invert, "OR 1 into CSIPHY 20nm lnn_misc1 (P/N invert)");

""",
            1,
        )
        print("csiphy: settle module_param default 0x28")

    old_settle = """	if (csiphy_params->settle_cnt < 8)
		csiphy_params->settle_cnt = 0x0E;

	pr_err("talkman_csiphy id=%d lanes=%u mask=0x%x settle=0x%x combo=%u csid=%u usr_clk=%u use=%u round=%u\\n",
		csiphy_id, csiphy_params->lane_cnt,
		csiphy_params->lane_mask, csiphy_params->settle_cnt,
		csiphy_params->combo_mode, csiphy_params->csid_core,
		csiphy_params->csiphy_clk, clk_rate, round_rate);
"""
    new_settle = """	if (csiphy_params->settle_cnt < 8)
		csiphy_params->settle_cnt = 0x0E;
	if (talkman_settle >= 0)
		csiphy_params->settle_cnt = talkman_settle;

	pr_err("talkman_csiphy id=%d lanes=%u mask=0x%x settle=0x%x combo=%u csid=%u usr_clk=%u use=%u round=%u hw=0x%x nm20=%d\\n",
		csiphy_id, csiphy_params->lane_cnt,
		csiphy_params->lane_mask, csiphy_params->settle_cnt,
		csiphy_params->combo_mode, csiphy_params->csid_core,
		csiphy_params->csiphy_clk, clk_rate, round_rate,
		csiphy_dev->hw_version, csiphy_dev->is_3_1_20nm_hw);
"""
    if "nm20=%d" in t:
        print("csiphy settle override already applied")
    elif old_settle in t:
        t = t.replace(old_settle, new_settle, 1)
        print("csiphy: force settle 0x28 + hw log")
    else:
        print("WARN: csiphy settle log block not found")

    if "talkman_pn_invert" not in t:
        old_parm = (
            'MODULE_PARM_DESC(settle, "CSIPHY settle_cnt; -1 = leave HAL value");\n'
        )
        new_parm = (
            'MODULE_PARM_DESC(settle, "CSIPHY settle_cnt; -1 = leave HAL value");\n'
            "\n"
            "/* 20nm lnn_misc1 lane-id uses 0x4 (clk) / 0x8|n (data). Bit 0 is unused.\n"
            " * OR 1 on every enabled lane = try P/N invert. echo 0 to disable. */\n"
            "static int talkman_pn_invert = 1;\n"
            "module_param_named(pn_invert, talkman_pn_invert, int, 0644);\n"
            'MODULE_PARM_DESC(pn_invert, "OR 1 into CSIPHY 20nm lnn_misc1 (P/N invert)");\n'
        )
        if old_parm not in t:
            raise SystemExit("settle MODULE_PARM_DESC not found for pn_invert")
        t = t.replace(old_parm, new_parm, 1)
        print("csiphy: pn_invert module_param default 1")
    if "static int talkman_pn_invert = 1;" in t:
        t = t.replace(
            "static int talkman_pn_invert = 1;",
            "static int talkman_pn_invert = 0;",
            1,
        )
        print("csiphy: pn_invert=0 (#124 2-lane data invert same 0xcc)")
    if "static int talkman_pn_invert = 3;" in t:
        t = t.replace(
            "static int talkman_pn_invert = 3;",
            "static int talkman_pn_invert = 0;",
            1,
        )
        print("csiphy: pn_invert=0 (#124 2-lane data invert same 0xcc)")
    if "static int talkman_pn_invert = 2;" in t:
        t = t.replace(
            "static int talkman_pn_invert = 2;",
            "static int talkman_pn_invert = 0;",
            1,
        )
        print("csiphy: pn_invert=0")
    if "static int talkman_pn_invert = 0;" in t:
        print("csiphy pn_invert already 0")

    if "talkman_cfg4_clr0" not in t:
        old_cfg4p = (
            'MODULE_PARM_DESC(pn_invert, "OR 1 into CSIPHY 20nm lnn_misc1 (P/N invert)");\n'
        )
        new_cfg4p = (
            'MODULE_PARM_DESC(pn_invert, "OR 1 into CSIPHY 20nm lnn_misc1 (P/N invert)");\n'
            "\n"
            "/* #63 half CSI same EOT+ECC. cfg4 reset is 0x5; clear bit 0. */\n"
            "static int talkman_cfg4_clr0 = 1;\n"
            "module_param_named(cfg4_clr0, talkman_cfg4_clr0, int, 0644);\n"
            'MODULE_PARM_DESC(cfg4_clr0, "Clear CSIPHY LNn_CFG4 bit 0");\n'
        )
        if old_cfg4p not in t:
            print("WARN: pn_invert decl not found for cfg4_clr0")
        else:
            t = t.replace(old_cfg4p, new_cfg4p, 1)

        print("csiphy: cfg4_clr0 module_param")
    if "static int talkman_cfg4_clr0 = 1;" in t:
        t = t.replace(
            "static int talkman_cfg4_clr0 = 1;",
            "static int talkman_cfg4_clr0 = 0;",
            1,
        )
        print("csiphy: cfg4_clr0 default back to 0 (#65 CSID silent)")
    elif "static int talkman_cfg4_clr0 = 0;" in t:
        print("csiphy cfg4_clr0 already 0")

    old_misc = """			msm_camera_io_w(lane_val, csiphybase +
				csiphy_dev->ctrl_reg->csiphy_reg.
				mipi_csiphy_lnn_misc1_addr + 0x40*j);
			msm_camera_io_w(0x17, csiphybase +
"""
    new_misc = """			if (talkman_pn_invert)
				lane_val |= 0x1;
			pr_err("talkman_csiphy ln j=%d misc1=0x%x pn=%d\\n",
				j, lane_val, talkman_pn_invert);
			msm_camera_io_w(lane_val, csiphybase +
				csiphy_dev->ctrl_reg->csiphy_reg.
				mipi_csiphy_lnn_misc1_addr + 0x40*j);
			msm_camera_io_w(0x17, csiphybase +
"""
    if "talkman_csiphy ln j=" in t:
        print("csiphy pn_invert write already applied")
    elif old_misc not in t:
        raise SystemExit("lnn_misc1 write not found")
    else:
        t = t.replace(old_misc, new_misc, 1)
        print("csiphy: OR pn_invert into lnn_misc1")

    old_pn1 = """			if (talkman_pn_invert)
				lane_val |= 0x1;
			pr_err("talkman_csiphy ln j=%d misc1=0x%x pn=%d\\n",
				j, lane_val, talkman_pn_invert);
"""
    new_pn3 = """			/* 0=off 1=all (same as off on a differential link)
			 * 2=clock only (misc1 0x4) 3=data only (misc1 bit3). */
			if (talkman_pn_invert == 1 ||
			    (talkman_pn_invert == 2 && lane_val == 0x4) ||
			    (talkman_pn_invert == 3 && (lane_val & 0x8)))
				lane_val |= 0x1;
			pr_err("talkman_csiphy ln j=%d misc1=0x%x pn=%d\\n",
				j, lane_val, talkman_pn_invert);
"""
    if "talkman_pn_invert == 3 && (lane_val & 0x8)" in t:
        print("csiphy pn_invert data/clk split already applied")
    elif old_pn1 in t:
        t = t.replace(old_pn1, new_pn3, 1)
        print("csiphy: pn_invert 1=all 2=clk 3=data")
    else:
        print("WARN: pn_invert if-block not found for data-only")

    if "talkman_cfg4_clr0)" not in t and "if (talkman_cfg4_clr0)" not in t:
        old_imp = """			msm_camera_io_w(0x17, csiphybase +
				csiphy_dev->ctrl_reg->csiphy_reg.
				mipi_csiphy_lnn_test_imp + 0x40*j);
			curr_lane++;
"""
        new_imp = """			msm_camera_io_w(0x17, csiphybase +
				csiphy_dev->ctrl_reg->csiphy_reg.
				mipi_csiphy_lnn_test_imp + 0x40*j);
			if (talkman_cfg4_clr0) {
				uint32_t c4 = msm_camera_io_r(csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg4_addr + 0x40*j);

				msm_camera_io_w(0, csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg4_addr + 0x40*j);
			}
			curr_lane++;
"""
        if old_imp not in t:
            raise SystemExit("test_imp write not found for cfg4_clr0")
        t = t.replace(old_imp, new_imp, 1)
        print("csiphy: CFG4 force 0")
    elif "msm_camera_io_w(c4 & ~0x1, csiphybase +" in t:
        t = t.replace(
            "msm_camera_io_w(c4 & ~0x1, csiphybase +",
            "msm_camera_io_w(0, csiphybase +",
            1,
        )
        print("csiphy: CFG4 write 0 (clear bit2 too)")
    else:
        print("csiphy CFG4 write already applied")

    if "#include <linux/workqueue.h>" not in t:
        t = t.replace(
            "#include <linux/delay.h>\n",
            "#include <linux/delay.h>\n#include <linux/workqueue.h>\n",
            1,
        )
        print("csiphy: workqueue.h")

    if "talkman_csiphy late j=" not in t:
        old_parm_end = (
            'MODULE_PARM_DESC(pn_invert, "OR 1 into CSIPHY 20nm lnn_misc1 (P/N invert)");\n'
        )
        new_parm_end = (
            'MODULE_PARM_DESC(pn_invert, "OR 1 into CSIPHY 20nm lnn_misc1 (P/N invert)");\n'
            "\n"
            "static struct csiphy_device *talkman_late_csiphy;\n"
            "static void talkman_csiphy_late_fn(struct work_struct *w);\n"
            "static DECLARE_DELAYED_WORK(talkman_csiphy_late, talkman_csiphy_late_fn);\n"
            "\n"
            "static void talkman_csiphy_late_fn(struct work_struct *w)\n"
            "{\n"
            "	struct csiphy_device *d = talkman_late_csiphy;\n"
            "	void __iomem *base;\n"
            "	int j;\n"
            "\n"
            "	if (!d || !d->base)\n"
            "		return;\n"
            "	base = d->base;\n"
            "	pr_err(\"talkman_csiphy late irq 0=0x%x 1=0x%x 2=0x%x 3=0x%x 4=0x%x mask0=0x%x pwr=0x%x\\n\",\n"
            "		msm_camera_io_r(base + 0x18c),\n"
            "		msm_camera_io_r(base + 0x190),\n"
            "		msm_camera_io_r(base + 0x194),\n"
            "		msm_camera_io_r(base + 0x198),\n"
            "		msm_camera_io_r(base + 0x19c),\n"
            "		msm_camera_io_r(base + 0x1ac),\n"
            "		msm_camera_io_r(base +\n"
            "			d->ctrl_reg->csiphy_reg.mipi_csiphy_glbl_pwr_cfg_addr));\n"
            "	for (j = 0; j < 5; j++) {\n"
            "		void __iomem *ln = base + 0x40 * j;\n"
            "\n"
            "		pr_err(\"talkman_csiphy late j=%d 00=0x%x 04=0x%x 08=0x%x 0c=0x%x 10=0x%x 20=0x%x 28=0x%x\\n\",\n"
            "			j,\n"
            "			msm_camera_io_r(ln + 0x00),\n"
            "			msm_camera_io_r(ln + 0x04),\n"
            "			msm_camera_io_r(ln + 0x08),\n"
            "			msm_camera_io_r(ln + 0x0c),\n"
            "			msm_camera_io_r(ln + 0x10),\n"
            "			msm_camera_io_r(ln + 0x20),\n"
            "			msm_camera_io_r(ln + 0x28));\n"
            "	}\n"
            "}\n"
        )
        if old_parm_end not in t:
            raise SystemExit("pn_invert MODULE_PARM_DESC not found for late dump")
        t = t.replace(old_parm_end, new_parm_end, 1)
        print("csiphy: late dump work")

    if "talkman_csiphy phy left on pwr=" in t:
        print("csiphy GLBL_PWR_CFG left on (live CSI)")
    elif "talkman_csiphy phy off pwr=" in t:
        print("csiphy GLBL_PWR_CFG already 0 for TG")
    elif "talkman_late_csiphy = csiphy_dev;\n	schedule_delayed_work(&talkman_csiphy_late, msecs_to_jiffies(300));\n	return rc;\n}\n\nstatic irqreturn_t msm_csiphy_irq" in t:
        t = t.replace(
            "	talkman_late_csiphy = csiphy_dev;\n"
            "	schedule_delayed_work(&talkman_csiphy_late, msecs_to_jiffies(300));\n"
            "	return rc;\n"
            "}\n"
            "\n"
            "static irqreturn_t msm_csiphy_irq",
            "	/* CAF TG skips CORE_CTRL so PHY is not an input. 8992 TG needs\n"
            "	 * CORE_CTRL+0x4320 (#81). PHY still HS-locks with 0x0100=0.\n"
            "	 * Mainline csiphy_lanes_disable writes 0 to GLBL_PWR_CFG. */\n"
            "	msm_camera_io_w(0, csiphybase +\n"
            "		csiphy_dev->ctrl_reg->csiphy_reg.\n"
            "		mipi_csiphy_glbl_pwr_cfg_addr);\n"
            "	pr_err(\"talkman_csiphy phy off pwr=0x%x\\n\",\n"
            "		msm_camera_io_r(csiphybase +\n"
            "			csiphy_dev->ctrl_reg->csiphy_reg.\n"
            "			mipi_csiphy_glbl_pwr_cfg_addr));\n"
            "	talkman_late_csiphy = csiphy_dev;\n"
            "	schedule_delayed_work(&talkman_csiphy_late, msecs_to_jiffies(300));\n"
            "	return rc;\n"
            "}\n"
            "\n"
            "static irqreturn_t msm_csiphy_irq",
            1,
        )
        print("csiphy: GLBL_PWR_CFG=0 after lane config (isolate TG from PHY)")
    if "talkman_csiphy dump j=" in t:
        print("csiphy lane dump already applied")
    else:
        old_end = """		j++;
		lane_mask >>= 1;
	}
	return rc;
}

static irqreturn_t msm_csiphy_irq"""
        new_end = """		j++;
		lane_mask >>= 1;
	}
	/* 20nm lane block is 0x40, not newer 2PH 0x200+CTRL9. Dump analog. */
	for (j = 0; j < 5; j++) {
		void __iomem *ln = csiphybase + 0x40 * j;

		pr_err("talkman_csiphy dump j=%d 00=0x%x 04=0x%x 08=0x%x 0c=0x%x 10=0x%x 14=0x%x 18=0x%x 1c=0x%x 20=0x%x 28=0x%x\\n",
			j,
			msm_camera_io_r(ln + 0x00),
			msm_camera_io_r(ln + 0x04),
			msm_camera_io_r(ln + 0x08),
			msm_camera_io_r(ln + 0x0c),
			msm_camera_io_r(ln + 0x10),
			msm_camera_io_r(ln + 0x14),
			msm_camera_io_r(ln + 0x18),
			msm_camera_io_r(ln + 0x1c),
			msm_camera_io_r(ln + 0x20),
			msm_camera_io_r(ln + 0x28));
	}
	pr_err("talkman_csiphy irq 0=0x%x 1=0x%x 2=0x%x 3=0x%x 4=0x%x pwr=0x%x\\n",
		msm_camera_io_r(csiphybase + 0x18c),
		msm_camera_io_r(csiphybase + 0x190),
		msm_camera_io_r(csiphybase + 0x194),
		msm_camera_io_r(csiphybase + 0x198),
		msm_camera_io_r(csiphybase + 0x19c),
		msm_camera_io_r(csiphybase +
			csiphy_dev->ctrl_reg->csiphy_reg.
			mipi_csiphy_glbl_pwr_cfg_addr));
	talkman_late_csiphy = csiphy_dev;
	schedule_delayed_work(&talkman_csiphy_late, msecs_to_jiffies(300));
	return rc;
}

static irqreturn_t msm_csiphy_irq"""
        if old_end not in t:
            raise SystemExit("csiphy lane_config end not found for dump")
        t = t.replace(old_end, new_end, 1)
        print("csiphy: lane register dump")

    if "schedule_delayed_work(&talkman_csiphy_late" not in t:
        old_ret = """	pr_err("talkman_csiphy irq 0=0x%x 1=0x%x 2=0x%x 3=0x%x 4=0x%x pwr=0x%x\\n",
		msm_camera_io_r(csiphybase + 0x18c),
		msm_camera_io_r(csiphybase + 0x190),
		msm_camera_io_r(csiphybase + 0x194),
		msm_camera_io_r(csiphybase + 0x198),
		msm_camera_io_r(csiphybase + 0x19c),
		msm_camera_io_r(csiphybase +
			csiphy_dev->ctrl_reg->csiphy_reg.
			mipi_csiphy_glbl_pwr_cfg_addr));
	return rc;
"""
        new_ret = """	pr_err("talkman_csiphy irq 0=0x%x 1=0x%x 2=0x%x 3=0x%x 4=0x%x pwr=0x%x\\n",
		msm_camera_io_r(csiphybase + 0x18c),
		msm_camera_io_r(csiphybase + 0x190),
		msm_camera_io_r(csiphybase + 0x194),
		msm_camera_io_r(csiphybase + 0x198),
		msm_camera_io_r(csiphybase + 0x19c),
		msm_camera_io_r(csiphybase +
			csiphy_dev->ctrl_reg->csiphy_reg.
			mipi_csiphy_glbl_pwr_cfg_addr));
	talkman_late_csiphy = csiphy_dev;
	schedule_delayed_work(&talkman_csiphy_late, msecs_to_jiffies(300));
	return rc;
"""
        if old_ret not in t:
            raise SystemExit("csiphy dump irq log not found for late schedule")
        t = t.replace(old_ret, new_ret, 1)
        print("csiphy: schedule late dump")
    else:
        print("csiphy late dump already scheduled")

    CSIPHY.write_text(t)


def patch_csid():
    t = CSID.read_text()
    if "#define DBG_CSID 0" in t:
        t = t.replace("#define DBG_CSID 0", "#define DBG_CSID 1", 1)
        print("csid: DBG_CSID=1")
    else:
        print("csid: DBG_CSID already non-zero or missing")

    old = """	CDBG("%s csid_params, lane_cnt = %d, lane_assign = 0x%x\\n",
		__func__,
		csid_params->lane_cnt,
		csid_params->lane_assign);
	CDBG("%s csid_params phy_sel = %d\\n", __func__,
		csid_params->phy_sel);

	msm_csid_reset(csid_dev);
"""
    new = """	pr_err("talkman_csid id=%d lanes=%u assign=0x%x phy_sel=%u usr_clk=%u\\n",
		csid_dev->pdev->id, csid_params->lane_cnt,
		csid_params->lane_assign, csid_params->phy_sel,
		csid_params->csi_clk);

	msm_csid_reset(csid_dev);
"""
    if "talkman_csid id=" in t:
        print("csid config log already present")
    elif old not in t:
        raise SystemExit("csid_params CDBG block not found")
    else:
        t = t.replace(old, new, 1)
        print("csid: config log")

    if "talkman_lane_assign" not in t:
        if "#define DBG_CSID 1\n" not in t:
            raise SystemExit("DBG_CSID 1 not found for lane_assign param")
        t = t.replace(
            "#define DBG_CSID 1\n",
            """#define DBG_CSID 1

/* #48: 0x3210 mapped phy1 (clock) as data (pkts=0, irq 0xd000dd).
 * 0x4320 keeps clock on phy1 and counts packets (header ECC).
 * 0x0234 = reverse of 0x4320 data lanes {0,2,3,4}. echo -1 for DT.
 * #49: 0x0234 same ECC as 0x4320 (ln0=phy4). #58 P/N invert same ECC.
 * #59: ln0=phy2 (0x4302) same ECC. #60: ln0=phy3 (0x4203) same ECC.
 * ln0 sweep {0,2,3,4} all ECC. Default back to 0x4320. */
static int talkman_lane_assign = 0x4320;
module_param_named(lane_assign, talkman_lane_assign, int, 0644);
MODULE_PARM_DESC(lane_assign, "CSID lane_assign override; -1 = DT");

""",
            1,
        )
        print("csid: lane_assign module_param default 0x4320")

    if "static int talkman_lane_assign = 0x0234;" in t:
        t = t.replace(
            "static int talkman_lane_assign = 0x0234;",
            "static int talkman_lane_assign = 0x4320;",
            1,
        )
        print("csid: lane_assign 0x0234 -> 0x4320")
    if "static int talkman_lane_assign = 0x4203;" in t:
        t = t.replace(
            "static int talkman_lane_assign = 0x4203;",
            "static int talkman_lane_assign = 0x4320;",
            1,
        )
        print("csid: lane_assign 0x4203 -> 0x4320")

    if "talkman_ctrl1_or" not in t:
        old_la = (
            'MODULE_PARM_DESC(lane_assign, "CSID lane_assign override; -1 = DT");\n'
        )
        new_la = (
            'MODULE_PARM_DESC(lane_assign, "CSID lane_assign override; -1 = DT");\n'
            "\n"
            "/* WP FUN_0041ddd4 live CORE_CTRL_1: phy_sel<<17 | 0x1000F. */\n"
            "static int talkman_ctrl1_or = 0x1000F;\n"
            "module_param_named(ctrl1_or, talkman_ctrl1_or, int, 0644);\n"
            'MODULE_PARM_DESC(ctrl1_or, "OR into CSID CORE_CTRL_1; -1 = stock 0xF");\n'
        )
        if old_la not in t:
            raise SystemExit("lane_assign MODULE_PARM_DESC not found for ctrl1_or")
        t = t.replace(old_la, new_la, 1)
        print("csid: ctrl1_or module_param default 0x1000F")

    if "talkman_tg" not in t:
        old_c1 = (
            'MODULE_PARM_DESC(ctrl1_or, "OR into CSID CORE_CTRL_1; -1 = stock 0xF");\n'
        )
        new_c1 = (
            'MODULE_PARM_DESC(ctrl1_or, "OR into CSID CORE_CTRL_1; -1 = stock 0xF");\n'
            "\n"
            "/* CAF CSID TG: skip PHY CORE_CTRL, 4080x3028 RAW10 incrementing. */\n"
            "static int talkman_tg = 1;\n"
            "module_param_named(tg, talkman_tg, int, 0644);\n"
            'MODULE_PARM_DESC(tg, "1 = CSID test generator (0xa06437)");\n'
            "static int talkman_tg_w = 4080;\n"
            "module_param_named(tg_w, talkman_tg_w, int, 0644);\n"
            "static int talkman_tg_h = 3028;\n"
            "module_param_named(tg_h, talkman_tg_h, int, 0644);\n"
            "static int talkman_tg_mode = 1;\n"
            "module_param_named(tg_mode, talkman_tg_mode, int, 0644);\n"
            'MODULE_PARM_DESC(tg_mode, "CSID TG payload 2:0 (1=incrementing)");\n'
        )
        if old_c1 not in t:
            raise SystemExit("ctrl1_or MODULE_PARM_DESC not found for tg")
        t = t.replace(old_c1, new_c1, 1)
        print("csid: TG module_param default on")

    old_3210 = """	/* #47: 0x4320 + ECC on every CSI header. Try rotated map. */
	csid_params->lane_assign = 0x3210;
	pr_err("talkman_csid id=%d lanes=%u assign=0x%x phy_sel=%u usr_clk=%u\\n",
		csid_dev->pdev->id, csid_params->lane_cnt,
		csid_params->lane_assign, csid_params->phy_sel,
		csid_params->csi_clk);
"""
    old_log = """	pr_err("talkman_csid id=%d lanes=%u assign=0x%x phy_sel=%u usr_clk=%u\\n",
		csid_dev->pdev->id, csid_params->lane_cnt,
		csid_params->lane_assign, csid_params->phy_sel,
		csid_params->csi_clk);
"""
    new_override = """	if (talkman_lane_assign >= 0)
		csid_params->lane_assign = talkman_lane_assign;
	pr_err("talkman_csid id=%d lanes=%u assign=0x%x phy_sel=%u usr_clk=%u override=0x%x\\n",
		csid_dev->pdev->id, csid_params->lane_cnt,
		csid_params->lane_assign, csid_params->phy_sel,
		csid_params->csi_clk, talkman_lane_assign);
"""
    if "override=0x%x" in t:
        print("csid lane_assign override already applied")
    elif old_3210 in t:
        t = t.replace(old_3210, new_override, 1)
        print("csid: replace 0x3210 force with 0x0234 override")
    elif "csid_params->lane_assign = 0x3210;" in t and old_log in t:
        t = t.replace("	csid_params->lane_assign = 0x3210;\n", "", 1)
        t = t.replace(old_log, new_override, 1)
        print("csid: replace 0x3210 assign + log with override")
    elif old_log in t:
        t = t.replace(old_log, new_override, 1)
        print("csid: apply lane_assign override")
    else:
        print("WARN: csid assign log block not found")

    old = """	clk_rate = (csid_params->csi_clk > 0) ?
				(csid_params->csi_clk) : csid_dev->csid_max_clk;
"""
    new = """	clk_rate = (csid_params->csi_clk > 0) ?
				(csid_params->csi_clk) : csid_dev->csid_max_clk;
	if (clk_rate < 100000000)
		clk_rate = csid_dev->csid_max_clk;
"""
    if "clk_rate < 100000000" in t:
        print("csid clk clamp already present")
    elif old not in t:
        raise SystemExit("csid clk_rate block not found")
    else:
        t = t.replace(old, new, 1)
        print("csid: clk clamp")

    old_ctrl1 = """		val = csid_params->phy_sel <<
			csid_dev->ctrl_reg->csid_reg.csid_phy_sel_shift;
		val |= 0xF;
		msm_camera_io_w(val, csidbase +
		csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_1_addr);
"""
    new_ctrl1 = """		val = csid_params->phy_sel <<
			csid_dev->ctrl_reg->csid_reg.csid_phy_sel_shift;
		/* WP FUN_0041ddd4: phy_sel<<17 | 0x1000F (Linux only used 0xF). */
		if (talkman_ctrl1_or >= 0)
			val |= talkman_ctrl1_or;
		else
			val |= 0xF;
		msm_camera_io_w(val, csidbase +
		csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_1_addr);
		pr_err("talkman_csid ctrl0=0x%x ctrl1=0x%x or=0x%x\\n",
			msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_0_addr),
			val, talkman_ctrl1_or);
"""
    if "talkman_ctrl1_or" in t and "talkman_csid ctrl0=" in t:
        print("csid CORE_CTRL_1 WP 0x1000F already applied")
    elif old_ctrl1 in t:
        t = t.replace(old_ctrl1, new_ctrl1, 1)
        print("csid: CORE_CTRL_1 |= WP 0x1000F")
    else:
        print("WARN: csid CORE_CTRL_1 0xF block not found")

    old_phy = """	val = csid_params->lane_cnt - 1;
	val |= csid_params->lane_assign <<
		csid_dev->ctrl_reg->csid_reg.csid_dl_input_sel_shift;
	if (csid_dev->hw_version < 0x30000000) {
"""
    new_phy = """	if (talkman_tg > 0) {
		uint32_t dt = 0x2b, bpl, tgv;

		if (csid_params->lut_params.num_cid > 0 &&
		    csid_params->lut_params.vc_cfg[0])
			dt = csid_params->lut_params.vc_cfg[0]->dt;
		/* CAF: 31:24 V blank, 23:13 H blank. */
		tgv = ((0x80 & 0xFF) << 24) | ((0x400 & 0x7FF) << 13);
		msm_camera_io_w(tgv, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_vc_cfg_addr);
		bpl = (talkman_tg_w * 10) / 8;
		tgv = ((bpl & 0x1FFF) << 16) | (talkman_tg_h & 0x1FFF);
		msm_camera_io_w(tgv, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_dt_n_cfg_0_addr);
		msm_camera_io_w(dt & 0x3F, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_dt_n_cfg_1_addr);
		msm_camera_io_w(talkman_tg_mode & 7, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_dt_n_cfg_2_addr);
		pr_err("talkman_csid tg cfg %ux%u bpl=%u dt=0x%x mode=%d\\n",
			talkman_tg_w, talkman_tg_h, bpl, dt, talkman_tg_mode);
	} else {
	val = csid_params->lane_cnt - 1;
	val |= csid_params->lane_assign <<
		csid_dev->ctrl_reg->csid_reg.csid_dl_input_sel_shift;
	if (csid_dev->hw_version < 0x30000000) {
"""
    old_lut = """	rc = msm_csid_cid_lut(&csid_params->lut_params, csid_dev);
	if (rc < 0)
		return rc;

	msm_csid_set_debug_reg(csid_dev, csid_params);
	return rc;
"""
    new_lut = """	}
	rc = msm_csid_cid_lut(&csid_params->lut_params, csid_dev);
	if (rc < 0)
		return rc;

	msm_csid_set_debug_reg(csid_dev, csid_params);
	if (talkman_tg > 0) {
		msm_camera_io_w(0x00A06437, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr);
		pr_err("talkman_csid tg enable 0xa06437\\n");
	}
	return rc;
"""
    if "talkman_csid tg mmio" in t:
        print("csid TG+CORE_CTRL mmio dump already applied")
    elif "talkman_csid tg enable 0xa06437" in t:
        old_skip = """	if (talkman_tg > 0) {
		uint32_t dt = 0x2b, bpl, tgv;

		if (csid_params->lut_params.num_cid > 0 &&
		    csid_params->lut_params.vc_cfg[0])
			dt = csid_params->lut_params.vc_cfg[0]->dt;
		/* CAF: 31:24 V blank, 23:13 H blank. */
		tgv = ((0x80 & 0xFF) << 24) | ((0x400 & 0x7FF) << 13);
		msm_camera_io_w(tgv, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_vc_cfg_addr);
		bpl = (talkman_tg_w * 10) / 8;
		tgv = ((bpl & 0x1FFF) << 16) | (talkman_tg_h & 0x1FFF);
		msm_camera_io_w(tgv, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_dt_n_cfg_0_addr);
		msm_camera_io_w(dt & 0x3F, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_dt_n_cfg_1_addr);
		msm_camera_io_w(talkman_tg_mode & 7, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_dt_n_cfg_2_addr);
		pr_err("talkman_csid tg cfg %ux%u bpl=%u dt=0x%x mode=%d\\n",
			talkman_tg_w, talkman_tg_h, bpl, dt, talkman_tg_mode);
	} else {
	val = csid_params->lane_cnt - 1;
	val |= csid_params->lane_assign <<
		csid_dev->ctrl_reg->csid_reg.csid_dl_input_sel_shift;
	if (csid_dev->hw_version < 0x30000000) {
		val |= (0xF << 10);
		msm_camera_io_w(val, csidbase +
		csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_0_addr);
	} else {
		msm_camera_io_w(val, csidbase +
		csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_0_addr);
		val = csid_params->phy_sel <<
			csid_dev->ctrl_reg->csid_reg.csid_phy_sel_shift;
		/* WP FUN_0041ddd4: phy_sel<<17 | 0x1000F (Linux only used 0xF). */
		if (talkman_ctrl1_or >= 0)
			val |= talkman_ctrl1_or;
		else
			val |= 0xF;
		msm_camera_io_w(val, csidbase +
		csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_1_addr);
		pr_err("talkman_csid ctrl0=0x%x ctrl1=0x%x or=0x%x\\n",
			msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_0_addr),
			val, talkman_ctrl1_or);
	}

	}
	rc = msm_csid_cid_lut(&csid_params->lut_params, csid_dev);
	if (rc < 0)
		return rc;

	msm_csid_set_debug_reg(csid_dev, csid_params);
	if (talkman_tg > 0) {
		msm_camera_io_w(0x00A06437, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr);
		pr_err("talkman_csid tg enable 0xa06437\\n");
	}
	return rc;
"""
        new_keep = """	val = csid_params->lane_cnt - 1;
	val |= csid_params->lane_assign <<
		csid_dev->ctrl_reg->csid_reg.csid_dl_input_sel_shift;
	if (csid_dev->hw_version < 0x30000000) {
		val |= (0xF << 10);
		msm_camera_io_w(val, csidbase +
		csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_0_addr);
	} else {
		msm_camera_io_w(val, csidbase +
		csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_0_addr);
		val = csid_params->phy_sel <<
			csid_dev->ctrl_reg->csid_reg.csid_phy_sel_shift;
		/* WP FUN_0041ddd4: phy_sel<<17 | 0x1000F (Linux only used 0xF). */
		if (talkman_ctrl1_or >= 0)
			val |= talkman_ctrl1_or;
		else
			val |= 0xF;
		msm_camera_io_w(val, csidbase +
		csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_1_addr);
		pr_err("talkman_csid ctrl0=0x%x ctrl1=0x%x or=0x%x\\n",
			msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_0_addr),
			val, talkman_ctrl1_or);
	}

	if (talkman_tg > 0) {
		uint32_t dt = 0x2b, bpl, tgv;

		if (csid_params->lut_params.num_cid > 0 &&
		    csid_params->lut_params.vc_cfg[0])
			dt = csid_params->lut_params.vc_cfg[0]->dt;
		/* CAF: 31:24 V blank, 23:13 H blank. */
		tgv = ((0x80 & 0xFF) << 24) | ((0x400 & 0x7FF) << 13);
		msm_camera_io_w(tgv, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_vc_cfg_addr);
		bpl = (talkman_tg_w * 10) / 8;
		tgv = ((bpl & 0x1FFF) << 16) | (talkman_tg_h & 0x1FFF);
		msm_camera_io_w(tgv, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_dt_n_cfg_0_addr);
		msm_camera_io_w(dt & 0x3F, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_dt_n_cfg_1_addr);
		msm_camera_io_w(talkman_tg_mode & 7, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_dt_n_cfg_2_addr);
		pr_err("talkman_csid tg cfg %ux%u bpl=%u dt=0x%x mode=%d\\n",
			talkman_tg_w, talkman_tg_h, bpl, dt, talkman_tg_mode);
	}
	rc = msm_csid_cid_lut(&csid_params->lut_params, csid_dev);
	if (rc < 0)
		return rc;

	msm_csid_set_debug_reg(csid_dev, csid_params);
	if (talkman_tg > 0) {
		msm_camera_io_w(0x00A06437, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr);
		pr_err("talkman_csid tg enable 0xa06437\\n");
	}
	pr_err("talkman_csid tg mmio ctrl0=0x%x ctrl1=0x%x tg=0x%x vc=0x%x dt0=0x%x dt1=0x%x dt2=0x%x lut0=0x%x cid0=0x%x pkts=0x%x ecc=0x%x long=0x%x\\n",
		msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_0_addr),
		msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_1_addr),
		msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr),
		msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_vc_cfg_addr),
		msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_dt_n_cfg_0_addr),
		msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_dt_n_cfg_1_addr),
		msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_dt_n_cfg_2_addr),
		msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_cid_lut_vc_0_addr),
		msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_cid_n_cfg_addr),
		msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_stats_total_pkts_rcvd_addr),
		msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_stats_ecc_addr),
		msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_captured_long_pkt_hdr_addr));
	return rc;
"""
        if old_skip not in t:
            raise SystemExit("csid TG skip-CORE_CTRL block not found for CORE_CTRL keep")
        t = t.replace(old_skip, new_keep, 1)
        print("csid: TG keep CORE_CTRL + mmio dump")
    elif old_phy in t and old_lut in t:
        t = t.replace(old_phy, new_phy, 1)
        t = t.replace(old_lut, new_lut, 1)
        print("csid: CAF test generator 4080x3028")
    else:
        print("WARN: csid CORE_CTRL/LUT block not found for TG")

    old_vc = """		/* CAF: 31:24 V blank, 23:13 H blank. */
		tgv = ((0x80 & 0xFF) << 24) | ((0x400 & 0x7FF) << 13);
"""
    new_vc = """		/* CAF: 31:24 V blank, 23:13 H blank, 3:2 num DT, 1:0 VC.
		 * WP 0x4008001c has bits 3:2 = 3. We used to write 0. */
		tgv = ((0x80 & 0xFF) << 24) | ((0x400 & 0x7FF) << 13);
		if (csid_params->lut_params.num_cid)
			tgv |= (csid_params->lut_params.num_cid & 3) << 2;
"""
    if "(csid_params->lut_params.num_cid & 3) << 2" in t:
        t = t.replace(
            """		/* CAF: 31:24 V blank, 23:13 H blank, 3:2 num DT, 1:0 VC.
		 * WP 0x4008001c has bits 3:2 = 3. We used to write 0. */
		tgv = ((0x80 & 0xFF) << 24) | ((0x400 & 0x7FF) << 13);
		if (csid_params->lut_params.num_cid)
			tgv |= (csid_params->lut_params.num_cid & 3) << 2;
""",
            """		/* CAF and mainline camss leave bits 3:2 = 0 (one DT).
		 * #79 num_cid=3 made ECC worse (high half). */
		tgv = ((0x80 & 0xFF) << 24) | ((0x400 & 0x7FF) << 13);
""",
            1,
        )
        print("csid: TG_VC num DT back to CAF 0")
    elif old_vc in t:
        t = t.replace(old_vc, new_vc, 1)
        print("csid: TG_VC num DT from LUT")
    else:
        print("WARN: TG_VC blanking not found for num DT")

    if "static int talkman_tg_mode = 1;" in t:
        t = t.replace(
            "static int talkman_tg_mode = 1;",
            "static int talkman_tg_mode = 2;",
            1,
        )
        print("csid: TG payload 2 = 0x55/0xAA (not incrementing black crop)")
    # #83: pixel-width DT0 (4080) made TG uncorrectable (IRQ 0x2000000).
    # CAF 7.1 / camss: bits 28:16 are bytes per line (RAW10 → width*10/8).
    if "bpl = talkman_tg_w;" in t:
        t = t.replace(
            "		/* WP 0x400040: this field matches width, not RAW10 bytes. */\n"
            "		bpl = talkman_tg_w;\n",
            "		bpl = (talkman_tg_w * 10) / 8;\n",
        )
        t = t.replace("		bpl = talkman_tg_w;\n",
                      "		bpl = (talkman_tg_w * 10) / 8;\n")
        print("csid: TG DT0 back to CAF bytes-per-line (#83 pixel width broke TG)")
    elif "		bpl = (talkman_tg_w * 10) / 8;\n" in t:
        print("csid TG bpl already CAF bytes-per-line")
    else:
        print("WARN: TG bpl formula not found")

    old_assign = """	val = csid_params->lane_cnt - 1;
	val |= csid_params->lane_assign <<
		csid_dev->ctrl_reg->csid_reg.csid_dl_input_sel_shift;
"""
    new_assign = """	val = csid_params->lane_cnt - 1;
	/* CAF/camss skip PHY lane map when TG is on. 8992 still needs
	 * CORE_CTRL (#75 silent). PHY stays HS-locked with 0x0100=0. */
	if (talkman_tg <= 0)
	val |= csid_params->lane_assign <<
		csid_dev->ctrl_reg->csid_reg.csid_dl_input_sel_shift;
"""
    if "if (talkman_tg <= 0)" in t and "lane_assign <<" in t:
        t = t.replace(
            """	val = csid_params->lane_cnt - 1;
	/* CAF/camss skip PHY lane map when TG is on. 8992 still needs
	 * CORE_CTRL (#75 silent). PHY stays HS-locked with 0x0100=0. */
	if (talkman_tg <= 0)
	val |= csid_params->lane_assign <<
		csid_dev->ctrl_reg->csid_reg.csid_dl_input_sel_shift;
""",
            """	val = csid_params->lane_cnt - 1;
	val |= csid_params->lane_assign <<
		csid_dev->ctrl_reg->csid_reg.csid_dl_input_sel_shift;
""",
            1,
        )
        print("csid: restore PHY lane map (TG needs 0x4320, #81 worse)")
    elif old_assign in t:
        print("csid CORE_CTRL_0 lane_assign kept (TG needs 0x4320)")
    else:
        print("WARN: CORE_CTRL_0 lane_assign block not found")

    old = """		CDBG("%s lut params num_cid = %d, cid = %d\\n",
			__func__,
			csid_lut_params->num_cid,
			csid_lut_params->vc_cfg[i]->cid);
		CDBG("%s lut params dt = 0x%x, df = %d\\n", __func__,
			csid_lut_params->vc_cfg[i]->dt,
			csid_lut_params->vc_cfg[i]->decode_format);
"""
    new = """		pr_err("talkman_csid lut n=%d i=%d cid=%u dt=0x%x df=%u\\n",
			csid_lut_params->num_cid, i,
			csid_lut_params->vc_cfg[i]->cid,
			csid_lut_params->vc_cfg[i]->dt,
			csid_lut_params->vc_cfg[i]->decode_format);
"""
    if "talkman_csid lut n=" in t:
        print("csid lut log already present")
    elif old not in t:
        raise SystemExit("csid lut CDBG block not found")
    else:
        t = t.replace(old, new, 1)
        print("csid: lut log")

    old = """	CDBG("%s CSID%d_IRQ_STATUS_ADDR = 0x%x\\n",
		 __func__, csid_dev->pdev->id, irq);
"""
    new = """	if (irq)
		pr_err_ratelimited("talkman_csid irq id=%d status=0x%x\\n",
			csid_dev->pdev->id, irq);
"""
    if "talkman_csid irq id=" in t:
        print("csid irq log already present")
        if "PHY_OVR" not in t:
            t = t.replace(
                'pr_err_ratelimited("talkman_csid irq id=%d status=0x%x\\n",\n'
                "\t\t\tcsid_dev->pdev->id, irq);\n",
                'pr_err_ratelimited("talkman_csid irq id=%d status=0x%x%s%s%s\\n",\n'
                "\t\t\tcsid_dev->pdev->id, irq,\n"
                '\t\t\t(irq & 0x02000000) ? " ECC" : "",\n'
                '\t\t\t(irq & 0x01000000) ? " CRC" : "",\n'
                '\t\t\t(irq & 0x00F00000) ? " PHY_OVR" : "");\n',
                1,
            )
            print("csid: irq class ECC/CRC/PHY_OVR (CSID 2.0/3.0 masks)")
    elif old not in t:
        raise SystemExit("csid irq CDBG not found")
    else:
        t = t.replace(old, new, 1)
        print("csid: irq log")

    old_stats = """	if (irq)
		pr_err_ratelimited("talkman_csid irq id=%d status=0x%x\\n",
			csid_dev->pdev->id, irq);
"""
    new_stats = """	if (irq) {
		static int talkman_csid_stats;

		pr_err_ratelimited("talkman_csid irq id=%d status=0x%x\\n",
			csid_dev->pdev->id, irq);
		if ((irq & ~0x800) && talkman_csid_stats < 8) {
			talkman_csid_stats++;
			pr_err("talkman_csid stats n=%d pkts=0x%x ecc=0x%x crc=0x%x long=0x%x unmap=0x%x short=0x%x\\n",
				talkman_csid_stats,
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_stats_total_pkts_rcvd_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_stats_ecc_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_stats_crc_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_captured_long_pkt_hdr_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_captured_unmapped_long_pkt_hdr_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_captured_short_pkt_addr));
		}
	}
"""
    if "talkman_csid stats n=" in t:
        print("csid stats dump already present")
    elif old_stats in t:
        t = t.replace(old_stats, new_stats, 1)
        print("csid: packet/crc stats dump")
    else:
        print("WARN: csid irq block for stats not found")

    if "misr=0x%x" not in t:
        old_line = """			pr_err("talkman_csid stats n=%d pkts=0x%x ecc=0x%x crc=0x%x long=0x%x unmap=0x%x short=0x%x\\n",
				talkman_csid_stats,
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_stats_total_pkts_rcvd_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_stats_ecc_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_stats_crc_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_captured_long_pkt_hdr_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_captured_unmapped_long_pkt_hdr_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_captured_short_pkt_addr));
"""
        new_line = """			pr_err("talkman_csid stats n=%d pkts=0x%x ecc=0x%x crc=0x%x long=0x%x unmap=0x%x short=0x%x misr=0x%x/0x%x/0x%x/0x%x\\n",
				talkman_csid_stats,
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_stats_total_pkts_rcvd_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_stats_ecc_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_stats_crc_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_captured_long_pkt_hdr_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_captured_unmapped_long_pkt_hdr_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_captured_short_pkt_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_pif_misr_dl0_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_pif_misr_dl1_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_pif_misr_dl2_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_pif_misr_dl3_addr));
"""
        if old_line not in t:
            raise SystemExit("csid stats line not found for MISR")
        t = t.replace(old_line, new_line, 1)
        print("csid: PIF MISR dump")
    else:
        print("csid MISR already present")

    if "map=0x%x unmap=0x%x" not in t:
        old_misr = """			pr_err("talkman_csid stats n=%d pkts=0x%x ecc=0x%x crc=0x%x long=0x%x unmap=0x%x short=0x%x misr=0x%x/0x%x/0x%x/0x%x\\n",
				talkman_csid_stats,
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_stats_total_pkts_rcvd_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_stats_ecc_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_stats_crc_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_captured_long_pkt_hdr_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_captured_unmapped_long_pkt_hdr_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_captured_short_pkt_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_pif_misr_dl0_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_pif_misr_dl1_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_pif_misr_dl2_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_pif_misr_dl3_addr));
"""
        new_misr = """			pr_err("talkman_csid stats n=%d pkts=0x%x ecc=0x%x crc=0x%x long=0x%x map=0x%x unmap=0x%x short=0x%x misr=0x%x/0x%x/0x%x/0x%x\\n",
				talkman_csid_stats,
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_stats_total_pkts_rcvd_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_stats_ecc_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_stats_crc_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_captured_long_pkt_hdr_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_captured_mmaped_long_pkt_hdr_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_captured_unmapped_long_pkt_hdr_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_captured_short_pkt_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_pif_misr_dl0_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_pif_misr_dl1_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_pif_misr_dl2_addr),
				msm_camera_io_r(csid_dev->base +
				csid_dev->ctrl_reg->csid_reg.csid_pif_misr_dl3_addr));
"""
        if old_misr in t:
            t = t.replace(old_misr, new_misr, 1)
            print("csid: dump mapped long pkt hdr 0x70")
        else:
            print("WARN: stats MISR line not found for map hdr")
    else:
        print("csid mapped hdr dump already present")

    old_mmio = """	pr_err("talkman_csid tg mmio ctrl0=0x%x ctrl1=0x%x tg=0x%x vc=0x%x dt0=0x%x dt1=0x%x dt2=0x%x lut0=0x%x cid0=0x%x pkts=0x%x ecc=0x%x long=0x%x\\n",
"""
    new_mmio = """	pr_err("talkman_csid tg mmio ctrl0=0x%x ctrl1=0x%x tg=0x%x vc=0x%x dt0=0x%x dt1=0x%x dt2=0x%x lut0=0x%x cid0=0x%x pkts=0x%x ecc=0x%x long=0x%x map=0x%x\\n",
"""
    if "tg mmio" in t and "long=0x%x map=0x%x" in t:
        print("csid tg mmio map already present")
    elif old_mmio in t:
        t = t.replace(old_mmio, new_mmio, 1)
        t = t.replace(
            """		msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_captured_long_pkt_hdr_addr));
	return rc;
""",
            """		msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_captured_long_pkt_hdr_addr),
		msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_captured_mmaped_long_pkt_hdr_addr));
	return rc;
""",
            1,
        )
        print("csid: tg mmio dump mapped hdr")
    else:
        print("WARN: tg mmio line not found for map hdr")

    CSID.write_text(t)


AFTER_I2C = r'''
static void talkman_smia_dump_csi(struct msm_sensor_ctrl_t *s_ctrl)
{
	static const uint16_t regs[] = {
		0x0100, 0x0104, 0x0110, 0x0111, 0x0112, 0x0114,
		0x034c, 0x034e, 0x0801
	};
	struct msm_camera_i2c_client *cl;
	uint16_t val;
	int rc, i;
	enum msm_camera_i2c_data_type dt;

	if (!s_ctrl || !s_ctrl->sensor_i2c_client ||
	    !s_ctrl->sensor_i2c_client->i2c_func_tbl)
		return;
	cl = s_ctrl->sensor_i2c_client;
	for (i = 0; i < ARRAY_SIZE(regs); i++) {
		val = 0xffff;
		dt = (regs[i] == 0x0112 || regs[i] == 0x034c ||
		      regs[i] == 0x034e) ?
			MSM_CAMERA_I2C_WORD_DATA :
			MSM_CAMERA_I2C_BYTE_DATA;
		rc = cl->i2c_func_tbl->i2c_read(cl, regs[i], &val, dt);
		pr_err("talkman_smia csi %s 0x%04x rc=%d val=0x%04x\n",
		       s_ctrl->sensordata->sensor_name, regs[i], rc, val);
	}
}

static void talkman_smia_after_i2c(struct msm_sensor_ctrl_t *s_ctrl,
	struct msm_camera_i2c_reg_setting *conf)
{
	struct msm_camera_i2c_client *cl;
	uint16_t model = 0, mode = 0, lanes = 0, want_stream = 0;
	uint16_t i;
	int rc;

	if (!s_ctrl || !s_ctrl->sensor_i2c_client ||
	    !s_ctrl->sensor_i2c_client->i2c_func_tbl || !conf ||
	    !conf->reg_setting)
		return;
	cl = s_ctrl->sensor_i2c_client;

	/* Skip grouped-hold-only tables; they are frequent and not CSI. */
	if (conf->size == 1 && conf->reg_setting[0].reg_addr == 0x0104)
		return;

	for (i = 0; i < conf->size; i++) {
		if (conf->reg_setting[i].reg_addr == 0x0100 &&
		    (conf->reg_setting[i].reg_data & 0xff) == 0x01)
			want_stream = 1;
	}

	/* SMIA 0x0111: 0 = CSI-2, 1 = CCP2. Qualcomm CSID is CSI-2 only. */
	rc = cl->i2c_func_tbl->i2c_write(cl, 0x0111, 0,
		MSM_CAMERA_I2C_BYTE_DATA);
	if (rc)
		pr_err("talkman_smia %s CSI-2 write rc=%d\n",
		       s_ctrl->sensordata->sensor_name, rc);

	rc = cl->i2c_func_tbl->i2c_read(cl, 0x0000, &model,
		MSM_CAMERA_I2C_WORD_DATA);
	if (!rc) {
		rc = cl->i2c_func_tbl->i2c_read(cl, 0x0114, &lanes,
			MSM_CAMERA_I2C_BYTE_DATA);
		if (!rc && model == 0xEACA && (lanes & 0xff) != 0x03) {
			cl->i2c_func_tbl->i2c_write(cl, 0x0114, 0x03,
				MSM_CAMERA_I2C_BYTE_DATA);
			pr_err("talkman_smia %s lane_mode 0x%x -> 4-lane\n",
			       s_ctrl->sensordata->sensor_name, lanes);
		} else if (!rc && model == 0x2140 && (lanes & 0xff) != 0x01) {
			cl->i2c_func_tbl->i2c_write(cl, 0x0114, 0x01,
				MSM_CAMERA_I2C_BYTE_DATA);
			pr_err("talkman_smia %s lane_mode 0x%x -> 2-lane\n",
			       s_ctrl->sensordata->sensor_name, lanes);
		}
	}

	if (want_stream) {
		mode = 0;
		rc = cl->i2c_func_tbl->i2c_read(cl, 0x0100, &mode,
			MSM_CAMERA_I2C_BYTE_DATA);
		if (rc || !(mode & 0x1)) {
			cl->i2c_func_tbl->i2c_write(cl, 0x0100, 1,
				MSM_CAMERA_I2C_BYTE_DATA);
			pr_err("talkman_smia %s forced stream-on (rc=%d val=0x%x)\n",
			       s_ctrl->sensordata->sensor_name, rc, mode);
			msleep(10);
		}
		talkman_smia_dump_csi(s_ctrl);
	} else if (conf->reg_setting[0].reg_addr == 0x0103) {
		talkman_smia_dump_csi(s_ctrl);
	}
}

'''

def patch_sensor():
    t = SENSOR.read_text()
    if "talkman_smia_after_i2c" not in t:
        needle = "static void talkman_smia_dump(struct msm_sensor_ctrl_t *s_ctrl)"
        if needle not in t:
            raise SystemExit("talkman_smia_dump not found")
        t = t.replace(needle, AFTER_I2C + needle, 1)
        print("sensor: inserted after_i2c + dump_csi")
    else:
        print("sensor: after_i2c already present")

    old32 = """		rc = s_ctrl->sensor_i2c_client->i2c_func_tbl->
			i2c_write_table(s_ctrl->sensor_i2c_client,
			&conf_array);
		if (!rc)
			talkman_smia_vfe_crop(s_ctrl);
		kfree(reg_setting);
"""
    new32 = """		rc = s_ctrl->sensor_i2c_client->i2c_func_tbl->
			i2c_write_table(s_ctrl->sensor_i2c_client,
			&conf_array);
		if (!rc) {
			talkman_smia_vfe_crop(s_ctrl);
			talkman_smia_after_i2c(s_ctrl, &conf_array);
		}
		kfree(reg_setting);
"""
    old64 = """		rc = s_ctrl->sensor_i2c_client->i2c_func_tbl->i2c_write_table(
			s_ctrl->sensor_i2c_client, &conf_array);
		if (!rc)
			talkman_smia_vfe_crop(s_ctrl);
		kfree(reg_setting);
"""
    new64 = """		rc = s_ctrl->sensor_i2c_client->i2c_func_tbl->i2c_write_table(
			s_ctrl->sensor_i2c_client, &conf_array);
		if (!rc) {
			talkman_smia_vfe_crop(s_ctrl);
			talkman_smia_after_i2c(s_ctrl, &conf_array);
		}
		kfree(reg_setting);
"""
    if "talkman_smia_after_i2c(s_ctrl, &conf_array)" in t:
        print("sensor: i2c hooks already present")
    else:
        if old32 not in t:
            raise SystemExit("config32 crop hook not found")
        if old64 not in t:
            raise SystemExit("config crop hook not found")
        t = t.replace(old32, new32, 1)
        t = t.replace(old64, new64, 1)
        print("sensor: hooked after_i2c on both WRITE_I2C_ARRAY paths")

    SENSOR.write_text(t)


def patch_ispif():
    t = ISPIF.read_text()
    old_cfg = """		cid_mask = msm_ispif_get_cids_mask_from_cfg(
				&params->entries[i]);
		msm_ispif_enable_intf_cids(ispif, intftype,
			cid_mask, vfe_intf, 1);
"""
    new_cfg = """		cid_mask = msm_ispif_get_cids_mask_from_cfg(
				&params->entries[i]);
		pr_err("talkman_ispif cfg vfe=%d intf=%d csid=%d cid_mask=0x%x crop=%d\\n",
			vfe_intf, intftype, params->entries[i].csid, cid_mask,
			params->entries[i].crop_enable);
		msm_ispif_enable_intf_cids(ispif, intftype,
			cid_mask, vfe_intf, 1);
"""
    if "talkman_ispif cfg vfe=" in t:
        print("ispif cfg log already present")
    elif old_cfg in t:
        t = t.replace(old_cfg, new_cfg, 1)
        print("ispif: log cid_mask/csid/intf")
    else:
        print("WARN: ispif enable_intf_cids block not found")

    old_sof = """	if (out[vfe_id].ispifIrqStatus0 &
			ISPIF_IRQ_STATUS_PIX_SOF_MASK) {
		ispif->sof_count[vfe_id].sof_cnt[PIX0]++;
	}
	if (out[vfe_id].ispifIrqStatus0 &
			ISPIF_IRQ_STATUS_RDI0_SOF_MASK) {
		ispif->sof_count[vfe_id].sof_cnt[RDI0]++;
	}
"""
    new_sof = """	if (out[vfe_id].ispifIrqStatus0 &
			ISPIF_IRQ_STATUS_PIX_SOF_MASK) {
		ispif->sof_count[vfe_id].sof_cnt[PIX0]++;
		pr_err_ratelimited("talkman_ispif PIX SOF vfe=%d n=%u st0=0x%x\\n",
			vfe_id, ispif->sof_count[vfe_id].sof_cnt[PIX0],
			out[vfe_id].ispifIrqStatus0);
	}
	if (out[vfe_id].ispifIrqStatus0 &
			ISPIF_IRQ_STATUS_RDI0_SOF_MASK) {
		ispif->sof_count[vfe_id].sof_cnt[RDI0]++;
		pr_err_ratelimited("talkman_ispif RDI0 SOF vfe=%d n=%u st0=0x%x\\n",
			vfe_id, ispif->sof_count[vfe_id].sof_cnt[RDI0],
			out[vfe_id].ispifIrqStatus0);
	}
"""
    if "talkman_ispif PIX SOF" in t:
        print("ispif PIX/RDI0 SOF log already present")
    elif old_sof in t:
        t = t.replace(old_sof, new_sof, 1)
        print("ispif: log PIX/RDI0 SOF")
    else:
        print("WARN: ispif PIX/RDI0 SOF block not found")

    ISPIF.write_text(t)


def main(phy_only=False):
    patch_csiphy()
    patch_csid()
    patch_ispif()
    if phy_only:
        print("apply-csi-sof done (phy only)")
        return
    patch_sensor()
    print("apply-csi-sof done")


if __name__ == "__main__":
    import sys

    main(phy_only="--phy-only" in sys.argv)
