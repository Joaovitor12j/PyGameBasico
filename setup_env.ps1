<#
Simple setup script for Windows PowerShell
- Creates .venv if missing
- Ensures pip is available (bootstraps with ensurepip if needed)
- Upgrades pip
- Installs requirements
Usage:
  pwsh -f setup_env.ps1             # just prepare the environment
  pwsh -f setup_env.ps1 run FILE.py # prepare and run a Python file inside the venv
#>

$ErrorActionPreference = 'Stop'

function Find-Python {
  if (Get-Command py -ErrorAction SilentlyContinue) { return 'py' }
  elseif (Get-Command python -ErrorAction SilentlyContinue) { return 'python' }
  else {
    Write-Error 'Python não encontrado. Instale Python 3.9+ e tente novamente.'
  }
}

$py = Find-Python

if (-not (Test-Path .venv)) {
  Write-Host '[setup] Criando ambiente virtual em .venv'
  # Tenta criar com --upgrade-deps (Python 3.10+); se não suportado, usa fallback
  try {
    & $py -m venv --upgrade-deps .venv 2>$null
  } catch {
    & $py -m venv .venv
  }
} else {
  Write-Host '[setup] Ambiente virtual .venv já existe'
}

$venvPython = Join-Path (Get-Location) '.venv/Scripts/python.exe'

# Garante que pip existe no venv
$hasPip = $false
try {
  & $venvPython -m pip --version *> $null
  if ($LASTEXITCODE -eq 0) { $hasPip = $true }
} catch {}

if (-not $hasPip) {
  Write-Host '[setup] pip não encontrado no venv. Tentando bootstrap com ensurepip...'
  try {
    & $venvPython -m ensurepip --upgrade *> $null
  } catch {}
  try {
    & $venvPython -m pip --version *> $null
    if ($LASTEXITCODE -eq 0) { $hasPip = $true }
  } catch {}
}

if (-not $hasPip) {
  Write-Error @"
[erro] O Python do venv ainda não possui pip.
Dicas: no Windows, certifique-se de ter instalado o Python com a opção "pip" e "venv".
Em ambientes Linux (WSL), instale os pacotes do sistema e recrie o venv:
  sudo apt-get update && sudo apt-get install -y python3-venv python3-pip
Depois execute novamente: pwsh -f setup_env.ps1
"@
}

Write-Host '[setup] Atualizando pip'
& $venvPython -m pip install --upgrade pip

if (Test-Path requirements.txt) {
  Write-Host '[setup] Instalando dependências de requirements.txt'
  & $venvPython -m pip install -r requirements.txt
} else {
  Write-Host '[setup] requirements.txt não encontrado. Pulando instalação de dependências.'
}

if ($args.Count -gt 0 -and $args[0] -eq 'run') {
  if ($args.Count -lt 2) {
    Write-Error 'Uso: pwsh -f setup_env.ps1 run ARQUIVO.py'
  }
  $target = $args[1]
  $rest = @()
  if ($args.Count -gt 2) { $rest = $args[2..($args.Count-1)] }
  Write-Host "[setup] Executando $target dentro do ambiente virtual"
  & $venvPython $target @rest
  exit $LASTEXITCODE
}

Write-Host "`n[setup] Pronto! Para ativar o ambiente virtual manualmente, execute:"
Write-Host '  .\.venv\Scripts\Activate.ps1'
Write-Host "`nPara rodar um exemplo sem ativar manualmente:"
Write-Host '  pwsh -f setup_env.ps1 run testeMostraGrade.py'
