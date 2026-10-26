param([ValidateSet('setup','cad','verify','fea','figures')][string]$Stage='cad')
$ErrorActionPreference='Stop'
$projectRoot=$PSScriptRoot
$env:TEMP='E:\Codex\cache\tmp'
$env:TMP=$env:TEMP
$env:PIP_CACHE_DIR='E:\Codex\cache\pip'
$env:MPLCONFIGDIR='E:\Codex\cache\matplotlib'
$pythonExe='E:\Codex\environments\openhand-t42\Scripts\python.exe'
New-Item -ItemType Directory -Force -Path $env:TEMP,$env:PIP_CACHE_DIR,$env:MPLCONFIGDIR | Out-Null
function Invoke-ProjectPython { param([string[]]$Arguments) & $pythonExe @Arguments; if ($LASTEXITCODE -ne 0) { throw 'Python command failed' } }
switch ($Stage) {
 'setup' {
  if (-not (Test-Path -LiteralPath $pythonExe)) { py -3.12 -m venv 'E:\Codex\environments\openhand-t42'; if ($LASTEXITCODE -ne 0) { throw 'venv creation failed' } }
  Invoke-ProjectPython -Arguments @('-m','pip','install','-r',(Join-Path $projectRoot 'requirements.txt'))
 }
 'cad' { Invoke-ProjectPython -Arguments @((Join-Path $projectRoot 'scripts\build_cad.py')) }
 'verify' { Invoke-ProjectPython -Arguments @((Join-Path $projectRoot 'scripts\verify_solver.py')) }
 'fea' { foreach ($variant in @('baseline','pocket_1p8')) { foreach ($size in @('3.0','2.4')) { Invoke-ProjectPython -Arguments @((Join-Path $projectRoot 'scripts\analyze.py'),'--variant',$variant,'--size',$size) } } }
 'figures' { Invoke-ProjectPython -Arguments @((Join-Path $projectRoot 'scripts\visualize.py')); Invoke-ProjectPython -Arguments @((Join-Path $projectRoot 'scripts\summarize.py')) }
}
