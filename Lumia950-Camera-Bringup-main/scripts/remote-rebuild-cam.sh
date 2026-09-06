#!/usr/bin/env bash
# Sync camera kernel sources to the build host, compile there, copy Image.gz-dtb back.
# Cursor, apply-*.py, bootimg.py, and adb stay on this Windows PC.
set -euo pipefail
# shellcheck source=remote-cam-lib.sh
source "$(cd "$(dirname "$0")" && pwd)/remote-cam-lib.sh"
load_remote_env
need_local_tree

echo "remote rebuild $REMOTE_USER@$REMOTE_HOST -j$REMOTE_JOBS $(date -Is)"
if ! ssh_ok; then
	echo "SSH failed for $REMOTE_USER@$REMOTE_HOST" >&2
	exit 1
fi

echo "== rsync source =="
"${RSH[@]}" --delete \
	--exclude '.git/' \
	"$LOCAL_SRC/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_SRC/"

echo "== make olddefconfig Image.gz dtbs =="
"${SSH[@]}" env \
	ARCH=arm64 SUBARCH=arm64 \
	"CROSS_COMPILE=$REMOTE_TC/bin/aarch64-linux-gnu-" \
	bash -s <<EOF
set -euo pipefail
mkdir -p '$REMOTE_OUT'
make -C '$REMOTE_SRC' O='$REMOTE_OUT' olddefconfig
# Ident is smia65pp over CCI. Do not build the 3.10 i2c smiapp driver.
if grep -q '^CONFIG_VIDEO_SMIAPP=y$' '$REMOTE_OUT/.config' 2>/dev/null; then
	sed -i 's/^CONFIG_VIDEO_SMIAPP=y$/# CONFIG_VIDEO_SMIAPP is not set/' \
		'$REMOTE_OUT/.config'
	make -C '$REMOTE_SRC' O='$REMOTE_OUT' olddefconfig
fi
rm -f '$REMOTE_OUT/arch/arm64/boot/dts/msm8992-mmo-talkman.dtb' \
      '$REMOTE_OUT/arch/arm64/boot/dts/mmo/msm8992-mmo-talkman.dtb'
make -C '$REMOTE_SRC' O='$REMOTE_OUT' -j'$REMOTE_JOBS' Image.gz dtbs
IMAGE='$REMOTE_OUT/arch/arm64/boot/Image.gz'
DTB='$REMOTE_OUT/arch/arm64/boot/dts/mmo/msm8992-mmo-talkman.dtb'
[ -f "\$DTB" ] || DTB='$REMOTE_OUT/arch/arm64/boot/dts/msm8992-mmo-talkman.dtb'
cat "\$IMAGE" "\$DTB" > '$REMOTE_IMAGE'
ls -l '$REMOTE_IMAGE'
echo KERNEL_CAM_BUILD_DONE
EOF

echo "== fetch Image.gz-dtb-cam =="
mkdir -p "$CAM_ROOT/out"
scp -o BatchMode=yes -o ConnectTimeout=8 \
	"$REMOTE_USER@$REMOTE_HOST:$REMOTE_IMAGE" \
	"$LOCAL_IMAGE"
cp -f "$LOCAL_IMAGE" "$CAM_ROOT/out/Image.gz-dtb-cam"
ls -l "$LOCAL_IMAGE" "$CAM_ROOT/out/Image.gz-dtb-cam"
echo REMOTE_CAM_BUILD_DONE
