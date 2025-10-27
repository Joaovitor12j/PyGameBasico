#!/usr/bin/env bash
set -euo pipefail

# Simple setup script for Linux/macOS
# - Creates .venv if missing
# - Ensures pip is available (bootstraps with ensurepip if needed)
# - Upgrades pip
# - Installs requirements
# Usage:
#   bash setup_env.sh           # just prepare the environment
#   bash setup_env.sh run FILE  # prepare and run a Python file inside the venv

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo python3
  elif command -v python >/dev/null 2>&1; then
    echo python
  else
    echo "Python não encontrado. Instale Python 3.9+ e tente novamente." >&2
    exit 1
  fi
}

PY=$(find_python)

if [ ! -d .venv ]; then
  echo "[setup] Criando ambiente virtual em .venv"
  # Tenta criar com --upgrade-deps (Python 3.10+); se não suportado, usa fallback
  # Usa env -i para criar ambiente limpo e evitar conflitos com Cursor
  if ! env -i PATH=/usr/bin:/bin "$PY" -m venv --upgrade-deps .venv >/dev/null 2>&1; then
    env -i PATH=/usr/bin:/bin "$PY" -m venv .venv 2>&1 || {
      echo "[setup] Tentando criar venv sem ensurepip..."
      env -i PATH=/usr/bin:/bin "$PY" -m venv --without-pip .venv
    }
  fi
  # Cria wrapper para o Python (necessário para compatibilidade com Cursor)
  echo "[setup] Criando wrapper do Python..."
  VENV_ABS_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.venv"
  cat > .venv/bin/python_real <<'WRAPPER_EOF'
#!/usr/bin/env bash
# Wrapper para garantir que o Python use o venv corretamente
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$(dirname "$SCRIPT_DIR")"
export VIRTUAL_ENV="$VENV_DIR"
export PATH="$VENV_DIR/bin:$PATH"
export PYTHONPATH="$VENV_DIR/lib/python3.12/site-packages:${PYTHONPATH:-}"
unset PYTHONHOME
exec /usr/bin/python3.12 "$@"
WRAPPER_EOF
  chmod +x .venv/bin/python_real
  
  # Corrige links simbólicos para usar o wrapper
  echo "[setup] Configurando links simbólicos..."
  rm -f .venv/bin/python .venv/bin/python3 .venv/bin/python3.12
  ln -s python_real .venv/bin/python3.12
  ln -s python3.12 .venv/bin/python3
  ln -s python3 .venv/bin/python
  
  # Cria sitecustomize.py para forçar reconhecimento do venv
  echo "[setup] Configurando sitecustomize.py..."
  mkdir -p .venv/lib/python3.12/site-packages
  cat > .venv/lib/python3.12/site-packages/sitecustomize.py <<'SITECUST_EOF'
"""
Customização do site para forçar o reconhecimento do ambiente virtual.
Necessário devido a conflitos com o Cursor IDE.
"""
import sys
import os
from pathlib import Path

# Detecta se estamos no venv
if 'VIRTUAL_ENV' in os.environ:
    venv_path = os.environ['VIRTUAL_ENV']
    
    # Força o sys.prefix para o venv
    sys.prefix = venv_path
    sys.exec_prefix = venv_path
    
    # Garante que o site-packages do venv está no path
    site_packages = Path(venv_path) / "lib" / "python3.12" / "site-packages"
    site_packages_str = str(site_packages)
    
    if site_packages_str not in sys.path:
        # Remove paths do sistema que podem conflitar
        sys.path = [p for p in sys.path if not p.startswith('/usr/lib/python3') or 'site-packages' not in p]
        # Adiciona o site-packages do venv no início
        sys.path.insert(0, site_packages_str)
SITECUST_EOF
else
  echo "[setup] Ambiente virtual .venv já existe"
  # Verifica se precisa atualizar o wrapper
  if [ ! -f .venv/bin/python_real ] || [ "$(readlink .venv/bin/python)" != "python3" ]; then
    echo "[setup] Atualizando wrapper do Python..."
    cat > .venv/bin/python_real <<'WRAPPER_EOF'
#!/usr/bin/env bash
# Wrapper para garantir que o Python use o venv corretamente
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$(dirname "$SCRIPT_DIR")"
export VIRTUAL_ENV="$VENV_DIR"
export PATH="$VENV_DIR/bin:$PATH"
export PYTHONPATH="$VENV_DIR/lib/python3.12/site-packages:${PYTHONPATH:-}"
unset PYTHONHOME
exec /usr/bin/python3.12 "$@"
WRAPPER_EOF
    chmod +x .venv/bin/python_real
    rm -f .venv/bin/python .venv/bin/python3 .venv/bin/python3.12
    ln -s python_real .venv/bin/python3.12
    ln -s python3.12 .venv/bin/python3
    ln -s python3 .venv/bin/python
  fi
  
  # Garante que sitecustomize.py existe
  if [ ! -f .venv/lib/python3.12/site-packages/sitecustomize.py ]; then
    echo "[setup] Configurando sitecustomize.py..."
    mkdir -p .venv/lib/python3.12/site-packages
    cat > .venv/lib/python3.12/site-packages/sitecustomize.py <<'SITECUST_EOF'
"""
Customização do site para forçar o reconhecimento do ambiente virtual.
Necessário devido a conflitos com o Cursor IDE.
"""
import sys
import os
from pathlib import Path

# Detecta se estamos no venv
if 'VIRTUAL_ENV' in os.environ:
    venv_path = os.environ['VIRTUAL_ENV']
    
    # Força o sys.prefix para o venv
    sys.prefix = venv_path
    sys.exec_prefix = venv_path
    
    # Garante que o site-packages do venv está no path
    site_packages = Path(venv_path) / "lib" / "python3.12" / "site-packages"
    site_packages_str = str(site_packages)
    
    if site_packages_str not in sys.path:
        # Remove paths do sistema que podem conflitar
        sys.path = [p for p in sys.path if not p.startswith('/usr/lib/python3') or 'site-packages' not in p]
        # Adiciona o site-packages do venv no início
        sys.path.insert(0, site_packages_str)
SITECUST_EOF
  fi
fi

# Use the venv's python
VENV_PY=.venv/bin/python

# Garante que pip existe no venv
if ! "$VENV_PY" -m pip --version >/dev/null 2>&1; then
  echo "[setup] pip não encontrado no venv. Tentando bootstrap com ensurepip..."
  if ! "$VENV_PY" -m ensurepip --upgrade >/dev/null 2>&1; then
    echo "[setup] Falha ao inicializar pip com ensurepip." >&2
  fi
fi

# Recheca pip
if ! "$VENV_PY" -m pip --version >/dev/null 2>&1; then
  echo "[erro] O Python do venv ainda não possui pip.\n" \
       "Dicas: em Debian/Ubuntu, instale pacotes do sistema e recrie o venv:" \
       "\n  sudo apt-get update && sudo apt-get install -y python3-venv python3-pip\n" \
       "Depois execute: bash setup_env.sh" >&2
  exit 3
fi

echo "[setup] Verificando versão do pip"
PIP_VERSION=$("$VENV_PY" -m pip --version | awk '{print $2}' | cut -d. -f1)
if [ "$PIP_VERSION" -lt 24 ]; then
  echo "[setup] Atualizando pip (versão antiga detectada)"
  "$VENV_PY" -m pip install --upgrade pip 2>/dev/null || echo "[aviso] Não foi possível atualizar o pip, mas continuando..."
else
  echo "[setup] Pip já está atualizado (versão $PIP_VERSION.x)"
fi

if [ -f requirements.txt ]; then
  echo "[setup] Instalando dependências de requirements.txt"
  "$VENV_PY" -m pip install -r requirements.txt
else
  echo "[setup] requirements.txt não encontrado. Pulando instalação de dependências."
fi

if [ "${1:-}" = "run" ]; then
  shift
  if [ -z "${1:-}" ]; then
    echo "Uso: bash setup_env.sh run ARQUIVO.py" >&2
    exit 2
  fi
  TARGET=$1
  shift || true
  echo "[setup] Executando $TARGET dentro do ambiente virtual"
  exec "$VENV_PY" "$TARGET" "$@"
fi

cat <<EOF

[setup] Pronto! Para ativar o ambiente virtual manualmente, execute:
  source .venv/bin/activate

Para rodar um exemplo sem ativar manualmente:
  bash setup_env.sh run testeMostraGrade.py
EOF
