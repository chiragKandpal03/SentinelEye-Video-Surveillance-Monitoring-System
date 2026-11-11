Add-Type -AssemblyName System.Windows.Forms

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$videoDir = Join-Path $projectRoot 'python-ai'
$python = Join-Path $videoDir '.venv\Scripts\python.exe'

if (-not (Test-Path $python)) {
    Write-Host 'Python virtual environment not found. Set up python-ai\.venv first.' -ForegroundColor Red
    Read-Host 'Press Enter to close'
    exit 1
}

$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = 'Choose an image or video to analyze'
$dialog.Filter = 'Images and videos|*.jpg;*.jpeg;*.png;*.bmp;*.webp;*.tif;*.tiff;*.mp4;*.avi;*.mov;*.mkv;*.wmv;*.m4v|All files|*.*'
$dialog.InitialDirectory = [Environment]::GetFolderPath('MyVideos')
if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
    exit 0
}

try {
    $health = Invoke-RestMethod -Uri 'http://localhost:8080/api/health' -TimeoutSec 3
    if ($health.status -ne 'ok') { throw 'Unexpected health response' }
} catch {
    Write-Host 'Backend is not running. Start it first, then run this shortcut again.' -ForegroundColor Red
    Read-Host 'Press Enter to close'
    exit 1
}

Write-Host "Analyzing: $($dialog.FileName)"
Set-Location $videoDir
& $python 'detector.py' '--source' $dialog.FileName '--fire-model' '..\models\fire_smoke.pt' '--weapon-model' '..\models\weapons.pt'
Write-Host 'Analysis ended.'
Read-Host 'Press Enter to close'
