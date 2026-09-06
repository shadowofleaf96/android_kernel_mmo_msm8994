# Shared paths for remote camera kernel builds. Sourced by the other scripts.
# shellcheck shell=bash

CAM_SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CAM_ROOT="$(cd "$CAM_SCRIPTS/.." && pwd)"
ENV_FILE="$CAM_SCRIPTS/remote-cam.env"

LOCAL_ANDROID="${LOCAL_ANDROID:-$HOME/android}"
LOCAL_SRC="$LOCAL_ANDROID/mmo_msm8994_talkman"
LOCAL_OUT="$LOCAL_ANDROID/out_cam"
LOCAL_TC="$LOCAL_ANDROID/toolchain/gcc-arm-8.3-2019.03-x86_64-aarch64-linux-gnu"
LOCAL_IMAGE="$LOCAL_ANDROID/Image.gz-dtb-cam"

load_remote_env() {
	if [ ! -f "$ENV_FILE" ]; then
		echo "missing $ENV_FILE" >&2
		echo "copy scripts/remote-cam.env.example to scripts/remote-cam.env" >&2
		exit 1
	fi
	# shellcheck disable=SC1090
	source "$ENV_FILE"
	: "${REMOTE_HOST:?set REMOTE_HOST in remote-cam.env}"
	: "${REMOTE_USER:?set REMOTE_USER in remote-cam.env}"
	REMOTE_ANDROID="${REMOTE_ANDROID:-$HOME/android}"
	REMOTE_JOBS="${REMOTE_JOBS:-20}"
	REMOTE_SRC="$REMOTE_ANDROID/mmo_msm8994_talkman"
	REMOTE_OUT="$REMOTE_ANDROID/out_cam"
	REMOTE_TC="$REMOTE_ANDROID/toolchain/gcc-arm-8.3-2019.03-x86_64-aarch64-linux-gnu"
	REMOTE_IMAGE="$REMOTE_ANDROID/Image.gz-dtb-cam"
	SSH=(ssh -o BatchMode=yes -o ConnectTimeout=8 "$REMOTE_USER@$REMOTE_HOST")
	RSH=(rsync -az --info=name0 -e "ssh -o BatchMode=yes -o ConnectTimeout=8")
}

need_local_tree() {
	[ -d "$LOCAL_SRC" ] || {
		echo "local kernel tree missing: $LOCAL_SRC" >&2
		exit 1
	}
	[ -x "$LOCAL_TC/bin/aarch64-linux-gnu-gcc" ] || {
		echo "local toolchain missing: $LOCAL_TC" >&2
		exit 1
	}
}

ssh_ok() {
	"${SSH[@]}" true
}
