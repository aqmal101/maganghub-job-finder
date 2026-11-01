$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$frontendRoot = Join-Path $projectRoot "frontend"

if (-not (Test-Path $python)) {
    Write-Host "Virtual environment tidak ditemukan. Membuat .venv..."
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        throw "Gagal membuat virtual environment."
    }
}

Write-Host "Memastikan dependency tersedia..."
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    throw "Gagal memasang dependency."
}

if (-not (Test-Path (Join-Path $frontendRoot "node_modules"))) {
    Write-Host "Memasang dependency frontend..."
    Push-Location $frontendRoot
    npm install
    $frontendInstallCode = $LASTEXITCODE
    Pop-Location
    if ($frontendInstallCode -ne 0) {
        throw "Gagal memasang dependency frontend."
    }
}

$backendProcess = $null
$frontendProcess = $null

try {
    Write-Host "Menjalankan MagangHub Job Finder..."
    $backendProcess = Start-Process `
        -FilePath $python `
        -ArgumentList "-m", "uvicorn", "backend.app.main:app", "--reload", "--port", "8000" `
        -WorkingDirectory $projectRoot `
        -PassThru

    $frontendProcess = Start-Process `
        -FilePath "npm.cmd" `
        -ArgumentList "run", "dev" `
        -WorkingDirectory $frontendRoot `
        -PassThru

    Write-Host "API      : http://127.0.0.1:8000"
    Write-Host "Frontend : http://127.0.0.1:3000"
    Write-Host "Docs     : http://127.0.0.1:8000/docs"
    Write-Host "Tekan Enter untuk menghentikan kedua aplikasi."
    Read-Host
}
finally {
    if ($frontendProcess -and -not $frontendProcess.HasExited) {
        Stop-Process -Id $frontendProcess.Id -Force
    }
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force
    }
}
