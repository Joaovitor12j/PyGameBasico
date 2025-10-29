import pygame
import random
import os
import json
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional

# =============================================================================
# CONSTANTES
# =============================================================================

class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    PHASE_VICTORY = "phase_victory"
    GAME_OVER = "game_over"

@dataclass
class GameConfig:
    """Configurações gerais do jogo"""
    WIDTH: int = 800
    HEIGHT: int = 600
    FPS: int = 60
    TITLE: str = "🚀 Space Escape"
    SAVE_FILE: str = "savegame.json"
    PHASE_TARGET_BASE: int = 100
    PHASE_VICTORY_DURATION: int = 5000  # ms

@dataclass
class DifficultyConfig:
    """Configuração de dificuldade"""
    meteors: int
    speed_min: int
    speed_max: int
    lives: int

    def scale_for_phase(self, phase: int):
        """Retorna configuração escalada para a fase"""
        return DifficultyConfig(
            meteors=self.meteors + 2 * phase,
            speed_min=self.speed_min + phase,
            speed_max=self.speed_max + phase,
            lives=self.lives
        )


# Dificuldades disponíveis
DIFFICULTIES = {
    "Fácil": DifficultyConfig(meteors=3, speed_min=2, speed_max=4, lives=20),
    "Normal": DifficultyConfig(meteors=6, speed_min=3, speed_max=6, lives=10),
    "Difícil": DifficultyConfig(meteors=10, speed_min=4, speed_max=8, lives=5),
}

# Cores
class Colors:
    WHITE = (255, 255, 255)
    RED = (255, 60, 60)
    BLUE = (60, 100, 255)
    YELLOW = (255, 215, 0)
    DARK_RED = (255, 0, 0)

# Assets
ASSETS = {
    "background_level_1": "level_1.png",
    "background_level_2": "level_2.png",
    "background_level_3": "level_3.png",
    "background_menu": "fundo_menu.png",
    "endgame_bg": "endgame.png",
    "player": "nave1.png",
    "player_up": "nave2.png",
    "meteor": "meteoro001.png",
    "meteor2": "meteoro002.png",
    "sound_point": "classic-game-action-positive-5-224402.mp3",
    "sound_hit": "stab-f-01-brvhrtz-224599.mp3",
    "music": "game-gaming-background-music-385611.mp3",
    "item_collect": "star.png",
}

# Dimensões padrão
class Sizes:
    PLAYER_IDLE = (80, 60)
    PLAYER_UP = (200, 140)
    METEOR = (40, 40)
    ITEM = (32, 32)
    PLAYER_SPEED = 7

# =============================================================================
# GERENCIADOR DE RECURSOS
# =============================================================================
class ResourceManager:
    """Gerencia carregamento de imagens e sons"""
    def __init__(self, asset_dir: str):
        self.asset_dir = asset_dir
        self.images = {}
        self.sounds = {}

    def _resolve_path(self, filename: str) -> str:
        """Resolve caminho relativo ao diretório de assets"""
        if os.path.isabs(filename):
            return filename
        return os.path.join(self.asset_dir, filename)

    def load_image(self, key: str, filename: str, size: tuple,
                   fallback_color: tuple) -> pygame.Surface:
        """Carrega imagem com fallback para cor sólida"""
        if key in self.images:
            return self.images[key]

        path = self._resolve_path(filename)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, size)
        else:
            img = pygame.Surface(size)
            img.fill(fallback_color)

        self.images[key] = img
        return img

    def load_sound(self, key: str, filename: str) -> Optional[pygame.mixer.Sound]:
        """Carrega som"""
        if key in self.sounds:
            return self.sounds[key]

        path = self._resolve_path(filename)
        if os.path.exists(path):
            sound = pygame.mixer.Sound(path)
            self.sounds[key] = sound
            return sound
        return None

    def load_music(self, filename: str, volume: float = 0.3) -> bool:
        """Carrega e toca música de fundo"""
        path = self._resolve_path(filename)
        if os.path.exists(path):
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(-1)
                return True
            except Exception as e:
                print(f"Aviso: erro ao carregar música: {e}")
        return False

# =============================================================================
# ENTIDADES DO JOGO
# =============================================================================

class Meteor:
    """Representa um meteoro"""
    def __init__(self, x: int, y: int, speed: int, image: pygame.Surface):
        self.rect = pygame.Rect(x, y, Sizes.METEOR[0], Sizes.METEOR[1])
        self.speed = speed
        self.image = image

    def update(self, screen_height: int) -> bool:
        """Atualiza posição. Retorna True se saiu da tela"""
        self.rect.y += self.speed
        return self.rect.y > screen_height

    def randomize_position(self, screen_width: int):
        """Reposiciona no topo com posição X aleatória"""
        self.rect.y = random.randint(-100, -40)
        self.rect.x = random.randint(0, screen_width - self.rect.width)

    def draw(self, screen: pygame.Surface):
        """Desenha o meteoro"""
        screen.blit(self.image, self.rect)

class Item:
    """Representa um item coletável"""
    def __init__(self, x: int, y: int, speed: int, image: pygame.Surface):
        self.rect = pygame.Rect(x, y, Sizes.ITEM[0], Sizes.ITEM[1])
        self.speed = speed
        self.image = image

    def update(self, screen_height: int) -> bool:
        """Move para baixo. Retorna True se saiu da tela."""
        self.rect.y += self.speed
        return self.rect.y > screen_height

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect)

class Player:
    """Representa o jogador"""
    def __init__(self, x: int, y: int, idle_img: pygame.Surface,
                 up_img: pygame.Surface):
        self.idle_img = idle_img
        self.up_img = up_img
        self.rect = idle_img.get_rect(center=(x, y))
        self.speed = Sizes.PLAYER_SPEED
        self.current_img = idle_img
        self.moving_up = False

    def move_to_position(self, x: int, y: int, screen_width: int, screen_height: int):
        half_w, half_h = self.rect.width // 2, self.rect.height // 2
        clamped_x = max(half_w, min(screen_width - half_w, x))
        clamped_y = max(half_h, min(screen_height - half_h, y))
        self.rect.center = (clamped_x, clamped_y)

    def update(self, keys, screen_width: int, screen_height: int):
        # Movimento horizontal (Setas e WASD)
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.rect.left > 0:
            self.rect.x -= self.speed
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.rect.right < screen_width:
            self.rect.x += self.speed

        # Movimento vertical (Setas e WASD)
        self.moving_up = False
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and self.rect.top > 0:
            self.rect.y -= self.speed
            self.moving_up = True
        if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and self.rect.bottom < screen_height:
            self.rect.y += self.speed

        # Atualiza sprite
        self.current_img = self.up_img if self.moving_up else self.idle_img

    def draw(self, screen: pygame.Surface):
        """Desenha o jogador"""
        screen.blit(self.current_img, self.rect)

    def reset_position(self, x: int, y: int):
        """Reposiciona o jogador"""
        self.rect.center = (x, y)

# =============================================================================
# GERENCIADOR DE SAVE
# =============================================================================

class SaveManager:
    """Gerencia salvamento e carregamento do jogo"""
    def __init__(self, save_path: str):
        self.save_path = save_path

    def save(self, difficulty: str, score: int, lives: int,
             phase: int, player_pos: tuple,
             items_collected: int = 0, boss_defeated: bool = False) -> int:
        """Salva o jogo e retorna o highscore atualizado"""
        try:
            highscore = max(self.get_highscore(), score)
            data = {
                "difficulty": difficulty,
                "score": score,
                "lives": lives,
                "phase": phase,
                "player": {"x": player_pos[0], "y": player_pos[1]},
                "items_collected": items_collected,
                "boss_defeated": boss_defeated,
                "highscore": highscore
            }
            with open(self.save_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            return highscore
        except Exception as e:
            print(f"Erro ao salvar: {e}")
            return self.get_highscore()

    def load(self) -> Optional[Dict]:
        """Carrega jogo salvo"""
        try:
            if not os.path.exists(self.save_path):
                return None
            with open(self.save_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar: {e}")
            return None

    def get_highscore(self) -> int:
        """Retorna o highscore salvo"""
        data = self.load()
        return data.get("highscore", 0) if data else 0


# =============================================================================
# GAME ENGINE
# =============================================================================

class SpaceEscape:
    """Classe principal do jogo"""
    def __init__(self):
        pygame.init()

        self.config = GameConfig()
        self.screen = pygame.display.set_mode((self.config.WIDTH, self.config.HEIGHT))
        pygame.display.set_caption(self.config.TITLE)
        self.clock = pygame.time.Clock()

        # Gerenciadores
        asset_dir = os.path.dirname(os.path.abspath(__file__))
        self.resources = ResourceManager(asset_dir)
        self.save_manager = SaveManager(os.path.join(asset_dir, self.config.SAVE_FILE))

        # Carrega recursos
        self._load_resources()

        # Estado do jogo
        self.state = GameState.MENU
        self.difficulty = "Normal"
        self.score = 0
        self.lives = 0
        self.phase = 0
        self.meteors: List[Meteor] = []
        self.player = None
        self.phase_victory_end = None
        # Progresso por fase
        self.items_collected = 0  # Itens coletados na fase atual
        self.boss_defeated = False  # Status do chefe (usado na fase 3)
        # Itens coletáveis e agendamento de spawn
        self.items: List[Item] = []
        self.next_item_spawn_score: Optional[int] = None

        # Fontes
        self.font_large = pygame.font.Font(None, 96)
        self.font_medium = pygame.font.Font(None, 64)
        self.font_small = pygame.font.Font(None, 48)
        self.font_tiny = pygame.font.Font(None, 36)

    def _load_resources(self):
        """Carrega todos os recursos do jogo"""
        # Imagens
        # Planos de fundo por fase
        self.bg_levels = [
            self.resources.load_image("bg_level_1", ASSETS["background_level_1"], (self.config.WIDTH, self.config.HEIGHT), Colors.WHITE),
            self.resources.load_image("bg_level_2", ASSETS["background_level_2"], (self.config.WIDTH, self.config.HEIGHT), Colors.WHITE),
            self.resources.load_image("bg_level_3", ASSETS["background_level_3"], (self.config.WIDTH, self.config.HEIGHT), Colors.WHITE),
        ]
        self.bg_menu = self.resources.load_image(
            "bg_menu", ASSETS["background_menu"],
            (self.config.WIDTH, self.config.HEIGHT), Colors.WHITE
        )
        self.bg_endgame = self.resources.load_image(
            "bg_endgame", ASSETS["endgame_bg"],
            (self.config.WIDTH, self.config.HEIGHT), Colors.WHITE
        )

        self.player_idle = self.resources.load_image(
            "player_idle", ASSETS["player"], Sizes.PLAYER_IDLE, Colors.BLUE
        )
        self.player_up = self.resources.load_image(
            "player_up", ASSETS["player_up"], Sizes.PLAYER_UP, Colors.BLUE
        )

        self.meteor_imgs = [
            self.resources.load_image("meteor1", ASSETS["meteor"],
                                      Sizes.METEOR, Colors.RED),
            self.resources.load_image("meteor2", ASSETS["meteor2"],
                                      Sizes.METEOR, Colors.YELLOW)
        ]

        # Item coletável
        self.item_img = self.resources.load_image(
            "item_collect", ASSETS["item_collect"], Sizes.ITEM, Colors.YELLOW
        )

        # Sons
        self.sound_point = self.resources.load_sound("point", ASSETS["sound_point"])
        self.sound_hit = self.resources.load_sound("hit", ASSETS["sound_hit"])
        self.resources.load_music(ASSETS["music"])

    def _create_meteors(self, config: DifficultyConfig) -> List[Meteor]:
        """Cria lista de meteoros baseado na configuração"""
        meteors = []
        for _ in range(config.meteors):
            x = random.randint(0, self.config.WIDTH - Sizes.METEOR[0])
            y = random.randint(-500, -40)
            speed = random.randint(config.speed_min, config.speed_max)
            img = random.choice(self.meteor_imgs)
            meteors.append(Meteor(x, y, speed, img))
        return meteors

    def new_game(self):
        """Inicia um novo jogo"""
        diff_config = DIFFICULTIES[self.difficulty]
        self.score = 0
        self.lives = diff_config.lives
        self.phase = 0
        self.items_collected = 0
        self.boss_defeated = False
        self.items = []
        self.next_item_spawn_score = None
        self.player = Player(
            self.config.WIDTH // 2, self.config.HEIGHT - 60,
            self.player_idle, self.player_up
        )
        self.meteors = self._create_meteors(diff_config.scale_for_phase(0))
        self._reset_item_spawn_schedule()
        self.state = GameState.PLAYING

    def load_game(self) -> bool:
        """Carrega jogo salvo. Retorna True se bem-sucedido"""
        data = self.save_manager.load()
        if not data:
            return False

        self.difficulty = data.get("difficulty", "Normal")
        self.score = data.get("score", 0)
        self.lives = data.get("lives", 3)
        self.phase = data.get("phase", 0)
        # Progresso por fase
        self.items_collected = data.get("items_collected", 0)
        self.boss_defeated = data.get("boss_defeated", False)
        # Itens ativos no mundo (não persistidos)
        self.items = []
        self.next_item_spawn_score = None

        diff_config = DIFFICULTIES[self.difficulty]
        self.player = Player(
            self.config.WIDTH // 2, self.config.HEIGHT - 60,
            self.player_idle, self.player_up
        )

        player_data = data.get("player", {})
        if player_data:
            self.player.rect.x = player_data.get("x", self.player.rect.x)
            self.player.rect.y = player_data.get("y", self.player.rect.y)

        self.meteors = self._create_meteors(diff_config.scale_for_phase(self.phase))
        self._reset_item_spawn_schedule()
        self.state = GameState.PLAYING
        return True

    def _get_phase_target(self) -> int:
        """Retorna pontuação necessária para completar a fase atual segundo as regras:
        Fase 1: 100+ pontos
        Fase 2: 250+ pontos
        Fase 3+: 350+ pontos
        """
        if self.phase == 0:
            return 100
        elif self.phase == 1:
            return 250
        else:
            return 350

    def _get_phase_required_items(self) -> int:
        """Quantidade de itens necessários para a fase atual (F2 e F3 requerem 3)"""
        if self.phase >= 1:
            return 3
        return 0

    def _is_boss_required(self) -> bool:
        """Indica se a fase atual requer derrotar chefe (Fase 3 em diante)"""
        return self.phase >= 2

    def _has_phase_victory(self) -> bool:
        """Valida as condições de vitória da fase atual."""
        # Pontos
        if self.score < self._get_phase_target():
            return False
        # Itens
        if self.items_collected < self._get_phase_required_items():
            return False
        # Chefe (se requerido)
        if self._is_boss_required() and not self.boss_defeated:
            return False
        return True

    def _get_bg_for_current_phase(self) -> pygame.Surface:
        """Retorna o background correspondente à fase atual.
        Mapeamento: fase 1->bg1, fase 2->bg2, fase 3+->bg3."""
        idx = 0
        if self.phase >= 2:
            idx = 2
        elif self.phase == 1:
            idx = 1
        return self.bg_levels[idx]

    # =============================
    # Itens coletáveis - Fase 2 e 3
    # =============================
    def _is_item_enabled(self) -> bool:
        """Itens aparecem a partir da Fase 2 (phase==1) e Fase 3+ (phase>=2)."""
        return self.phase >= 1

    def _item_speed_for_phase(self) -> int:
        """Velocidade do item por fase: Fase 2 -> 7, Fase 3+ -> 8."""
        return 7 if self.phase == 1 else 8

    def _next_multiple_of_20_above(self, value: int) -> int:
        rem = value % 20
        return value + (20 - rem) if rem != 0 else value + 20

    def _reset_item_spawn_schedule(self):
        """Inicializa o próximo marco de pontuação para spawn de item."""
        if self._is_item_enabled():
            self.next_item_spawn_score = self._next_multiple_of_20_above(self.score)
        else:
            self.next_item_spawn_score = None

    def _spawn_item(self):
        """Cria um item no topo com posição X aleatória.
        Garante que apenas um item esteja ativo por vez."""
        # Salvaguarda adicional: não spawna se já existe item ativo
        if len(self.items) > 0:
            return
        x = random.randint(0, self.config.WIDTH - Sizes.ITEM[0])
        y = random.randint(-200, -40)
        speed = self._item_speed_for_phase()
        self.items.append(Item(x, y, speed, self.item_img))

    def _handle_meteor_collision(self):
        """Processa colisão com meteoro"""
        self.lives -= 1 # Dano de vida

        # Penalidade de pontos (BUG CORRIGIDO)
        if 0 < self.score < 50:
            self.score = max(0, self.score - 2)
        elif self.score >= 50:
            self.score = max(0, self.score - 5)

        if self.sound_hit:
            self.sound_hit.play()

    def _advance_phase(self):
        """Avança para a próxima fase"""
        self.phase += 1
        # Reseta progresso específico da fase
        self.items_collected = 0
        self.boss_defeated = False
        # Limpa itens e reprograma spawns para a nova fase
        self.items = []
        self._reset_item_spawn_schedule()
        # Reposiciona jogador e recria meteoros com dificuldade escalada
        self.player.reset_position(self.config.WIDTH // 2, self.config.HEIGHT - 60)
        diff_config = DIFFICULTIES[self.difficulty]
        self.meteors = self._create_meteors(diff_config.scale_for_phase(self.phase))
        self.state = GameState.PLAYING
        self.phase_victory_end = None

    def update_gameplay(self):
        """Atualiza lógica do gameplay"""
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.config.WIDTH, self.config.HEIGHT)

        diff_config = DIFFICULTIES[self.difficulty].scale_for_phase(self.phase)

        for meteor in self.meteors:
            if meteor.update(self.config.HEIGHT):
                # Meteoro saiu da tela
                meteor.randomize_position(self.config.WIDTH)
                meteor.speed = random.randint(diff_config.speed_min, diff_config.speed_max)
                meteor.image = random.choice(self.meteor_imgs)
                self.score += 1 # Pontuação do meteoro
                if self.sound_point:
                    self.sound_point.play()

            # Verifica colisão
            if meteor.rect.colliderect(self.player.rect):
                self._handle_meteor_collision()
                meteor.randomize_position(self.config.WIDTH)
                meteor.speed = random.randint(diff_config.speed_min, diff_config.speed_max)

                if self.lives <= 0:
                    self.state = GameState.GAME_OVER
                    return

        # Spawns de itens por pontuação (Fase 2 e 3) — apenas 1 por vez e exatamente a cada +20 pontos
        if self._is_item_enabled():
            if self.next_item_spawn_score is None:
                self._reset_item_spawn_schedule()
            # Apenas quando cruza o limiar atual; sem acumular múltiplos
            if self.next_item_spawn_score is not None and self.score >= self.next_item_spawn_score:
                if len(self.items) == 0:
                    self._spawn_item()
                # Avança o agendamento para o próximo múltiplo de 20 sempre
                self.next_item_spawn_score += 20

        # Atualiza itens e checa coleta
        for item in self.items[:]:
            if item.update(self.config.HEIGHT):
                # Saiu da tela
                self.items.remove(item)
                continue
            if item.rect.colliderect(self.player.rect):
                self.items.remove(item)
                self.items_collected += 1
                if self.sound_point:
                    self.sound_point.play()

        # Verifica vitória da fase (todas as condições desta fase)
        if self._has_phase_victory():
            self.state = GameState.PHASE_VICTORY
            self.phase_victory_end = pygame.time.get_ticks() + self.config.PHASE_VICTORY_DURATION

    def draw_gameplay(self):
        """Desenha o gameplay"""
        self.screen.blit(self._get_bg_for_current_phase(), (0, 0))

        # Desenha meteoros e itens
        for meteor in self.meteors:
            meteor.draw(self.screen)
        for item in self.items:
            item.draw(self.screen)

        # Por último, o jogador por cima
        self.player.draw(self.screen)

        # HUD linha 1
        hud_text = self.font_tiny.render(
            f"Pontos: {self.score}   Vidas: {self.lives}   Fase: {self.phase + 1}",
            True, Colors.WHITE
        )
        self.screen.blit(hud_text, (10, 10))

        # HUD linha 2 - Objetivos da fase
        target_pts = self._get_phase_target()
        req_items = self._get_phase_required_items()
        boss_req = self._is_boss_required()
        obj_parts = [f"Objetivo: {self.score}/{target_pts} pts"]
        if req_items > 0:
            obj_parts.append(f"Itens: {self.items_collected}/{req_items}")
        if boss_req:
            obj_parts.append(f"Chefe: {'Derrotado' if self.boss_defeated else 'Não'}")
        hud2_text = self.font_tiny.render("  •  ".join(obj_parts), True, Colors.WHITE)
        self.screen.blit(hud2_text, (10, 40))

    def draw_phase_victory(self):
        """Desenha tela de vitória da fase"""
        self.screen.blit(self._get_bg_for_current_phase(), (0, 0))

        title = self.font_large.render("Fase vencida!", True, Colors.YELLOW)
        phase_label = self.font_small.render(
            f"Fase {self.phase + 1} concluída!", True, Colors.WHITE
        )

        # Cronômetro
        remaining_ms = max(0, self.phase_victory_end - pygame.time.get_ticks())
        remaining_sec = (remaining_ms // 1000) + (1 if remaining_ms % 1000 > 0 else 0)
        timer_text = self.font_small.render(
            f"Próxima fase em {remaining_sec}s...", True, Colors.WHITE
        )

        self.screen.blit(title,
                         (self.config.WIDTH // 2 - title.get_width() // 2, 180))
        self.screen.blit(phase_label,
                         (self.config.WIDTH // 2 - phase_label.get_width() // 2, 260))
        self.screen.blit(timer_text,
                         (self.config.WIDTH // 2 - timer_text.get_width() // 2, 320))

        # Verifica se deve avançar
        if pygame.time.get_ticks() >= self.phase_victory_end:
            self._advance_phase()

    def run_menu(self) -> bool:
        """Executa menu. Retorna False se deve sair do jogo"""
        menu_options = ["Novo jogo", "Carregar jogo salvo", "Escolher dificuldade", "Sair"]
        selected = 0
        message = ""
        message_timer = 0

        while self.state == GameState.MENU:
            self.screen.blit(self.bg_menu, (0, 0))

            # Título
            title = self.font_medium.render("🚀 SPACE ESCAPE 🚀", True, Colors.YELLOW)
            self.screen.blit(title, (self.config.WIDTH // 2 - title.get_width() // 2, 80))

            # Opções
            start_y = 220
            for i, opt in enumerate(menu_options):
                color = Colors.YELLOW if i == selected else Colors.WHITE
                label = self.font_tiny.render(opt, True, color)
                self.screen.blit(label,
                                 (self.config.WIDTH // 2 - label.get_width() // 2,
                                  start_y + i * 40))

            # Dificuldade atual
            diff_text = self.font_tiny.render(
                f"Dificuldade atual: {self.difficulty}", True, Colors.WHITE
            )
            self.screen.blit(diff_text, (self.config.WIDTH // 2 - diff_text.get_width() // 2, start_y + len(menu_options) * 40 + 20))

            # Mensagem temporária
            if message:
                msg = self.font_tiny.render(message, True, Colors.WHITE)
                self.screen.blit(msg, (self.config.WIDTH // 2 - msg.get_width() // 2, self.config.HEIGHT - 80))
                message_timer -= 1
                if message_timer <= 0:
                    message = ""

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        selected = (selected + 1) % len(menu_options)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        selected = (selected - 1) % len(menu_options)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        choice = menu_options[selected]
                        if choice == "Novo jogo":
                            self.new_game()
                        elif choice == "Carregar jogo salvo":
                            if not self.load_game():
                                message = "Nenhum jogo salvo encontrado."
                                message_timer = self.config.FPS * 2
                        elif choice == "Escolher dificuldade":
                            self._difficulty_menu()
                        elif choice == "Sair":
                            return False
                    elif event.key == pygame.K_ESCAPE:
                        return False

            self.clock.tick(self.config.FPS)

        return True

    def _difficulty_menu(self):
        """Menu de seleção de dificuldade"""
        diffs = list(DIFFICULTIES.keys())
        selected = diffs.index(self.difficulty)
        choosing = True

        while choosing:
            self.screen.blit(self.bg_menu, (0, 0))

            title = self.font_medium.render("Escolher dificuldade", True, Colors.YELLOW)
            self.screen.blit(title, (self.config.WIDTH // 2 - title.get_width() // 2, 80))

            for i, diff in enumerate(diffs):
                color = Colors.YELLOW if i == selected else Colors.WHITE
                label = self.font_tiny.render(diff, True, color)
                self.screen.blit(label, (self.config.WIDTH // 2 - label.get_width() // 2, 220 + i * 40))

            hint = self.font_tiny.render(
                "ENTER para confirmar • ESC para voltar", True, Colors.WHITE
            )
            self.screen.blit(hint, (self.config.WIDTH // 2 - hint.get_width() // 2, 400))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    choosing = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        selected = (selected + 1) % len(diffs)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        selected = (selected - 1) % len(diffs)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.difficulty = diffs[selected]
                        choosing = False
                    elif event.key == pygame.K_ESCAPE:
                        choosing = False

            self.clock.tick(self.config.FPS)

    def run_game_over(self) -> bool:
        """Executa tela de game over. Retorna False se deve sair"""
        # Salva jogo
        highscore = self.save_manager.save(
            self.difficulty, self.score, self.lives,
            self.phase, self.player.rect.center,
            items_collected=self.items_collected,
            boss_defeated=self.boss_defeated
        )

        pygame.mixer.music.stop()

        self.screen.blit(self.bg_endgame, (0, 0))

        # Título
        title = self.font_large.render("GAME OVER", True, Colors.DARK_RED)
        self.screen.blit(title, (self.config.WIDTH // 2 - title.get_width() // 2, 120))

        # Informações
        labels = [
            f"Fase: {self.phase + 1}",
            f"Dificuldade: {self.difficulty}",
            f"Pontuação: {self.score}",
            f"Maior pontuação: {highscore}"
        ]

        start_y = 260
        for i, text in enumerate(labels):
            label = self.font_small.render(text, True, Colors.WHITE)
            self.screen.blit(label, (self.config.WIDTH // 2 - label.get_width() // 2, start_y + i * 50))

        hint = self.font_tiny.render(
            "Pressione qualquer tecla para voltar ao menu", True, Colors.WHITE
        )
        self.screen.blit(hint, (self.config.WIDTH // 2 - hint.get_width() // 2, self.config.HEIGHT - 80))

        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    waiting = False
                    self.state = GameState.MENU

            self.clock.tick(self.config.FPS)

        return True

    def run(self):
        """Loop principal do jogo"""
        running = True

        while running:
            if self.state == GameState.MENU:
                running = self.run_menu()

            elif self.state == GameState.PLAYING:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEMOTION:
                        self.player.move_to_position(event.pos[0], event.pos[1], self.config.WIDTH, self.config.HEIGHT)
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        self.player.move_to_position(event.pos[0], event.pos[1], self.config.WIDTH, self.config.HEIGHT)

                if running:
                    self.update_gameplay()
                    self.draw_gameplay()
                    pygame.display.flip()
                    self.clock.tick(self.config.FPS)

            elif self.state == GameState.PHASE_VICTORY:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                if running:
                    self.draw_phase_victory()
                    pygame.display.flip()
                    self.clock.tick(self.config.FPS)

            elif self.state == GameState.GAME_OVER:
                running = self.run_game_over()

        pygame.quit()


# =============================================================================
# EXECUÇÃO
# =============================================================================

if __name__ == "__main__":
    game = SpaceEscape()
    game.run()