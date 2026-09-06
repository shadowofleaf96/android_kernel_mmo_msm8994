#!/usr/bin/env python3
"""After a talkman camera flash: wait for boot, wake/unlock, open Open Camera
once (retry if HAL stops at tables 1-5), save dmesg + screenshot.

Open Camera: swipe-up opens Settings. Never swipe after the app is in
the foreground. Unlock is wakeup + wm dismiss-keyguard; one short swipe
only if the keyguard is still showing.

Usage:
  python scripts/ocam-dump.py preview-k61
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

SERIAL = os.environ.get("ANDROID_SERIAL", "").strip()
if not SERIAL:
    sys.exit("set ANDROID_SERIAL to the adb device serial")
SU = "/debug_ramdisk/su"
PKG = "net.sourceforge.opencamera"
ACTIVITY = "net.sourceforge.opencamera/.MainActivity"
CAM_ROOT = Path(__file__).resolve().parents[1]
KEEP = (
    "talkman_smia",
    "talkman_csid",
    "talkman_ispif",
    "talkman_vfe",
    "talkman_csiphy",
    "talkman_cgc",
    "talkman_mmcc",
    "talkman_tcsr",
    "tg off after",
    "tg will off",
    "camif error",
    "smiapp:",
    "colorbars",
    "WRITE_I2C",
    "CFG_STREAM",
    "0x0100",
    "0x0100=1 early",
    "WP disable",
    "2-lane",
    "dphy analog",
    "wpmap",
    "supplies",
    "0130",
    "4800",
    "0136",
    "31a8",
    "link_rate",
    "PHY_OVR",
    " ECC",
    "ctrl1=",
    "skip colorbars",
    "dphy_register",
    "overflow",
    "iommu",
    "page fault",
    "FAR",
)


def adb(*args: str, check: bool = True, timeout: int = 60) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["adb", "-s", SERIAL, *args],
            check=check,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.CalledProcessError:
        if check:
            raise
        return subprocess.CompletedProcess(args, 1, "", "")
    except subprocess.TimeoutExpired:
        if check:
            raise
        return subprocess.CompletedProcess(args, 1, "", "")


def adb_bin(*args: str, timeout: int = 60) -> bytes:
    p = subprocess.run(
        ["adb", "-s", SERIAL, *args],
        check=True,
        capture_output=True,
        timeout=timeout,
    )
    return p.stdout


def sh(cmd: str, check: bool = True, timeout: int = 60) -> str:
    p = adb("shell", cmd, check=check, timeout=timeout)
    return (p.stdout or "") + (p.stderr or "")


def wait_boot(timeout_s: int = 300) -> None:
    adb("wait-for-device", timeout=timeout_s)
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            if sh("getprop sys.boot_completed").strip() == "1":
                return
        except subprocess.CalledProcessError:
            pass
        time.sleep(2)
    raise SystemExit("boot_completed never became 1")


def dmesg() -> str:
    adb("shell", SU, "-M", "-c",
        "dmesg > /data/local/tmp/talkman-dmesg.txt", check=False, timeout=60)
    p = adb("exec-out", "cat", "/data/local/tmp/talkman-dmesg.txt",
            check=False, timeout=60)
    if p.returncode == 0 and (p.stdout or "").strip():
        return p.stdout
    p = adb("shell", SU, "-M", "-c", "dmesg", check=False, timeout=120)
    return p.stdout or ""


def stay_awake() -> None:
    sh("svc power stayon true", check=False)
    sh("input keyevent 224", check=False)  # KEYCODE_WAKEUP


def keyguard_up() -> bool:
    # displays dump is smaller than full dumpsys window.
    out = sh("dumpsys window displays", check=False, timeout=20)
    return "isKeyguardShowing=true" in out


def wake_unlock() -> None:
    """Unlock before any camera UI. Do not swipe once Open Camera is up."""
    stay_awake()
    time.sleep(0.4)
    sh("wm dismiss-keyguard", check=False)
    time.sleep(0.4)
    if not keyguard_up():
        return
    print("keyguard still up after dismiss-keyguard, one short swipe")
    # Short swipe: lockscreen only. Full-screen swipe-up opens OC settings.
    sh("input swipe 720 1900 720 1100 200", check=False)
    time.sleep(0.4)


def streamed(text: str, before: str = "") -> bool:
    """True when this boot produced a new stream-on after `before`."""
    for marker in ("0x0100=1 after_phy", "0x0100 skipped tg-isolate",
                   "0x0100 forced 0 tg-isolate",                    "0x0100 left to HAL",
                   "START_STREAM rc=", "talkman_smia START_STREAM",
                   "0x0100=1 early", "tg WP disable", "dphy analog",
                   "tg enable", "supplies"):
        if text.count(marker) > before.count(marker):
            return True
    return False


def open_camera() -> None:
    sh(f"am force-stop {PKG}", check=False)
    time.sleep(1.2)
    p = adb("shell", "am", "start", "-n", ACTIVITY, check=False, timeout=15)
    print((p.stdout or "") + (p.stderr or ""), end="")


def save_dump(tag: str, text: str, png: bytes | None) -> Path:
    out = CAM_ROOT / "out"
    out.mkdir(exist_ok=True)
    uname = sh("uname -a", check=False).strip()
    n0100 = 0
    lines = []
    for ln in text.splitlines():
        if not any(k in ln for k in KEEP):
            continue
        if "0x0100" in ln or "after_phy" in ln or "dphy cap=" in ln:
            n0100 += 1
            if n0100 > 8:
                continue
        lines.append(ln)
    txt = out / f"{tag}.txt"
    txt.write_text(
        f"=== uname ===\n{uname}\n=== dmesg talkman ===\n" + "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    if png:
        (out / f"{tag}.png").write_bytes(png)
        print(f"wrote {txt} and {out / (tag + '.png')}")
    else:
        print(f"wrote {txt} (no screenshot)")
    return txt


def main() -> int:
    tag = sys.argv[1] if len(sys.argv) > 1 else "preview"
    print(f"ocam-dump {tag} serial={SERIAL}")
    wait_boot()
    print("boot_completed=1")

    for _ in range(45):
        dm = dmesg()
        if "qcamera slot bind rc=0" in dm:
            print("ident+slot bind seen, wait 8s for daemon")
            time.sleep(8)
            break
        time.sleep(1)
    else:
        print("WARN: no slot bind yet, continuing")

    # HAL3 (QCamera3) times out capture requests. HAL1 paints preview.
    adb("shell", SU, "-M", "-c",
        "setprop persist.camera.HAL3.enabled 0", check=False)
    print("persist.camera.HAL3.enabled=0")
    adb("shell", SU, "-M", "-c", "setprop ctl.restart qcamerasvr", check=False)
    time.sleep(2)
    adb("shell", SU, "-M", "-c", "setprop ctl.restart cameraserver", check=False)
    time.sleep(4)
    # Grey Open Camera: cameraserver D-state in msm_post_event.
    for _ in range(8):
        ps = sh("ps -A", check=False, timeout=15)
        stuck = any(
            "cameraserver" in ln and " msm_post_event " in ln
            for ln in ps.splitlines()
        )
        if not stuck:
            break
        print("cameraserver stuck in msm_post_event, restart again")
        adb("shell", SU, "-M", "-c", "setprop ctl.restart cameraserver",
            check=False)
        time.sleep(3)

    wake_unlock()
    if keyguard_up():
        print("keyguard still showing after ADB unlock — need a PIN/swipe from you")
        save_dump(tag, dmesg(), None)
        return 2

    def grab_png() -> bytes | None:
        try:
            png = adb_bin("exec-out", "screencap", "-p", timeout=20)
            if png[:8] != b"\x89PNG\r\n\x1a\n" and b"PNG" not in png[:16]:
                print("screencap did not return a PNG")
                return None
            return png
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"screencap failed: {e}")
            return None

    baseline = dmesg()
    ok = False
    tgon_png = None
    for attempt in range(1, 4):
        print(f"Open Camera attempt {attempt}")
        stay_awake()
        open_camera()
        # TG stays on 12s this flash. Grab a frame while CID0 can map.
        t0 = time.time()
        while time.time() - t0 < 14:
            dm = dmesg()
            if "talkman_csid tg enable" in dm and dm.count(
                    "talkman_csid tg enable") > baseline.count(
                    "talkman_csid tg enable"):
                tgon_png = grab_png()
                if tgon_png:
                    p = CAM_ROOT / "out" / f"{tag}-tgon.png"
                    p.write_bytes(tgon_png)
                    print(f"TG-on screencap {p}")
                break
            time.sleep(0.2)
        time.sleep(5)
        dm = dmesg()
        if streamed(dm, baseline):
            print("stream-on seen, wait 5s for CSID stats (stay in Open Camera)")
            time.sleep(5)
            ok = True
            break
        print("no new 0x0100=1, force-stop and retry")
        sh(f"am force-stop {PKG}", check=False)
        baseline = dm
        time.sleep(3)

    stay_awake()
    dm_final = dmesg()
    png = grab_png()
    save_dump(tag, dm_final, png)
    print("stream_ok" if ok else "stream_missing")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
