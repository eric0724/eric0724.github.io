$src = Join-Path $PSScriptRoot 'miniclaw-executor'
$tmp = Join-Path $PSScriptRoot '_zip_tmp'
$out = Join-Path $PSScriptRoot 'miniclaw-executor.zip'

if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
if (Test-Path $out) { Remove-Item $out -Force }

Copy-Item $src $tmp -Recurse

# 排除敏感/暫存檔案
Remove-Item (Join-Path $tmp 'app\credentials\auth-profiles.json') -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $tmp 'app\server.js.bak') -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $tmp 'app\node_modules') -Recurse -Force -ErrorAction SilentlyContinue

Compress-Archive -Path "$tmp\*" -DestinationPath $out -Force
Remove-Item $tmp -Recurse -Force

Write-Host "Done. Size: $([math]::Round((Get-Item $out).Length/1KB)) KB"