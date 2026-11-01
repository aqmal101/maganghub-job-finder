$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

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

Write-Host "Menjalankan MagangHub Job Finder API..."
Write-Host "API : http://127.0.0.1:8000"
Write-Host "Docs: http://127.0.0.1:8000/docs"
Write-Host "Tekan Ctrl+C untuk menghentikan server."

& $python -m uvicorn backend.app.main:app --reload
