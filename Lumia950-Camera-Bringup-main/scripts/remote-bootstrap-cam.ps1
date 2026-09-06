# One-time copy of kernel tree + toolchain + out_cam to the build host.
$ErrorActionPreference = "Stop"
$script = Join-Path $PSScriptRoot "remote-bootstrap-cam.sh"
$wslPath = (wsl -e wslpath -a $script).Trim()
wsl -e bash $wslPath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
