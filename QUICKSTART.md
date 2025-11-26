# Guia de Início Rápido - PyGame Básico

## Configuração (faça uma vez)

```bash
bash setup_env.sh
```

Este comando:
- ✅ Cria o ambiente virtual (`.venv`)
- ✅ Instala o PyGame e dependências
- ✅ Configura compatibilidade com Cursor IDE

## Executar Exemplos

### Modo 1: Usar o script `run.sh` (mais simples)
```bash
bash run.sh SpaceAtaque/spaceAtaque.py # Roda jogo espacial
```

### Modo 2: Usar diretamente o Python do venv
```bash
.venv/bin/python SpaceAtaque/spaceAtaque.py
```

### Modo 3: Ativar o venv manualmente
```bash
source .venv/bin/activate
deactivate  # quando terminar
```

## Jogos Disponíveis

| Jogo | Arquivo | Descrição |
|------|---------|-----------|
| **Space Ataque** | `SpaceAtaque/spaceAtaque.py` | Desvie de meteoros no espaço |

## Problemas?

### Erro: "No module named 'pygame'"
```bash
# Recriar o ambiente virtual
rm -rf .venv
bash setup_env.sh
```

### Erro: "externally-managed-environment"
✅ **Já resolvido!** O projeto agora tem compatibilidade total com Cursor IDE.
Se ainda aparecer, execute:
```bash
bash setup_env.sh
```

### Não consigo executar direto com `/usr/bin/python3`
⚠️ **Correto!** O PyGame está instalado apenas no ambiente virtual (`.venv`), não no Python do sistema.

**Use sempre uma destas formas:**
```bash
# Opção 1 (recomendada)
bash run.sh testeMostraGrade.py

# Opção 2
.venv/bin/python testeMostraGrade.py

# Opção 3
source .venv/bin/activate
python testeMostraGrade.py
deactivate
```

### Verificar instalação
```bash
.venv/bin/python -c "import pygame; print(f'PyGame {pygame.__version__} OK!')"
```

### Mais ajuda
Consulte o arquivo `README.md` para documentação completa.

