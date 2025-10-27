##############################################################
###               S P A C E     E S C A P E                ###
##############################################################
###                  versao Alpha 0.1                      ###
##############################################################
### Objetivo: desviar dos meteoros que caem.               ###
### Cada colisão tira uma vida. Sobreviva o máximo que     ###
### conseguir!                                             ###
##############################################################
### Prof. Filipo Novo Mor - github.com/ProfessorFilipo     ###
##############################################################

import pygame
import random

# Inicializa o PyGame
pygame.init()

# --- Configurações da janela ---
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🚀 Space Escape")

# --- Cores ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 60, 60)
BLUE = (50, 100, 255)
GRAY = (180, 180, 180)

# --- Fonte ---
font = pygame.font.Font(None, 36)

# --- Jogador (nave) ---
player = pygame.Rect(WIDTH // 2 - 30, HEIGHT - 60, 60, 30)
player_speed = 8

# --- Meteoros ---
meteor_list = []
for i in range(5):
    x = random.randint(0, WIDTH - 40)
    y = random.randint(-500, -40)
    meteor_list.append(pygame.Rect(x, y, 40, 40))
meteor_speed = 5

# --- Variáveis de jogo ---
lives = 3
score = 0
clock = pygame.time.Clock()
running = True

# --- Loop principal do jogo ---
while running:
    screen.fill(BLACK)

    # --- Eventos ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Movimento do jogador ---
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and player.left > 0:
        player.x -= player_speed
    if keys[pygame.K_RIGHT] and player.right < WIDTH:
        player.x += player_speed

    # --- Movimento e reposição dos meteoros ---
    for meteor in meteor_list:
        meteor.y += meteor_speed
        if meteor.y > HEIGHT:
            meteor.y = random.randint(-100, -40)
            meteor.x = random.randint(0, WIDTH - meteor.width)
            score += 1  # ganha ponto ao desviar com sucesso

        # --- Checa colisão ---
        if meteor.colliderect(player):
            lives -= 1
            meteor.y = random.randint(-100, -40)
            meteor.x = random.randint(0, WIDTH - meteor.width)
            if lives <= 0:
                running = False

    # --- Desenha jogador e meteoros ---
    pygame.draw.rect(screen, BLUE, player)
    for meteor in meteor_list:
        pygame.draw.ellipse(screen, RED, meteor)

    # --- Exibe pontuação e vidas ---
    text = font.render(f"Pontos: {score}   Vidas: {lives}", True, WHITE)
    screen.blit(text, (10, 10))

    # --- Atualiza tela ---
    pygame.display.flip()
    clock.tick(60)

# --- Tela de fim de jogo ---
screen.fill(GRAY)
end_text = font.render("Fim de jogo! Pressione qualquer tecla para sair.", True, BLACK)
final_score = font.render(f"Pontuação final: {score}", True, BLACK)
screen.blit(end_text, (160, 260))
screen.blit(final_score, (300, 300))
pygame.display.flip()

# Espera o jogador pressionar uma tecla antes de fechar
waiting = True
while waiting:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
            waiting = False

pygame.quit()
