@echo off
setlocal
cd /d "%~dp0"

set "SERVER_TEMPLATE="
if exist "%~dp0python-portable\python.exe" set "SERVER_TEMPLATE=""%~dp0python-portable\python.exe"" -m http.server __PORT__"

if not defined SERVER_TEMPLATE where py >nul 2>nul && set "SERVER_TEMPLATE=py -3 -m http.server __PORT__"
if not defined SERVER_TEMPLATE where python >nul 2>nul && set "SERVER_TEMPLATE=python -m http.server __PORT__"
if not defined SERVER_TEMPLATE where python3 >nul 2>nul && set "SERVER_TEMPLATE=python3 -m http.server __PORT__"
if not defined SERVER_TEMPLATE where npx >nul 2>nul && set "SERVER_TEMPLATE=npx --yes http-server -p __PORT__ -c-1 ."

if not defined SERVER_TEMPLATE (
  echo Could not find Python or Node.js (npx).
  echo Install Python 3 or Node.js and run start.bat again.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$ErrorActionPreference='Stop';" ^
"function Test-Url([string]$u){ try { Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 1 | Out-Null; return $true } catch { return $false } }" ^
"function Start-Server([string]$tmpl,[int]$port,[string]$wd){ $cmd=$tmpl.Replace('__PORT__',[string]$port); return Start-Process -FilePath 'cmd.exe' -ArgumentList '/c',$cmd -WorkingDirectory $wd -WindowStyle Hidden -PassThru }" ^
"function Wait-Server([string]$u,[int]$timeoutMs){ $deadline=(Get-Date).AddMilliseconds($timeoutMs); while((Get-Date)-lt $deadline){ if(Test-Url $u){ return $true }; Start-Sleep -Milliseconds 250 }; return $false }" ^
"$wd = (Resolve-Path '.').Path;" ^
"$serverTemplate = '%SERVER_TEMPLATE%';" ^
"$ports = @(8080,8081,8082);" ^
"$selectedPort = $null;" ^
"$server = $null;" ^
"foreach($p in $ports){" ^
"  $testUrl = 'http://localhost:' + $p + '/dj-visualizer.html';" ^
"  $candidate = Start-Server $serverTemplate $p $wd;" ^
"  Start-Sleep -Milliseconds 250;" ^
"  if($candidate.HasExited){ continue }" ^
"  if(Wait-Server $testUrl 12000){ $selectedPort=$p; $server=$candidate; break }" ^
"  if(-not $candidate.HasExited){ Stop-Process -Id $candidate.Id -Force -ErrorAction SilentlyContinue }" ^
"}" ^
"if(-not $selectedPort -or -not $server){ Write-Host 'Failed to start server on ports 8080/8081/8082.'; exit 2 }" ^
"$url = 'http://localhost:' + $selectedPort + '/dj-visualizer.html';" ^
"$chromeCandidates = @($env:ProgramFiles + '\\Google\\Chrome\\Application\\chrome.exe', ${env:ProgramFiles(x86)} + '\\Google\\Chrome\\Application\\chrome.exe', $env:LocalAppData + '\\Google\\Chrome\\Application\\chrome.exe');" ^
"$chrome = $chromeCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1;" ^
"Write-Host ('Server running at ' + $url);" ^
"if ($chrome) {" ^
"  $browser = $null;" ^
"  if($env:TEMP -and (Test-Path $env:TEMP)){" ^
"    try {" ^
"      $profile = Join-Path $env:TEMP ('djviz-profile-' + [Guid]::NewGuid().ToString());" ^
"      New-Item -ItemType Directory -Path $profile -Force | Out-Null;" ^
"      $browser = Start-Process -FilePath $chrome -ArgumentList '--new-window',('--user-data-dir=' + $profile),$url -PassThru -ErrorAction Stop;" ^
"    } catch {}" ^
"  }" ^
"  if(-not $browser){ $browser = Start-Process -FilePath $chrome -ArgumentList '--new-window',$url -PassThru }" ^
"  Wait-Process -Id $browser.Id;" ^
"} else {" ^
"  Start-Process $url | Out-Null;" ^
"  Write-Host 'Chrome not found. Opening default browser. Close this window when done to stop the server.';" ^
"  Read-Host | Out-Null;" ^
"}" ^
"if (-not $server.HasExited) { Stop-Process -Id $server.Id -Force }"

if errorlevel 1 (
  echo.
  echo Failed to run PowerShell part (possibly company policy).
  echo Manually start the server and open dj-visualizer.html:
  if exist "%~dp0python-portable\python.exe" (
    echo   python-portable\python.exe -m http.server 8080
  ) else (
    echo   py -3 -m http.server 8080
  )
  echo   then open http://localhost:8080/dj-visualizer.html
  pause
)

endlocal
