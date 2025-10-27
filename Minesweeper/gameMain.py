#######################################################################
###                     Caça Minas - Mine Sweeper                   ###
#######################################################################
### A rotina de "derrota" mostra uma mensagem na                    ###
### mesma janela do jogo, mostrando, ainda, as posicoes das bombas  ###
#######################################################################
###                        versao 1.0 Alpha                         ###
### Prof. Filipo Mor - github.com/ProfessorFilipo                   ###
#######################################################################

import pygame
import random
import os

# Cores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GRAY = (128, 128, 128)

# Configurações do jogo
GRID_SIZE = 20
BOMB_COUNT = 10
CELL_SIZE = 16  # Tamanho de cada célula no arquivo de sprites

SCREEN_WIDTH = CELL_SIZE * GRID_SIZE
SCREEN_HEIGHT = CELL_SIZE * GRID_SIZE

pygame.init()

# Caminho base dos assets relativo a este arquivo
ASSET_DIR = os.path.dirname(os.path.abspath(__file__))

# Inicializa o mixer de áudio ANTES de carregar o som
explosion_sound = None
try:
    pygame.mixer.init()
    # Tenta localizar o arquivo de som em formatos comuns dentro da pasta do jogo
    for fname in ("explosao.mp3", "explosao.wav"):
        sound_path = os.path.join(ASSET_DIR, fname)
        if os.path.exists(sound_path):
            explosion_sound = pygame.mixer.Sound(sound_path)
            explosion_sound.set_volume(1.0)
            break
    if explosion_sound is None:
        print("Aviso: arquivo de som de explosão não encontrado (explosao.mp3/.wav). O jogo continuará sem áudio.")
except Exception as e:
    # Captura erros do mixer ou de carregamento do som sem encerrar o jogo
    print(f"Aviso: não foi possível inicializar áudio ou carregar som: {e}")
    explosion_sound = None

screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
pygame.display.set_caption("Campo Minado com Sprites")

# Carrega a imagem das células
try:
    image_path = os.path.join(ASSET_DIR, "celulas.png")
    cell_images = pygame.image.load(image_path)
except Exception as e:
    print(f"Erro ao carregar 'celulas.png' em {image_path}: {e}")
    pygame.quit()
    exit()

# Função para obter um sprite específico da imagem
def get_cell_image(x, y):
    rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    return cell_images.subsurface(rect)

# Inicializa o grid
grid = []
for row in range(GRID_SIZE):
    grid.append([0] * GRID_SIZE)

# Coloca as bombas
bombs_placed = 0
while bombs_placed < BOMB_COUNT:
    x = random.randint(0, GRID_SIZE - 1)
    y = random.randint(0, GRID_SIZE - 1)
    if grid[x][y] == 0:
        grid[x][y] = -1  # -1 representa uma bomba
        bombs_placed += 1

# Calcula os números ao redor das bombas
for x in range(GRID_SIZE):
    for y in range(GRID_SIZE):
        if grid[x][y] == -1:
            continue

        bomb_count = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == 0 and j == 0:
                    continue

                neighbor_x = x + i
                neighbor_y = y + j

                if 0 <= neighbor_x < GRID_SIZE and 0 <= neighbor_y < GRID_SIZE and grid[neighbor_x][neighbor_y] == -1:
                    bomb_count += 1

        grid[x][y] = bomb_count

# Lógica para revelar a célula e células vizinhas (recursivamente)
def reveal_cell(x, y, revealed):
    if x < 0 or x >= GRID_SIZE or y < 0 or y >= GRID_SIZE or revealed[x][y]:
        return

    revealed[x][y] = True
    global score  # Permite modificar a variável score global
    score += 10  # Adiciona pontos por revelar uma célula segura

    if grid[x][y] == 0:
        for i in range(-1, 2):
            for j in range(-1, 2):
                reveal_cell(x + i, y + j, revealed)

revealed = []
for row in range(GRID_SIZE):
    revealed.append([False] * GRID_SIZE)

# Matriz para rastrear células marcadas com bandeira
flagged = []
for row in range(GRID_SIZE):
    flagged.append([False] * GRID_SIZE)

game_over = False
score = 0  # Inicializa a pontuação
BOMB_MARK_REWARD = 50
BOMB_MARK_PENALTY = -20

clock = pygame.time.Clock()

# Loop principal do jogo
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            column = pos[0] // CELL_SIZE
            row = pos[1] // CELL_SIZE

            if event.button == 1:  # Botão esquerdo
                if not game_over and not flagged[row][column]:
                    if grid[row][column] == -1:
                        game_over = True

                        # Mostrar todas as bombas
                        for x in range(GRID_SIZE):
                            for y in range(GRID_SIZE):
                                if grid[x][y] == -1:
                                    revealed[x][y] = True

                        if explosion_sound:
                            explosion_sound.play()  # Toca o som da explosão
                    else:
                        reveal_cell(row, column, revealed)
            elif event.button == 3:  # Botão direito
                if not game_over and not revealed[row][column]:
                    flagged[row][column] = not flagged[row][column]  # Alterna a marcação
                    if flagged[row][column]:  # Se a bandeira foi colocada
                        if grid[row][column] == -1:
                            score += BOMB_MARK_REWARD
                        else:
                            score += BOMB_MARK_PENALTY
                    else:  # Se a bandeira foi removida
                        if grid[row][column] == -1:
                            score -= BOMB_MARK_REWARD
                        else:
                            score -= BOMB_MARK_PENALTY

    screen.fill(BLACK)

    for row in range(GRID_SIZE):
        for column in range(GRID_SIZE):
            cell_value = grid[row][column]

            # Determina qual sprite usar
            sprite_x, sprite_y = 1, 2  # Inicializa com célula fechada

            if flagged[row][column]:
                sprite_x, sprite_y = 3, 2  # Célula com bandeira
            elif revealed[row][column]:
                if cell_value == 0:
                    sprite_x, sprite_y = 0, 2  # Célula vazia revelada
                elif cell_value > 0:
                    sprite_index = cell_value - 1
                    sprite_x = sprite_index % 4
                    sprite_y = sprite_index // 4
                elif game_over and cell_value == -1:
                    sprite_x, sprite_y = 2, 2  # Bomba revelada
            elif game_over and cell_value == -1:
                sprite_x, sprite_y = 2, 2  # mostrar bomba após game over

            cell_image = get_cell_image(sprite_x, sprite_y)
            screen.blit(cell_image, (column * CELL_SIZE, row * CELL_SIZE))

    # Mostra a pontuação atual
    font = pygame.font.Font(None, 30)
    score_text = font.render(f"Pontuação: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))  # Posição no canto superior esquerdo

    if game_over:
        # Desenha um retângulo semi-transparente
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((GRAY[0], GRAY[1], GRAY[2], 128))  # Cor cinza semi-transparente
        screen.blit(overlay, (0, 0))

        # Desenha a mensagem "Game Over"
        font = pygame.font.Font(None, 50)
        text = font.render("VOCÊ EXPLODIU!", True, RED)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(text, text_rect)

        # Mostra a pontuação final
        score_text = font.render(f"Pontuação: {score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))  # Ajusta a posição
        screen.blit(score_text, score_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
