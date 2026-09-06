#!/usr/bin/env python3
"""#104: HAL reaches 0x0100=1 only while CSID TG supplies SOF. After stream
is up, turn TG off so CSID takes the PHY (pwr=0x3f, 0xdd irqs = live MIPI).
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

CSID = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csid/msm_csid.c"


def main() -> None:
    t = CSID.read_text()
    old_stay = """		pr_err("talkman_csid tg stay on (lane sweep; no PIX SOF)\\n");
"""
    new_off = """		/* Sample PHY after HAL has SOF. Daily image stays 113. */
		talkman_tg_off_dev = csid_dev;
		schedule_delayed_work(&talkman_tg_off_dwork,
			msecs_to_jiffies(800));
		pr_err("talkman_csid tg will off WP 0xa06436 in 800ms\\n");
"""
    if old_stay in t:
        CSID.write_text(t.replace(old_stay, new_off, 1))
        print("csid: schedule TG off 800ms (CSI sample)")
        return
    if "talkman_csid tg will off WP 0xa06436" in t:
        print("csid TG auto-off already scheduled")
        return
    old_en = """		pr_err("talkman_csid tg enable 0xa06437\\n");
	} else {"""
    new_en = """		pr_err("talkman_csid tg enable 0xa06437\\n");
		/* #113 analog b04x stuck. Sample PHY after HAL has SOF. */
		talkman_tg_off_dev = csid_dev;
		schedule_delayed_work(&talkman_tg_off_dwork,
			msecs_to_jiffies(800));
		pr_err("talkman_csid tg will off WP 0xa06436 in 800ms\\n");
	} else {"""
    if old_en in t:
        if "static DECLARE_DELAYED_WORK(talkman_tg_off_dwork" not in t:
            raise SystemExit("tg-off work missing")
        CSID.write_text(t.replace(old_en, new_en, 1))
        print("csid: schedule TG off 800ms (#113 analog b04x)")
        return
    old_zero = """	msm_camera_io_w(0, csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr);
	pr_err("talkman_csid tg off after stream was=0x%x now=0x%x\\n",
		was, msm_camera_io_r(csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr));
"""
    new_wp = """	/* WP FUN_0041ddd4 writes 0xa06436 (bit0 clear). Zeroing the
	 * whole TG_CTRL killed PIX SOF (#105/#106). */
	msm_camera_io_w(0x00A06436, csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr);
	pr_err("talkman_csid tg off WP 0xa06436 was=0x%x now=0x%x pkts=0x%x ecc=0x%x crc=0x%x long=0x%x\\n",
		was, msm_camera_io_r(csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr),
		msm_camera_io_r(csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_stats_total_pkts_rcvd_addr),
		msm_camera_io_r(csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_stats_ecc_addr),
		msm_camera_io_r(csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_stats_crc_addr),
		msm_camera_io_r(csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_captured_long_pkt_hdr_addr));
"""
    old_off = """		/* #109 analog stuck. Sample PHY after HAL has SOF. */
		talkman_tg_off_dev = csid_dev;
		schedule_delayed_work(&talkman_tg_off_dwork,
			msecs_to_jiffies(800));
		pr_err("talkman_csid tg will off WP 0xa06436 in 800ms\\n");
"""
    new_stay = """		pr_err("talkman_csid tg stay on (PHY 0x20000dd)\\n");
"""
    if "talkman_csid tg stay on (PHY 0x20000dd)" in t and old_off not in t:
        print("csid TG stay-on already present")
        return
    if old_off in t:
        CSID.write_text(t.replace(old_off, new_stay, 1))
        print("csid: TG stay on (analog/settle did not fix PHY)")
        return
    if "talkman_csid tg will off WP 0xa06436" in t:
        raise SystemExit("tg-off schedule present but pattern missing")

    if old_zero in t:
        CSID.write_text(t.replace(old_zero, new_wp, 1))
        print("csid: TG off = WP 0xa06436 (not 0)")
        return

    if "talkman_csid tg off after stream" in t:
        raise SystemExit("tg-off work present but zero-write pattern missing")

    if "#include <linux/workqueue.h>" not in t:
        t = t.replace(
            "#include <linux/delay.h>\n",
            "#include <linux/delay.h>\n#include <linux/workqueue.h>\n",
            1,
        )
        print("csid: workqueue.h")

    old_parm = """MODULE_PARM_DESC(tg_mode, "CSID TG payload 2:0 (1=incrementing)");


#define TRUE   1
"""
    new_parm = """MODULE_PARM_DESC(tg_mode, "CSID TG payload 2:0 (1=incrementing)");

static struct csid_device *talkman_tg_off_dev;
static void talkman_csid_tg_off_work(struct work_struct *work)
{
	struct csid_device *csid_dev = talkman_tg_off_dev;
	uint32_t was;

	if (!csid_dev || !csid_dev->base ||
	    csid_dev->csid_state != CSID_POWER_UP)
		return;
	was = msm_camera_io_r(csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr);
	msm_camera_io_w(0x00A06436, csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr);
	pr_err("talkman_csid tg off WP 0xa06436 was=0x%x now=0x%x pkts=0x%x ecc=0x%x crc=0x%x long=0x%x\\n",
		was, msm_camera_io_r(csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr),
		msm_camera_io_r(csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_stats_total_pkts_rcvd_addr),
		msm_camera_io_r(csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_stats_ecc_addr),
		msm_camera_io_r(csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_stats_crc_addr),
		msm_camera_io_r(csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_captured_long_pkt_hdr_addr));
	/* After TG, try clock on phy0 (assign 0x4321). TG needed 0x4320. */
	msm_camera_io_w(0x43213, csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_0_addr);
	pr_err("talkman_csid after off ctrl0=0x%x (0x4321 clk phy0)\\n",
		msm_camera_io_r(csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_0_addr));
}
static DECLARE_DELAYED_WORK(talkman_tg_off_dwork, talkman_csid_tg_off_work);

#define TRUE   1
"""
    if old_parm not in t:
        raise SystemExit("tg_mode MODULE_PARM_DESC not found")
    t = t.replace(old_parm, new_parm, 1)
    print("csid: TG auto-off work")

    old_en = """		msm_camera_io_w(0x00A06437, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr);
		pr_err("talkman_csid tg enable 0xa06437\\n");
"""
    new_en = """		msm_camera_io_w(0x00A06437, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr);
		pr_err("talkman_csid tg enable 0xa06437\\n");
		talkman_tg_off_dev = csid_dev;
		schedule_delayed_work(&talkman_tg_off_dwork,
			msecs_to_jiffies(800));
"""
    if old_en not in t:
        raise SystemExit("tg enable block not found")
    t = t.replace(old_en, new_en, 1)
    print("csid: schedule TG off 800ms after enable")

    old_rel = """static int msm_csid_release(struct csid_device *csid_dev)
{
	uint32_t irq;

	if (csid_dev->csid_state != CSID_POWER_UP) {
"""
    new_rel = """static int msm_csid_release(struct csid_device *csid_dev)
{
	uint32_t irq;

	cancel_delayed_work_sync(&talkman_tg_off_dwork);
	if (talkman_tg_off_dev == csid_dev)
		talkman_tg_off_dev = NULL;

	if (csid_dev->csid_state != CSID_POWER_UP) {
"""
    if old_rel not in t:
        raise SystemExit("msm_csid_release not found")
    t = t.replace(old_rel, new_rel, 1)
    print("csid: cancel TG off on release")

    CSID.write_text(t)


if __name__ == "__main__":
    main()
