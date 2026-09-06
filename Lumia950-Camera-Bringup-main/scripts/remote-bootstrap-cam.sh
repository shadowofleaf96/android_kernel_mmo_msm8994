#!/usr/bin/env bash
# One-time: copy kernel source, toolchain, and out_cam onto the build host.
# After this, remote-rebuild-cam.sh only syncs source deltas + compiles.
set -euo pipefail
# shellcheck source=remote-cam-lib.sh
source "$(cd "$(dirname "$0")" && pwd)/remote-cam-lib.sh"
load_remote_env
need_local_tree

echo "bootstrap $REMOTE_USER@$REMOTE_HOST:$REMOTE_ANDROID"
if ! ssh_ok; then
	echo "SSH failed. On this PC (WSL): ssh $REMOTE_USER@$REMOTE_HOST" >&2
	echo "must work without a password (ssh-copy-id)." >&2
	exit 1
fi

"${SSH[@]}" "mkdir -p '$REMOTE_ANDROID' '$REMOTE_ANDROID/toolchain'"

echo "== toolchain =="
"${RSH[@]}" "$LOCAL_TC/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_TC/"

echo "== kernel source =="
"${RSH[@]}" --delete \
	--exclude '.git/' \
	"$LOCAL_SRC/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_SRC/"

if [ -d "$LOCAL_OUT" ]; then
	echo "== out_cam (object tree; first copy is large, then builds are incremental) =="
	"${RSH[@]}" "$LOCAL_OUT/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_OUT/"
else
	echo "no local $LOCAL_OUT — remote first build will be a full compile"
fi

echo "BOOTSTRAP_OK"
echo "next: scripts/remote-rebuild-cam.sh"
