import pygame
import random
import sys
import os

# Inicializa o PyGame
pygame.init()

# Define tamanhos da tela
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Jogo de Moedinhas do Céu")

# Define cores
BG_COLOR = (0, 100, 255)  # céu azul

# Carregamento de sprites (usaremos retângulos coloridos como placeholders aqui)
# Na implementação real, substitua por imagens carregadas com pygame.image.load()
ASSET_DIR = os.path.dirname(os.path.abspath(__file__))
background_img = None
try:
    bg_path = os.path.join(ASSET_DIR, 'Assets', 'Ocean_8', '6.png')
    background_img = pygame.image.load(bg_path)
    background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))
except Exception as e:
    print(f"Aviso: fundo não pôde ser carregado em {bg_path}: {e}. Usando cor sólida de fundo.")


# Sprites (poderiam ser substituídos por imagens reais)
def create_sprite(width, height, color):
    sprite = pygame.Surface((width, height))
    sprite.fill(color)
    return sprite

# Carregando sprites ou criando objetos
# Barco
boat_sprite = create_sprite(80, 40, (255, 0, 0))
# Moeda
coin_sprite = create_sprite(20, 20, (255, 215, 0))  # dourada
# Mar
sea_sprite = create_sprite(WIDTH, 100, (0, 0, 255))
sea_rect = sea_sprite.get_rect(topleft=(0, HEIGHT - 100))
# Porto (local de descarga)
port_sprite = create_sprite(100, 50, (139, 69, 19))
port_rect = port_sprite.get_rect(topleft=(WIDTH//2 - 50, HEIGHT - 50))

# Variáveis do jogo
clock = pygame.time.Clock()
FONT = pygame.font.SysFont(None, 36)

# Classe para moedas
class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y, speed):
        super().__init__()
        self.image = coin_sprite
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = speed  # velocidade de queda

    def update(self):
        self.rect.y += self.speed
        # Se a moeda passar do limite inferior, ela reaparece no topo com nova velocidade
        if self.rect.top > HEIGHT:
            self.rect.x = random.randint(0, WIDTH - self.rect.width)
            self.rect.y = random.randint(-50, -10)
            self.speed = random.uniform(2, 5)  # nova velocidade aleatória

# Classe para o barco
class Boat(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = boat_sprite
        self.rect = self.image.get_rect(midbottom=(WIDTH//2, HEIGHT - 100))
        self.speed = 8  # velocidade de movimento
        self.carga = 0  # quantidade de moedas capturadas
        self.max_carga = 10  # limite de moedas antes de voltar ao porto
        self.captura_ativo = True  # controle se está em captura ou descarregando

    def update(self, keys_pressed):
        # Movimenta o barco com as setas esquerda/direita
        if keys_pressed[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys_pressed[pygame.K_RIGHT]:
            self.rect.x += self.speed
        # Limitar o movimento aos limites da tela
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH

    def voltar_ao_porto(self):
        # Move o barco para o porto para descarregar
        self.rect.midbottom = (WIDTH//2, HEIGHT - 100)
        self.carga = 0  # descarrega as moedas

# Funções para diferentes níveis de dificuldade
def configurar_dificuldade(nivel):
    if nivel == 1:
        qty_moedas = 15
        velocidade_min = 2
        velocidade_max = 3
    elif nivel == 2:
        qty_moedas = 25
        velocidade_min = 3
        velocidade_max = 4
    elif nivel == 3:
        qty_moedas = 35
        velocidade_min = 4
        velocidade_max = 6
    return qty_moedas, velocidade_min, velocidade_max

# Variáveis do jogo
nivel = 1  # nível inicial
qtd_moedas, v_min, v_max = configurar_dificuldade(nivel)

# Grupo de moedas
moedas = pygame.sprite.Group()

# Criar moedas iniciais
for _ in range(qtd_moedas):
    x = random.randint(0, WIDTH - 20)
    y = random.randint(-100, -10)
    speed = random.uniform(v_min, v_max)
    moedas.add(Coin(x, y, speed))

# Instancia o barco
barco = Boat()
todos_sprites = pygame.sprite.Group()
todos_sprites.add(barco)

# Variável para controle do estado do jogo
em_descarga = False
tempo_descarga = 0

# Loop principal do jogo
running = True
while running:
    clock.tick(60)  # limita a 60 fps
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # Se o barco estiver carregando e atingir a capacidade máxima, inicia a descarga
    if not em_descarga and barco.carga >= barco.max_carga:
        em_descarga = True
        tempo_descarga = pygame.time.get_ticks()

    # Processo de descarregamento
    if em_descarga:
        # O barco volta ao porto
        barco.voltar_ao_porto()
        # Tempo de descarga (ex: 2 segundos)
        if pygame.time.get_ticks() - tempo_descarga > 2000:
            barco.carga = 0
            em_descarga = False
        continue  # pula o restante do loop enquanto descarrega

    # Atualiza o movimento do barco com as teclas
    barco.update(keys)

    # Atualiza as moedas
    moedas.update()

    # Detecta colisões entre moedas e o barco
    colisoes = pygame.sprite.spritecollide(barco, moedas, True)
    for moeda in colisoes:
        barco.carga += 1
        # Quando uma moeda é capturada, cria uma nova moeda em posição aleatória
        x = random.randint(0, WIDTH - 20)
        y = random.randint(-50, -10)
        speed = random.uniform(v_min, v_max)
        moedas.add(Coin(x, y, speed))

    # Verifica se é necessário gerar novas moedas para manter o total
    while len(moedas) < qtd_moedas:
        x = random.randint(0, WIDTH - 20)
        y = random.randint(-100, -10)
        speed = random.uniform(v_min, v_max)
        moedas.add(Coin(x, y, speed))

    # Desenho na tela
    screen.fill(BG_COLOR)
    # Antes de desenhar outros elementos, insira:
    if background_img:
        screen.blit(background_img, (0, 0))
    # Desenha o mar
    screen.blit(sea_sprite, sea_rect)
    # Desenha o porto
    screen.blit(port_sprite, port_rect)
    # Desenha as moedas
    moedas.draw(screen)
    # Desenha o barco
    todos_sprites.draw(screen)

    # Display de informações
    info_text = f'Moedas capturadas: {barco.carga}/{barco.max_carga}'
    nivel_texto = f'Nível: {nivel}'
    text_surface = FONT.render(info_text, True, (255, 255, 255))
    screen.blit(text_surface, (10, 10))
    nivel_surface = FONT.render(nivel_texto, True, (255, 255, 255))
    screen.blit(nivel_surface, (10, 50))

    # Condição de avanço de nível
    if barco.carga >= barco.max_carga:
        # Pode incluir mudança de nível ou evento especial
        nivel += 1
        if nivel > 3:
            nivel = 3  # limite máximo
        qtd_moedas, v_min, v_max = configurar_dificuldade(nivel)
        # ajusta quantidade de moedas e suas velocidades
        # Se desejar, pode criar novas moedas ou ajustar o jogo aqui

    # Atualiza a tela
    pygame.display.flip()

# Encerra o pygame
pygame.quit()
sys.exit()

