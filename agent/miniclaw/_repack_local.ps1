$src = Join-Path $PSScriptRoot 'miniclaw-executor'
$out = Join-Path $PSScriptRoot 'miniclaw-executor.zip'
$tmp = Join-Path $PSScriptRoot '_zip_tmp'

if (Test-Path $out) { Remove-Item $out -Force }
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }

Copy-Item $src $tmp -Recurse

Remove-Item (Join-Path $tmp 'app\credentials\auth-profiles.json') -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $tmp 'app\server.js') -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $tmp 'app\skills_manager.js') -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $tmp 'app\server.js.bak') -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $tmp 'app\node_modules') -Recurse -Force -ErrorAction SilentlyContinue

Compress-Archive -Path "$tmp\*" -DestinationPath $out -Force
Remove-Item $tmp -Recurse -Force

Write-Host "Done. Size: $([math]::Round((Get-Item $out).Length/1KB)) KB"