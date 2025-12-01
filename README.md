# Space Ataque (PyGame) — Guia Completo do Jogo

O jogo Space Ataque é um shooter 2D com fases, itens, chefe final, multiplayer local e
um sistema de áudio completo com salvamento de configurações.

Se você quer apenas jogar, siga o Início Rápido. Se quiser conhecer o funcionamento do jogo (fases, sons, salvamento, etc.), veja as seções abaixo.

## Link do video para apresentação do jogo
- Youtube: https://youtu.be/M7zaWu-7IM4
- Drive: https://drive.google.com/file/d/1ipGRbkJddyYgWjsfDbQW8BlcaTdS-Qhm/view?usp=sharing

## Requisitos

- Python 3.9 ou superior (recomendado 3.10+)
- Pip atualizado
- (Opcional) Ambiente virtual (venv) para isolar dependências

## 🚀 Início Rápido

Configurar e rodar o Space Ataque em poucos passos a partir da raiz do projeto.

### Linux/macOS

```bash
# 1) Preparar ambiente (cria .venv e instala dependências)
bash setup_env.sh

# 2) Rodar o Space Ataque
bash run.sh SpaceAtaque/spaceAtaque.py
```

### Windows (PowerShell)

```powershell
# 1) Preparar ambiente (cria .venv e instala dependências)
pwsh -f setup_env.ps1

# 2) Rodar o Space Ataque
pwsh -f run.ps1 SpaceAtaque/spaceAtaque.py
```

### Usando diretamente o Python do venv

```bash
# Após executar setup_env.sh
.venv/bin/python SpaceAtaque/spaceAtaque.py
```

> Dica: Você também pode rodar outros exemplos do repositório com os mesmos scripts `run.sh`/`run.ps1`.

## Como Jogar

- Movimento (Player 1):
    - Setas: mover; Espaço: atirar
    - Alternativamente WASD para mover
    - Mouse: mover nave (acompanha o cursor); clique também reposiciona
- Pausa: ESC (abre menu de pausa)
- Multiplayer local (2 jogadores):
    - Player 1: setas; Player 2: WASD
    - Tiros automáticos no modo multiplayer

## Objetivo, Fases e Dificuldades

- Pontuação e fases
    - Fase 1: alcance 100 pontos
    - Fase 2: alcance 250 pontos e colete 3 itens (estrelas)
    - Fase 3+: alcance 350 pontos, colete 3 itens e derrote o chefe
- Dificuldades disponíveis: Fácil, Normal, Difícil (alterável no menu)
- Cada fase aumenta a pressão: mais inimigos e maior velocidade

### Itens

- Estrela (coletável a partir da Fase 2): aumenta o contador de itens da fase
- Escudo: concede invulnerabilidade por ~5 segundos com efeito visual ao redor da nave

### Chefe Final (a partir da Fase 3)

- O chefe aparece quando os objetivos base da fase (pontos + itens) são cumpridos
- Barra de vida com 100% e mudança de sprite conforme a vida diminui
- Movimenta-se no topo quando certos thresholds de vida são atingidos
- Ao derrotá-lo:
    - Toca o som de explosão do chefe
    - Você ganha pontos bônus
    - Surge a Tela de Vitória do jogo e você retorna ao menu principal (automático em 5s ou ao pressionar uma tecla)

## Sistema de Áudio

O jogo possui música e diversos efeitos sonoros com volumes independentes e persistência no save.

- Controles de volume e liga/desliga nas Configurações:
    - Sliders: point, hit, shoot, music (0–100%)
    - Flag de habilitação por item (inclui música)
    - Aplicação imediata: volumes e pausa/despausa de música são aplicados na hora
- Persistência no savegame: volumes e flags são salvos e restaurados automaticamente ao iniciar o jogo ou carregar o save
- Sons implementados e quando tocam:
    - sound_point: quando destrói inimigo e em alguns pickups
    - sound_hit: ao colidir com inimigos
    - sound_shoot: ao atirar
    - low_lifes: toca em loop enquanto você estiver com 3 ou menos vidas durante o gameplay
    - boss_final: toca por ~5 segundos quando o chefe aparece
    - collect_star: quando coleta uma estrela
    - gameover: na tela de Game Over
    - load_levels: toca em loop na tela de “Fase vencida” (espera entre fases)
    - boss_explosion: quando o chefe é derrotado
    - pause_game: toca em loop enquanto o jogo está pausado
    - space_bridge: toca em loop nos menus de “Escolher dificuldade” e “Configurações”
- Ducking automático:
    - Enquanto load_levels toca (tela de espera entre fases), os outros sons e a música são temporariamente rebaixados para destacar o som de espera
    - Ao iniciar a próxima fase, tudo volta ao volume normal
- Robustez de volume:
    - Os novos SFX não dependem apenas do volume/flag de “point” — eles usam como base o maior volume entre os sliders de SFX (point/hit/shoot),
      garantindo audibilidade
    - Alguns sons críticos (ex.: do chefe) têm ajuste de volume imediato para permanecerem audíveis mesmo se SFX base estiverem desligados

## Salvamento e Carregamento

O savegame (arquivo JSON) fica em `SpaceAtaque/savegame.json` e contém:

- difficulty, score, lives, phase
- posição do jogador
- items_collected, boss_defeated e highscore
- volumes e sound_enabled (configurações de áudio)

Quando ocorre salvamento:

- Ao pausar e escolher “Salvar e voltar ao menu” ou “Salvar e fechar o jogo”
- Ao entrar em Game Over
- Ao entrar na Tela de Vitória do jogo

Carregamento:

- A opção “Carregar jogo salvo” no menu principal restaura o progresso e aplica as configurações de som

## Estrutura do Projeto (essencial)

```
PyGameBasico/
├── SpaceAtaque/
│   ├── Assets/                # Imagens, sons, fundos, sprites
│   ├── spaceAtaque.py          # Jogo Space Ataque (principal)
│   └── savegame.json          # Save do jogo
├── setup_env.sh / setup_env.ps1
├── run.sh / run.ps1
└── requirements.txt
```

Outros diretórios contêm exemplos adicionais (CatchTheCoin, Minesweeper, etc.). Você pode executá-los com os mesmos scripts `run.sh`/`run.ps1`.

## Dicas e Solução de Problemas

- “No module named 'pygame'”
    - Use o venv do projeto e os scripts de execução
    - Linux/macOS: `bash run.sh SpaceAtaque/spaceAtaque.py`
    - Windows: `pwsh -f run.ps1 SpaceAtaque/spaceAtaque.py`
- PEP 668 — “externally-managed-environment”
    - Evite instalar pacotes no Python do sistema
    - Use `setup_env.sh`/`setup_env.ps1` para criar o venv do projeto e instalar as dependências
- Sem áudio no Linux?
    - Verifique se o mixer do sistema não está mutado
    - Em algumas distros, pode ser necessário instalar bibliotecas de áudio SDL (por exemplo, `libsdl2-mixer` e codecs). O PyGame normalmente traz o
      necessário, mas o suporte do SO é importante
- Música não toca?
    - Abra Configurações no menu principal e verifique se “Música” está ligada e com volume acima de 0

## Instalação Manual (alternativa)

1) Verifique Python e pip:

- Linux/macOS: `python3 --version` e `python3 -m pip --version`
- Windows: `py --version` e `py -m pip --version`

2) Crie/ative o ambiente virtual:

- Linux/macOS:
    - Criar: `python3 -m venv .venv`
    - Ativar: `source .venv/bin/activate`
- Windows (PowerShell):
    - Criar: `py -m venv .venv`
    - Ativar: `.venv\\Scripts\\Activate.ps1`

3) Instale as dependências:

```bash
pip install -r requirements.txt
```

4) Rode o jogo:

```bash
python SpaceAtaque/spaceAtaque.py   # Windows (dentro do venv)
python3 SpaceAtaque/spaceAtaque.py  # Linux/macOS (dentro do venv)
```

---

Bom jogo! 🚀 Se encontrar algum problema ou tiver sugestões, abra uma issue ou envie um PR.
