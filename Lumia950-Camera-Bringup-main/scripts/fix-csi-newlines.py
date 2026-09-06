from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()
from pathlib import Path

p = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/msm_sensor.c"
t = p.read_text()
# Raw-string insert wrote C "\\n" (backslash + n) instead of newline escape.
fixed = t.replace("\\\\n", "\\n")
# Only the new talkman_smia after_i2c logs should have had double escapes.
# If we accidentally doubled real "\\n" sequences elsewhere, stop.
if t.count("\\\\n") == 0:
    print("already clean")
else:
    # Safer: only touch lines containing talkman_smia and a format string.
    lines = []
    n = 0
    for line in t.splitlines(True):
        if "talkman_smia" in line and "\\\\n" in line:
            line = line.replace("\\\\n", "\\n")
            n += 1
        lines.append(line)
    p.write_text("".join(lines))
    print(f"fixed {n} format strings")
