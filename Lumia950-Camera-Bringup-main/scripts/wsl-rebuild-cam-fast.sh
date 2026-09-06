#!/usr/bin/env bash
set -euo pipefail
ROOT="${ANDROID_BUILD_ROOT:-$HOME/android}"
SRC="${KERNEL_TREE:-$ROOT/mmo_msm8994_talkman}"
OUT=$ROOT/out_cam
TC=$ROOT/toolchain/gcc-arm-8.3-2019.03-x86_64-aarch64-linux-gnu
export ARCH=arm64 SUBARCH=arm64
export CROSS_COMPILE=$TC/bin/aarch64-linux-gnu-
echo "fast rebuild start $(date -Is)"
rm -f "$OUT/arch/arm64/boot/dts/msm8992-mmo-talkman.dtb"
make -C "$SRC" O="$OUT" -j4 Image.gz dtbs
IMAGE="$OUT/arch/arm64/boot/Image.gz"
DTB="$OUT/arch/arm64/boot/dts/mmo/msm8992-mmo-talkman.dtb"
[ -f "$DTB" ] || DTB="$OUT/arch/arm64/boot/dts/msm8992-mmo-talkman.dtb"
cat "$IMAGE" "$DTB" > "$ROOT/Image.gz-dtb-cam"
ls -l "$ROOT/Image.gz-dtb-cam"
echo KERNEL_CAM_BUILD_DONE
