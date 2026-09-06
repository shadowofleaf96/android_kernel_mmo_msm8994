# Run from Windows / Cursor. Uses WSL ssh+rsync against the build host.
$ErrorActionPreference = "Stop"
$script = Join-Path $PSScriptRoot "remote-rebuild-cam.sh"
$wslPath = (wsl -e wslpath -a $script).Trim()
wsl -e bash $wslPath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
