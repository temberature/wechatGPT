do {
    python .\screenshot.py 2>&1 | ForEach-Object {
        Write-Host $_ -NoNewline
        Add-Content -Path "output.log" -Value $_ -NoNewline
    }
    Write-Host ""
    Add-Content -Path "output.log" -Value ""
    $exitCode = $LASTEXITCODE
} while ($exitCode -ne 0)
