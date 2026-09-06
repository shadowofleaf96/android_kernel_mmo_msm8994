#!/usr/bin/env bash
# Incremental talkman kernel build: Hill smia65pp + camera DT.
set -euo pipefail
ROOT="${KERNEL_TREE:-$HOME/android}/.."
# KERNEL_TREE is the git checkout; parent holds out_cam + toolchain in the
# lab layout. Override with ANDROID_BUILD_ROOT if needed.
ROOT="${ANDROID_BUILD_ROOT:-$HOME/android}"
SRC="${KERNEL_TREE:-$ROOT/mmo_msm8994_talkman}"
OUT=$ROOT/out_cam
TC=$ROOT/toolchain/gcc-arm-8.3-2019.03-x86_64-aarch64-linux-gnu
export ARCH=arm64
export SUBARCH=arm64
export CROSS_COMPILE=$TC/bin/aarch64-linux-gnu-

echo "cam build start $(date -Is)"
echo "src=$(git -C "$SRC" rev-parse --abbrev-ref HEAD) $(git -C "$SRC" rev-parse --short HEAD)"

if [ ! -d "$OUT" ]; then
  echo "copying out_fw to out_cam"
  cp -a "$ROOT/out_fw" "$OUT"
  echo COPY_OK
fi

if ! grep -q '^CONFIG_SMIA65PP=y' "$OUT/.config"; then
  echo 'CONFIG_SMIA65PP=y' >> "$OUT/.config"
  echo "appended CONFIG_SMIA65PP=y"
fi

make -C "$SRC" O="$OUT" olddefconfig
grep -E 'CONFIG_SMIA65PP|VIDEO_SMIAPP|MSMB_CAMERA' "$OUT/.config" || true

rm -f "$OUT/arch/arm64/boot/dts/msm8992-mmo-talkman.dtb" \
      "$OUT/arch/arm64/boot/dts/mmo/msm8992-mmo-talkman.dtb"

echo "rebuild start $(date -Is) jobs=4"
make -C "$SRC" O="$OUT" -j4 Image.gz dtbs

IMAGE="$OUT/arch/arm64/boot/Image.gz"
DTB="$OUT/arch/arm64/boot/dts/mmo/msm8992-mmo-talkman.dtb"
if [ ! -f "$DTB" ]; then
  DTB="$OUT/arch/arm64/boot/dts/msm8992-mmo-talkman.dtb"
fi
ls -l "$IMAGE" "$DTB"
strings "$DTB" | grep -E 'qcom,camera|CAMIF_MCLK|CAM_RESET' || true
if strings "$DTB" | grep -q 'imx214\|ov5648\|s5k3m2'; then
  echo "WARNING: MTP camera strings still in DTB" >&2
fi

cat "$IMAGE" "$DTB" > "$ROOT/Image.gz-dtb-cam"
ls -l "$ROOT/Image.gz-dtb-cam"
echo KERNEL_CAM_BUILD_DONE
echo "cam build end $(date -Is)"
