$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== MYgene Development Server ==="
Write-Host "Checking MariaDB..."

sudo service mariadb start
if ($LASTEXITCODE -ne 0) { throw "MariaDB start failed" }

$dbCount = sudo mariadb -N -B -e "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME IN ('mygene','mygene_logs');"
if ($LASTEXITCODE -ne 0 -or "$dbCount".Trim() -ne "2") {
    throw "MYgene databases unavailable"
}

Write-Host "MYgene databases: READY"

$services = @("login-server","char-server","map-server","web-server")

function Get-RunningCount {
    $output = @(bash ./athena-start status)
    if ($LASTEXITCODE -ne 0) { throw "Status check failed" }

    $count = 0
    foreach ($name in $services) {
        if (@($output | Where-Object { $_.StartsWith("'$name' is running") }).Count -eq 1) {
            $count++
        }
    }
    return $count
}

$running = Get-RunningCount

if ($running -eq 0) {
    Write-Host "Starting MYgene Ragnarok..."
    bash ./athena-start start --enlog
    if ($LASTEXITCODE -ne 0) { throw "Ragnarok startup failed" }
    Start-Sleep -Seconds 8
} elseif ($running -eq 4) {
    Write-Host "All four servers are already running."
} else {
    throw "Only $running of 4 services running. Inspect before restarting."
}

bash ./athena-start status
if ($LASTEXITCODE -ne 0) { throw "Final status check failed" }

if ((Get-RunningCount) -ne 4) {
    throw "MYgene is not fully running. Check server logs."
}

Write-Host "MYgene Development Server: READY!"
