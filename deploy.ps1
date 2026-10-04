#Requires -Version 5.1
param(
    [ValidateSet('docker', 'local')]
    [string]$Mode = 'docker'
)

$ErrorActionPreference = 'Stop'
$ProjectDir = $PSScriptRoot
$BackendDir = Join-Path $ProjectDir 'backend'
$FrontendDir = Join-Path $ProjectDir 'frontend'

function Invoke-Checked {
    param([string]$Command, [string[]]$Arguments)
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Command 执行失败，退出码：$LASTEXITCODE" }
}

function Wait-Service {
    param([string]$Url)
    for ($attempt = 0; $attempt -lt 15; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) { return }
        } catch { }
        Start-Sleep -Seconds 2
    }
    throw "服务未就绪：$Url，请检查日志"
}

Push-Location $ProjectDir
try {
    if ($Mode -eq 'docker') {
        $ConfigFile = Join-Path $BackendDir '.env.production'
        if (-not (Test-Path -LiteralPath $ConfigFile)) {
            Copy-Item -LiteralPath (Join-Path $BackendDir '.env.production.example') -Destination $ConfigFile
            Write-Host '已复制生产配置模板，模型功能可稍后配置。'
        }
        & docker compose version
        if ($LASTEXITCODE -eq 0) {
            Invoke-Checked 'docker' @('compose', 'up', '-d', '--build')
        } else {
            Invoke-Checked 'docker-compose' @('up', '-d', '--build')
        }
        Wait-Service 'http://localhost:8000/health'
        Wait-Service 'http://localhost/'
        Write-Host '服务已启动：http://localhost'
    } else {
        $VenvDir = Join-Path $BackendDir '.venv'
        if (-not (Test-Path -LiteralPath $VenvDir)) {
            Invoke-Checked 'python' @('-m', 'venv', $VenvDir)
        }
        $PythonPath = Join-Path $VenvDir 'Scripts/python.exe'
        Invoke-Checked $PythonPath @('-m', 'pip', 'install', '-r', (Join-Path $BackendDir 'requirements.txt'))
        if (-not (Test-Path -LiteralPath (Join-Path $BackendDir '.env'))) {
            Copy-Item -LiteralPath (Join-Path $BackendDir '.env.example') -Destination (Join-Path $BackendDir '.env')
        }
        Invoke-Checked $PythonPath @('-m', 'playwright', 'install', 'chromium')
        Invoke-Checked $PythonPath @((Join-Path $BackendDir 'init_data.py'))
        Set-Location $FrontendDir
        Invoke-Checked 'npm.cmd' @('ci')
        Invoke-Checked 'npm.cmd' @('run', 'build')

        $LogDir = Join-Path $BackendDir 'logs'
        New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
        $BackendProcess = Start-Process -FilePath $PythonPath -WorkingDirectory $BackendDir `
            -ArgumentList '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000', '--workers', '1' `
            -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput (Join-Path $LogDir 'backend-output.log') `
            -RedirectStandardError (Join-Path $LogDir 'backend-error.log')
        Wait-Service 'http://localhost:8000/health'
        $FrontendProcess = Start-Process -FilePath 'cmd.exe' -WorkingDirectory $FrontendDir `
            -ArgumentList '/c', 'npm.cmd run preview -- --host 127.0.0.1 --port 4173 --strictPort' `
            -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput (Join-Path $LogDir 'frontend-output.log') `
            -RedirectStandardError (Join-Path $LogDir 'frontend-error.log')
        Wait-Service 'http://localhost:4173/'
        Write-Host "服务已启动：http://localhost:4173；后端进程 $($BackendProcess.Id)，前端进程 $($FrontendProcess.Id)"
    }
} finally {
    Pop-Location
}
