$start = Get-Location
Set-Location $PSScriptRoot
try {
    uv run cxfreeze build
}
finally {
    Set-Location $start
}

