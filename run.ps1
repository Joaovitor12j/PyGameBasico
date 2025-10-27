<#!
Convenience launcher for Windows PowerShell.
Ensures the virtual environment is ready and runs a Python script inside it.
Usage:
  pwsh -f run.ps1                 # runs testeMostraGrade.py by default
  pwsh -f run.ps1 ARQUIVO.py ...  # runs the given file inside the venv
!>
param(
  [string]$Target = 'testeMostraGrade.py',
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Rest
)

$ErrorActionPreference = 'Stop'

$setup = Join-Path (Get-Location) 'setup_env.ps1'
& pwsh -f $setup run $Target @Rest
exit $LASTEXITCODE
