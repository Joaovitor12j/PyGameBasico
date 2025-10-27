# PyGame Básico — Configuração e Execução

Este repositório contém exemplos simples usando PyGame (jogos/demos). Este guia fornece as configurações mínimas para instalar as dependências e executar os scripts.

## Requisitos
- Python 3.9 ou superior (recomendado 3.10+)
- Pip atualizado
- (Opcional) Ambiente virtual para isolar dependências

## 🚀 Início Rápido

Configure e rode o projeto em poucos segundos:

### Linux/macOS:
```bash
# Configurar ambiente automaticamente (cria .venv e instala dependências)
bash setup_env.sh

# Rodar um exemplo
bash run.sh                        # roda testeMostraGrade.py por padrão
bash run.sh janelaBasico.py        # roda arquivo específico
bash run.sh CatchTheCoin/mainGame.py  # roda jogo de moedas
```

### Windows (PowerShell):
```powershell
# Configurar ambiente automaticamente
pwsh -f setup_env.ps1

# Rodar um exemplo
pwsh -f run.ps1                    # roda testeMostraGrade.py por padrão
pwsh -f run.ps1 janelaBasico.py    # roda arquivo específico
```

### Usando diretamente o Python do venv:
```bash
# Após executar setup_env.sh
.venv/bin/python testeMostraGrade.py
.venv/bin/python CatchTheCoin/mainGame.py
```

> **Nota para usuários do Cursor**: Este projeto inclui um wrapper especial para garantir compatibilidade total com o Cursor IDE. Os scripts de setup detectam e corrigem automaticamente qualquer conflito.

## Instalação Manual

1) Confirme a versão do Python e do pip:
- Linux/macOS: `python3 --version` e `python3 -m pip --version`
- Windows: `py --version` e `py -m pip --version`

2) (Recomendado) Crie e ative um ambiente virtual:
- Linux/macOS:
  - Criar: `python3 -m venv .venv`
  - Ativar: `source .venv/bin/activate`
- Windows (PowerShell):
  - Criar: `py -m venv .venv`
  - Ativar: `.venv\Scripts\Activate.ps1`

3) Instale as dependências:
```bash
pip install -r requirements.txt
```

Isso instalará o PyGame (versão 2.5.0 ou superior).

## Executando os Exemplos

Todos os scripts podem ser executados a partir da raiz do projeto. Alguns exemplos disponíveis:
- `testeMostraGrade.py` - Grade centralizada
- `janelaBasico.py` - Janela básica PyGame
- `janelaComSprite.py` - Exemplo com sprites
- `janelaComSpriteMovimentacao.py` - Sprites com movimentação
- `janelaTeste001.py` - Teste de janela
- `maze001.py` - Labirinto
- `CatchTheCoin/mainGame.py` - Jogo de coletar moedas
- `Minesweeper/gameMain.py` - Campo minado
- `SpaceEscape/spaceScape.py` - Jogo espacial

Para rodar um exemplo (após ativar o venv):
```bash
# Linux/macOS
python3 testeMostraGrade.py

# Windows
py testeMostraGrade.py
```

Ou use os scripts de conveniência:
```bash
# Linux/macOS
bash run.sh testeMostraGrade.py

# Windows
pwsh -f run.ps1 testeMostraGrade.py
```

## Estrutura do Projeto
```
PyGameBasico/
├── *.py                     # Scripts de exemplo na raiz
├── CatchTheCoin/            # Jogo de coletar moedas
│   ├── Assets/              # Recursos do jogo
│   └── mainGame.py          # Script principal
├── Minesweeper/             # Campo minado
│   └── gameMain.py          # Script principal
├── SpaceEscape/             # Jogo espacial
│   └── spaceScape.py        # Script principal
├── requirements.txt         # Dependências Python
├── setup_env.sh/.ps1        # Scripts de configuração
└── run.sh/.ps1              # Scripts de execução rápida
```

## Erro "No module named 'pygame'" — Como resolver rapidamente
Se ao executar um script você vir o erro "No module named 'pygame'", significa que o PyGame não está instalado no interpretador atual. Use uma destas opções:

- Opção 1 (recomendada): usar o ambiente virtual do projeto e rodar automaticamente:
  - Linux/macOS: `bash run.sh` (roda testeMostraGrade.py) ou `bash run.sh SEU_SCRIPT.py`
  - Windows: `pwsh -f run.ps1` ou `pwsh -f run.ps1 SEU_SCRIPT.py`

- Opção 2: preparar manualmente o venv e instalar dependências:
  - Linux/macOS: `bash setup_env.sh`
  - Windows: `pwsh -f setup_env.ps1`
  Em seguida rode: `bash setup_env.sh run SEU_SCRIPT.py` ou ative o venv e use `python SEU_SCRIPT.py`.

- Opção 3: se estiver usando uma IDE e surgir um aviso pedindo privilégios de administrador para instalar pacotes (por exemplo, no Python 3.12 do sistema), escolha "Configure" e selecione o interpretador do projeto como o Python dentro de `.venv` (caminho `.venv/bin/python` no Linux/macOS ou `.venv\Scripts\python.exe` no Windows). Assim você evita instalar em áreas protegidas do sistema.

Após qualquer uma das opções acima, o comando `python -c "import pygame; print(pygame.__version__)"` dentro do venv deve funcionar sem erros.


## Erro: "externally-managed-environment" (PEP 668) — Como resolver
Esse erro ocorre quando você tenta instalar pacotes (ex.: pygame) no Python do sistema (ex.: Python 3.12 em Debian/Ubuntu) que está marcado como "gerenciado externamente". A instalação direta com pip é bloqueada para proteger o ambiente do sistema.

Soluções recomendadas (sem exigir permissões administrativas):
- Opção rápida (recomendada): use o venv do projeto e rode automaticamente:
  - Linux/macOS: `bash run.sh` (padrão roda testeMostraGrade.py) ou `bash run.sh SEU_SCRIPT.py`
  - Windows: `pwsh -f run.ps1` ou `pwsh -f run.ps1 SEU_SCRIPT.py`
- Preparar manualmente o venv e instalar dependências:
  - Linux/macOS: `bash setup_env.sh`
  - Windows: `pwsh -f setup_env.ps1`
  Depois rode: `bash setup_env.sh run SEU_SCRIPT.py` ou ative o venv e use `python SEU_SCRIPT.py`.
- IDE (PyCharm/VS Code): configure o interpretador do projeto apontando para o Python do venv, e não para o Python do sistema:
  - Linux/macOS: selecione `.venv/bin/python`
  - Windows: selecione `.venv\Scripts\python.exe`
  Em seguida, instale as dependências usando o terminal do venv ou a própria IDE (desde que esteja usando o interpretador do venv).

Evite instalar no Python do sistema. Caso entenda os riscos e deseje forçar a instalação no sistema, o pip permite `--break-system-packages`, mas NÃO é recomendado e pode quebrar o Python do seu sistema. Prefira sempre o venv do projeto.
