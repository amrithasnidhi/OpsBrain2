Write-Host "Starting OpsBrain2 Integration Setup..."

# Load env vars from app/frontend/.env
Get-Content "app\frontend\.env" | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.+)$') {
        [System.Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), "Process")
    }
}

# 1. Start Backend
Write-Host "Setting up backend..."
Set-Location app\backend
pip install -r requirements.txt | Out-Null
$backend = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    .\..\..\venv\Scripts\python.exe -m uvicorn main:app --reload
}
Set-Location ..\..

# 2. Start Frontend
Write-Host "Setting up frontend..."
Set-Location app\frontend
npm install | Out-Null
$frontend = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    npm.cmd run dev
}
Set-Location ..\..

Write-Host ""
Write-Host "OpsBrain2 is running!"
Write-Host "  Backend:  http://127.0.0.1:8000"
Write-Host "  Frontend: http://localhost:5173"
Write-Host ""
Write-Host "Press Ctrl+C to stop both servers."

try {
    while ($true) {
        Receive-Job -Job $backend, $frontend
        Start-Sleep -Seconds 2
    }
} finally {
    Write-Host "Stopping servers..."
    Stop-Job -Job $backend, $frontend
    Remove-Job -Job $backend, $frontend
    Write-Host "Done."
}
