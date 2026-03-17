@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "SERVER_TEMPLATE="
if exist "%~dp0python-portable\python.exe" set "SERVER_TEMPLATE=""%~dp0python-portable\python.exe"" -m http.server __PORT__ --bind 127.0.0.1"

if not defined SERVER_TEMPLATE where py >nul 2>nul && set "SERVER_TEMPLATE=py -3 -m http.server __PORT__ --bind 127.0.0.1"
if not defined SERVER_TEMPLATE where python >nul 2>nul && set "SERVER_TEMPLATE=python -m http.server __PORT__ --bind 127.0.0.1"
if not defined SERVER_TEMPLATE where python3 >nul 2>nul && set "SERVER_TEMPLATE=python3 -m http.server __PORT__ --bind 127.0.0.1"
if not defined SERVER_TEMPLATE where npx >nul 2>nul && set "SERVER_TEMPLATE=npx --yes http-server -p __PORT__ -a 127.0.0.1 -c-1 ."

if not defined SERVER_TEMPLATE (
  echo Could not find Python or Node.js (npx).
  echo Install Python 3 or Node.js and run start.bat again.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$ErrorActionPreference='Stop';" ^
"function Test-Url([string]$u){ try { Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 1 | Out-Null; return $true } catch { return $false } }" ^
"function Test-PortBusy([int]$p){ try { $l = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse('127.0.0.1'), $p); $l.Start(); $l.Stop(); return $false } catch { return $true } }" ^
"function Start-Server([string]$tmpl,[int]$port,[string]$wd){ $cmd=$tmpl.Replace('__PORT__',[string]$port); return Start-Process -FilePath 'cmd.exe' -ArgumentList '/c',$cmd -WorkingDirectory $wd -WindowStyle Hidden -PassThru }" ^
"function Wait-Server([string]$u,[int]$timeoutMs){ $deadline=(Get-Date).AddMilliseconds($timeoutMs); while((Get-Date)-lt $deadline){ if(Test-Url $u){ return $true }; Start-Sleep -Milliseconds 250 }; return $false }" ^
"$wd = (Resolve-Path '.').Path;" ^
"$serverTemplate = '%SERVER_TEMPLATE%';" ^
"$ports = @(8080,8081,8082);" ^
"$selectedPort = $null;" ^
"$server = $null;" ^
"foreach($p in $ports){" ^
"  if(Test-PortBusy $p){ continue }" ^
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
"$edgeCandidates = @($env:ProgramFiles + '\\Microsoft\\Edge\\Application\\msedge.exe', ${env:ProgramFiles(x86)} + '\\Microsoft\\Edge\\Application\\msedge.exe', $env:LocalAppData + '\\Microsoft\\Edge\\Application\\msedge.exe');" ^
"$chrome = $chromeCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1;" ^
"$edge = $edgeCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1;" ^
"$browserPath = $null;" ^
"$browserName = 'default browser';" ^
"if ($chrome) { $browserPath = $chrome; $browserName = 'Chrome' } elseif ($edge) { $browserPath = $edge; $browserName = 'Edge' }" ^
"Write-Host ('Server running at ' + $url);" ^
"if ($browserPath) {" ^
"  $browser = $null;" ^
"  if($env:TEMP -and (Test-Path $env:TEMP)){" ^
"    try {" ^
"      $profile = Join-Path $env:TEMP ('djviz-profile-' + [Guid]::NewGuid().ToString());" ^
"      New-Item -ItemType Directory -Path $profile -Force | Out-Null;" ^
"      $browser = Start-Process -FilePath $browserPath -ArgumentList '--new-window',('--user-data-dir=' + $profile),$url -PassThru -ErrorAction Stop;" ^
"    } catch {}" ^
"  }" ^
"  if(-not $browser){ $browser = Start-Process -FilePath $browserPath -ArgumentList '--new-window',$url -PassThru }" ^
"  Write-Host ($browserName + ' opened. Close this browser window to stop the server.');" ^
"  Wait-Process -Id $browser.Id;" ^
"} else {" ^
"  Start-Process $url | Out-Null;" ^
"  Write-Host 'Chrome/Edge not found. Opening default browser. Close this window when done to stop the server.';" ^
"  Read-Host | Out-Null;" ^
"}" ^
"if (-not $server.HasExited) { Stop-Process -Id $server.Id -Force }"

if errorlevel 1 (
  echo.
  echo PowerShell startup failed (possibly company policy).
  echo Trying CMD fallback on ports 8080/8081/8082...
  set "SELECTED_PORT="
  for %%P in (8080 8081 8082) do (
    call :port_busy %%P PORT_BUSY
    if "!PORT_BUSY!"=="0" if not defined SELECTED_PORT (
      set "FALLBACK_CMD=%SERVER_TEMPLATE:__PORT__=%%P%"
      start "DJVIZ_FALLBACK_%%P" /min cmd /c !FALLBACK_CMD!
      timeout /t 2 /nobreak >nul
      call :check_url "http://127.0.0.1:%%P/dj-visualizer.html" READY
      if "!READY!"=="1" set "SELECTED_PORT=%%P"
      if "!READY!"=="0" taskkill /FI "WINDOWTITLE eq DJVIZ_FALLBACK_%%P*" /T /F >nul 2>nul
    )
  )
  if not defined SELECTED_PORT (
    echo Failed to start fallback server on ports 8080/8081/8082.
    pause
    goto :done
  )
  start "" "http://127.0.0.1:!SELECTED_PORT!/dj-visualizer.html"
  echo Browser opened at http://127.0.0.1:!SELECTED_PORT!/dj-visualizer.html
  echo Press any key to stop fallback server...
  pause >nul
  taskkill /FI "WINDOWTITLE eq DJVIZ_FALLBACK_*" /T /F >nul 2>nul
)

:done
endlocal
exit /b

:check_url
set "%~2=0"
set "CHECK_URL=%~1"
where curl >nul 2>nul
if not errorlevel 1 (
  curl -fsS --max-time 2 "%CHECK_URL%" >nul 2>nul && set "%~2=1"
  goto :eof
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -c "import urllib.request,sys; urllib.request.urlopen(sys.argv[1],timeout=2)" "%CHECK_URL%" >nul 2>nul && set "%~2=1"
  goto :eof
)
where python >nul 2>nul
if not errorlevel 1 (
  python -c "import urllib.request,sys; urllib.request.urlopen(sys.argv[1],timeout=2)" "%CHECK_URL%" >nul 2>nul && set "%~2=1"
  goto :eof
)
where python3 >nul 2>nul
if not errorlevel 1 (
  python3 -c "import urllib.request,sys; urllib.request.urlopen(sys.argv[1],timeout=2)" "%CHECK_URL%" >nul 2>nul && set "%~2=1"
)
goto :eof

:port_busy
set "%~2=0"
set "CHECK_PORT=%~1"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -c "import socket,sys;s=socket.socket();rc=s.connect_ex(('127.0.0.1',int(sys.argv[1])));s.close();sys.exit(1 if rc==0 else 0)" "%CHECK_PORT%" >nul 2>nul
  if errorlevel 1 set "%~2=1"
  goto :eof
)
where python >nul 2>nul
if not errorlevel 1 (
  python -c "import socket,sys;s=socket.socket();rc=s.connect_ex(('127.0.0.1',int(sys.argv[1])));s.close();sys.exit(1 if rc==0 else 0)" "%CHECK_PORT%" >nul 2>nul
  if errorlevel 1 set "%~2=1"
  goto :eof
)
where python3 >nul 2>nul
if not errorlevel 1 (
  python3 -c "import socket,sys;s=socket.socket();rc=s.connect_ex(('127.0.0.1',int(sys.argv[1])));s.close();sys.exit(1 if rc==0 else 0)" "%CHECK_PORT%" >nul 2>nul
  if errorlevel 1 set "%~2=1"
)
goto :eof
