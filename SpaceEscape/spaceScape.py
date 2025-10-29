import pygame
import random
import os

# Definição de cores auxiliares
YELLOW = (255, 215, 0)

# Inicializa o PyGame
pygame.init()

# Caminho base dos assets relativo a este arquivo
ASSET_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------
# 🔧 CONFIGURAÇÕES GERAIS DO JOGO
# ----------------------------------------------------------
WIDTH, HEIGHT = 800, 600
FPS = 60
pygame.display.set_caption("🚀 Space Escape")

ASSETS = {
    "background_level_1": "level_1.png",                         # imagem de fundo
    "background_menu": "fundo_menu.png",                        # imagem de fundo
    "endgame_bg": "endgame.png",                                # imagem da tela de fim de jogo
    "player": "nave1.png",                                      # imagem da nave (padrão/idle/baixo)
    "player_up": "nave2.png",                                   # imagem da nave quando movendo para cima
    "meteor": "meteoro001.png",                                 # imagem do meteoro
    "meteor2": "meteoro002.png",                                # imagem do meteoro
    "sound_point": "classic-game-action-positive-5-224402.mp3", # som ao desviar com sucesso
    "sound_hit": "stab-f-01-brvhrtz-224599.mp3",                # som de colisão
    "music": "game-gaming-background-music-385611.mp3"          # música de fundo. direitos: Music by Maksym Malko from Pixabay
}

# ----------------------------------------------------------
# 🖼️ CARREGAMENTO DE IMAGENS E SONS
# ----------------------------------------------------------
# Cores para fallback (caso os arquivos não existam)
WHITE = (255, 255, 255)
RED = (255, 60, 60)
BLUE = (60, 100, 255)

# Tela do jogo
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Resolvedor de caminho relativo aos assets
def resolve_path(name):
    return name if os.path.isabs(name) else os.path.join(ASSET_DIR, name)

# Função auxiliar para carregar imagens de forma segura
def load_image(filename, fallback_color, size=None):
    path = resolve_path(filename)
    if os.path.exists(path):
        imagem_load = pygame.image.load(path).convert_alpha()
        if size:
            imagem_load = pygame.transform.scale(imagem_load, size)
        return imagem_load
    else:
        # Gera uma superfície simples colorida se a imagem não existir
        surf = pygame.Surface(size or (50, 50))
        surf.fill(fallback_color)
        return surf

# Carrega imagens
background = load_image(ASSETS["background_level_1"], WHITE, (WIDTH, HEIGHT))
background_menu = load_image(ASSETS["background_menu"], WHITE, (WIDTH, HEIGHT))
endgame_bg = load_image(ASSETS["endgame_bg"], WHITE, (WIDTH, HEIGHT))
# Sprites da nave: idle/baixo e subindo
player_img_idle = load_image(ASSETS["player"], BLUE, (80, 60))
player_img_up = load_image(ASSETS.get("player_up", ASSETS["player"]), BLUE, (200, 140))
current_player_img = player_img_idle
meteor_img = load_image(ASSETS["meteor"], RED, (40, 40))
meteor_img2 = load_image(ASSETS["meteor2"], YELLOW, (40, 40))

# Sons
def load_sound(filename):
    path = resolve_path(filename)
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    return None

sound_point = load_sound(ASSETS["sound_point"])
sound_hit = load_sound(ASSETS["sound_hit"])

# Música de fundo (opcional)
music_path = resolve_path(ASSETS["music"])
if os.path.exists(music_path):
    try:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)  # loop infinito
    except Exception as e:
        print(f"Aviso: não foi possível tocar música de fundo em {music_path}: {e}")

# ----------------------------------------------------------
# 🧠 VARIÁVEIS E ESTADO DO JOGO
# ----------------------------------------------------------
font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()

# Configurações por dificuldade
DIFFICULTIES = {
    "Fácil":   {"meteors": 5,  "speed_min": 2, "speed_max": 5, "lives": 5},
    "Normal":  {"meteors": 8,  "speed_min": 3, "speed_max": 7, "lives": 3},
    "Difícil": {"meteors": 12, "speed_min": 4, "speed_max": 9, "lives": 2},
}
current_difficulty = "Normal"
player_speed = 7
meteor_images = [meteor_img, meteor_img2]
SAVE_PATH = os.path.join(ASSET_DIR, "savegame.json")

# ----------------------------------------------------------
# 🗺️ FASES DO JOGO
# ----------------------------------------------------------
current_phase_index = 0  # 0 = Fase 1, 1 = Fase 2, ...

# Estados do fluxo de jogo: "playing" (jogando), "phase_victory" (tela de vitória)
game_mode = "playing"
phase_victory_end_ms = None  # timestamp (ms) quando a contagem regressiva termina

# Metas de pontuação por fase (cumulativas). Ex.: Fase 1 = 100, Fase 2 = 200, ...
PHASE_TARGET_BASE = 100

def get_phase_target(phase_index):
    return PHASE_TARGET_BASE * (phase_index + 1)


def get_phase_config(base_cfg, phase_index):
    """Retorna a configuração da fase a partir da dificuldade base e do índice da fase.
    A cada fase, aumentamos levemente a quantidade e a velocidade dos meteoros.
    """
    # Escalonamento simples: +2 meteoros por fase, +1 na velocidade mínima e máxima por fase
    return {
        "meteors": base_cfg["meteors"] + 2 * phase_index,
        "speed_min": base_cfg["speed_min"] + phase_index,
        "speed_max": base_cfg["speed_max"] + phase_index,
        "lives": base_cfg["lives"],  # vidas não aumentam automaticamente
    }


def build_meteors_for_phase(phase_index):
    base = DIFFICULTIES.get(current_difficulty, DIFFICULTIES["Normal"])
    return build_meteors(get_phase_config(base, phase_index))


# Helpers para estado
def build_meteors(selected_difficulty):
    build_meteor_list = []
    for _ in range(selected_difficulty["meteors"]):
        x = random.randint(0, WIDTH - 40)
        y = random.randint(-500, -40)
        bm_rect = pygame.Rect(x, y, 40, 40)
        speed = random.randint(selected_difficulty["speed_min"], selected_difficulty["speed_max"])
        img = random.choice(meteor_images)
        build_meteor_list.append({"rect": bm_rect, "img": img, "speed": speed})
    return build_meteor_list

def create_new_game_state():
    selected_difficulty = DIFFICULTIES[current_difficulty]
    state = {
        "difficulty": current_difficulty,
        "player_rect": player_img_idle.get_rect(center=(WIDTH // 2, HEIGHT - 60)),
        "score": 0,
        "lives": selected_difficulty["lives"],
        "phase": 0,
        "meteors": build_meteors(get_phase_config(selected_difficulty, 0)),
    }
    return state

def get_saved_highscore():
    try:
        import json
        if not os.path.exists(SAVE_PATH):
            return 0
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return int(data.get("highscore", 0))
    except Exception:
        return 0


def save_game(state):
    try:
        # Atualiza e persiste o highscore
        prev_high = get_saved_highscore()
        new_highscore = max(prev_high, int(state["score"]))
        data = {
            "difficulty": state["difficulty"],
            "score": int(state["score"]),
            "lives": int(state["lives"]),
            "phase": int(state.get("phase", 0)),
            "player": {"x": int(state["player_rect"].x), "y": int(state["player_rect"].y)},
            "highscore": new_highscore,
        }
        import json
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return new_highscore
    except Exception as exception:
        print(f"Aviso: falha ao salvar jogo: {exception}")
        return None

def load_game_state():
    try:
        import json
        if not os.path.exists(SAVE_PATH):
            return None
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        diff = data.get("difficulty", "Normal")
        # Ajusta configuração e recria meteoros conforme a fase salva
        selected_difficulty = DIFFICULTIES.get(diff, DIFFICULTIES["Normal"])
        phase_idx = int(data.get("phase", 0))
        state = {
            "difficulty": diff,
            "player_rect": player_img_idle.get_rect(center=(WIDTH // 2, HEIGHT - 60)),
            "score": int(data.get("score", 0)),
            "lives": int(data.get("lives", selected_difficulty["lives"])),
            "phase": phase_idx,
            "meteors": build_meteors(get_phase_config(selected_difficulty, phase_idx)),
        }
        # Reposiciona player se existir no save
        p = data.get("player", {})
        state["player_rect"].x = int(p.get("x", state["player_rect"].x))
        state["player_rect"].y = int(p.get("y", state["player_rect"].y))
        return state
    except Exception as exception:
        print(f"Aviso: falha ao carregar jogo: {exception}")
        return None

# ----------------------------------------------------------
# 🧭 MENU INICIAL (Novo jogo, Carregar, Dificuldade, Sair)
# ----------------------------------------------------------
menu_font = pygame.font.Font(None, 64)
small_font = pygame.font.Font(None, 36)
menu_options = ["Novo jogo", "Carregar jogo salvo", "Escolher dificuldade", "Sair"]
selected = 0

showing_menu = True
pending_message = ""
message_timer = 0

while showing_menu:
    screen.blit(background_menu, (0, 0))

    title = menu_font.render("🚀 SPACE ESCAPE 🚀", True, YELLOW)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))

    # Lista de opções
    start_y = 220
    for i, opt in enumerate(menu_options):
        color = YELLOW if i == selected else WHITE
        label = small_font.render(opt, True, color)
        screen.blit(label, (WIDTH // 2 - label.get_width() // 2, start_y + i * 40))

    # Mostrar dificuldade atual
    diff_text = small_font.render(f"Dificuldade atual: {current_difficulty}", True, WHITE)
    screen.blit(diff_text, (WIDTH // 2 - diff_text.get_width() // 2, start_y + len(menu_options) * 40 + 20))

    # Mensagem temporária
    if pending_message:
        msg = small_font.render(pending_message, True, WHITE)
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT - 80))
        message_timer -= 1
        if message_timer <= 0:
            pending_message = ""

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); exit()
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                selected = (selected + 1) % len(menu_options)
            elif event.key in (pygame.K_UP, pygame.K_w):
                selected = (selected - 1) % len(menu_options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                choice = menu_options[selected]
                if choice == "Novo jogo":
                    game_state = create_new_game_state()
                    showing_menu = False
                elif choice == "Carregar jogo salvo":
                    loaded = load_game_state()
                    if loaded:
                        game_state = loaded
                        current_difficulty = loaded["difficulty"]
                        showing_menu = False
                    else:
                        pending_message = "Nenhum jogo salvo encontrado."
                        message_timer = FPS * 2
                elif choice == "Escolher dificuldade":
                    # Submenu simples de dificuldade
                    diffs = list(DIFFICULTIES.keys())
                    d_selected = diffs.index(current_difficulty)
                    choosing = True
                    while choosing:
                        screen.blit(background_menu, (0, 0))
                        title2 = menu_font.render("Escolher dificuldade", True, YELLOW)
                        screen.blit(title2, (WIDTH // 2 - title2.get_width() // 2, 80))
                        for i, d in enumerate(diffs):
                            color = YELLOW if i == d_selected else WHITE
                            lab = small_font.render(d, True, color)
                            screen.blit(lab, (WIDTH // 2 - lab.get_width() // 2, 220 + i * 40))
                        hint = small_font.render("ENTER para confirmar • ESC para voltar", True, WHITE)
                        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 400))
                        pygame.display.flip()
                        for e2 in pygame.event.get():
                            if e2.type == pygame.QUIT:
                                pygame.quit(); exit()
                            elif e2.type == pygame.KEYDOWN:
                                if e2.key in (pygame.K_DOWN, pygame.K_s):
                                    d_selected = (d_selected + 1) % len(diffs)
                                elif e2.key in (pygame.K_UP, pygame.K_w):
                                    d_selected = (d_selected - 1) % len(diffs)
                                elif e2.key in (pygame.K_RETURN, pygame.K_SPACE):
                                    current_difficulty = diffs[d_selected]
                                    choosing = False
                                elif e2.key == pygame.K_ESCAPE:
                                    choosing = False
                elif choice == "Sair":
                    pygame.quit(); exit()
            elif event.key == pygame.K_ESCAPE:
                pygame.quit(); exit()

# agora sim começa o jogo de fato
running = True
# Inicializa variáveis a partir do estado
player_rect = game_state["player_rect"]
score = game_state["score"]
lives = game_state["lives"]
current_phase_index = int(game_state.get("phase", 0))
meteor_list = game_state["meteors"]
# Modo de jogo e controle de vitória de fase
game_mode = "playing"
phase_victory_end_ms = None

# ----------------------------------------------------------
# 🕹️ LOOP PRINCIPAL
# ----------------------------------------------------------
while running:
    clock.tick(FPS)
    screen.blit(background, (0, 0))

    # --- Eventos ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Se estamos na tela de vitória da fase, desenha e aguarda o cronômetro
    if game_mode == "phase_victory":
        screen.blit(background, (0, 0))
        # Mensagens de vitória
        big_font = pygame.font.Font(None, 96)
        mid_font = pygame.font.Font(None, 48)
        title = big_font.render("Fase vencida!", True, YELLOW)
        phase_label = mid_font.render(f"Fase {current_phase_index + 1} concluída!", True, WHITE)
        # Cronômetro restante
        now_ms = pygame.time.get_ticks()
        remaining_ms = max(0, (phase_victory_end_ms or now_ms) - now_ms)
        remaining_sec = (remaining_ms // 1000) + (1 if remaining_ms % 1000 > 0 else 0)
        timer_text = mid_font.render(f"Próxima fase em {remaining_sec}s...", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 180))
        screen.blit(phase_label, (WIDTH // 2 - phase_label.get_width() // 2, 260))
        screen.blit(timer_text, (WIDTH // 2 - timer_text.get_width() // 2, 320))
        pygame.display.flip()

        if phase_victory_end_ms is not None and now_ms >= phase_victory_end_ms:
            # Avança para a próxima fase
            current_phase_index += 1
            # Reposiciona o jogador e recria meteoros com a nova configuração
            player_rect = player_img_idle.get_rect(center=(WIDTH // 2, HEIGHT - 60))
            base_cfg = DIFFICULTIES.get(current_difficulty, DIFFICULTIES["Normal"])
            meteor_list = build_meteors(get_phase_config(base_cfg, current_phase_index))
            # Volta a jogar
            game_mode = "playing"
            phase_victory_end_ms = None
        continue  # não processa lógica de jogo enquanto exibe a vitória

    # --- Movimento do jogador ---
    keys = pygame.key.get_pressed()
    # Esquerda/Direita
    if keys[pygame.K_LEFT] and player_rect.left > 0:
        player_rect.x -= player_speed
    if keys[pygame.K_RIGHT] and player_rect.right < WIDTH:
        player_rect.x += player_speed
    # Cima/Baixo
    if keys[pygame.K_UP] and player_rect.top > 0:
        player_rect.y -= player_speed
    if keys[pygame.K_DOWN] and player_rect.bottom < HEIGHT:
        player_rect.y += player_speed

    # Alterar sprite conforme movimento vertical
    if keys[pygame.K_UP]:
        current_player_img = player_img_up
    else:
        # Parado ou movendo para baixo usa nave1
        current_player_img = player_img_idle

    # --- Movimento dos meteoros ---
    for m in meteor_list:
        rect = m["rect"]
        rect.y += m["speed"]

        # Saiu da tela → reposiciona e soma pontos
        if rect.y > HEIGHT:
            rect.y = random.randint(-100, -40)
            rect.x = random.randint(0, WIDTH - rect.width)
            # opcionalmente randomizar novo speed e imagem
            base_cfg = DIFFICULTIES.get(current_difficulty, DIFFICULTIES["Normal"])
            cfg = get_phase_config(base_cfg, current_phase_index)
            m["speed"] = random.randint(cfg["speed_min"], cfg["speed_max"])
            m["img"] = random.choice(meteor_images)
            score += 1
            if sound_point:
                sound_point.play()

        # Colisão
        if rect.colliderect(player_rect):
            lives -= 1
            if score > 0 and score < 50 == 0:
                score -= 2
            elif score > 50:
                score -= 5
            elif score < 0:
                score = 0
            rect.y = random.randint(-100, -40)
            rect.x = random.randint(0, WIDTH - rect.width)
            cfg = DIFFICULTIES.get(current_difficulty, DIFFICULTIES["Normal"])
            m["speed"] = random.randint(cfg["speed_min"], cfg["speed_max"])
            if sound_hit:
                sound_hit.play()
            if lives <= 0:
                running = False

    # Verifica vitória da fase atual
    if score >= get_phase_target(current_phase_index):
        # Entra na tela de vitória por 5s
        game_mode = "phase_victory"
        phase_victory_end_ms = pygame.time.get_ticks() + 5000

    # --- Desenha tudo ---
    screen.blit(current_player_img, player_rect)
    for m in meteor_list:
        screen.blit(m["img"], m["rect"])

    # --- Exibe pontuação, vidas e fase ---
    text = font.render(f"Pontos: {score}   Vidas: {lives}   Fase: {current_phase_index + 1}", True, WHITE)
    screen.blit(text, (10, 10))

    pygame.display.flip()

# ----------------------------------------------------------
# 🏁 TELA DE FIM DE JOGO
# ----------------------------------------------------------
# Salvar jogo automaticamente (estado final) e obter highscore
new_high = save_game({
    "difficulty": current_difficulty,
    "player_rect": player_rect,
    "score": score,
    "lives": lives,
})
if new_high is None:
    new_high = get_saved_highscore()

pygame.mixer.music.stop()

# Desenhar tela final com imagem de fundo
screen.blit(endgame_bg, (0, 0))

# Título "GAME OVER" em vermelho
big_font = pygame.font.Font(None, 96)
end_title = big_font.render("GAME OVER", True, (255, 0, 0))
screen.blit(end_title, (WIDTH // 2 - end_title.get_width() // 2, 120))

# Informações: fase, dificuldade, pontuação atual e maior pontuação
info_font = pygame.font.Font(None, 48)
label_fase = info_font.render(f"Fase: {current_phase_index + 1}", True, WHITE)
label_diff = info_font.render(f"Dificuldade: {current_difficulty}", True, WHITE)
label_score = info_font.render(f"Pontuação: {score}", True, WHITE)
label_high = info_font.render(f"Maior pontuação: {new_high}", True, WHITE)

center_x = WIDTH // 2
start_y = 260
for i, surf in enumerate([label_fase, label_diff, label_score, label_high]):
    screen.blit(surf, (center_x - surf.get_width() // 2, start_y + i * 50))

hint = font.render("Pressione qualquer tecla para sair", True, WHITE)
screen.blit(hint, (center_x - hint.get_width() // 2, HEIGHT - 80))

pygame.display.flip()

waiting = True
while waiting:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
            waiting = False

pygame.quit()
