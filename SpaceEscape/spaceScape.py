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
    PAUSED = "paused"
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
    enemies: int
    speed_min: int
    speed_max: int
    lives: int

    def scale_for_phase(self, phase: int):
        """Retorna configuração escalada para a fase"""
        return DifficultyConfig(
            enemies=self.enemies + 2 * phase,
            speed_min=self.speed_min + phase,
            speed_max=self.speed_max + phase,
            lives=self.lives
        )


# Dificuldades disponíveis
DIFFICULTIES = {
    "Fácil": DifficultyConfig(enemies=3, speed_min=2, speed_max=4, lives=20),
    "Normal": DifficultyConfig(enemies=6, speed_min=3, speed_max=6, lives=10),
    "Difícil": DifficultyConfig(enemies=10, speed_min=4, speed_max=8, lives=5),
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
    "background_level_1": "Assets/Levels/Level_1/backgroundL1.png",
    "background_level_2": "Assets/Levels/Level_2/backgroundL2.png",
    "background_level_3": "Assets/Levels/Level_3/backgroundL3.png",
    "background_menu": "Assets/Menu/background.png",
    "endgame_bg": "endgame.png",
    "player": "nave1.png",
    "player_up": "nave2.png",
    "sound_point": "classic-game-action-positive-5-224402.mp3",
    "sound_hit": "stab-f-01-brvhrtz-224599.mp3",
    "music": "game-gaming-background-music-385611.mp3",
    "item_collect": "star.png",
    "sound_shoot": "laser.mp3",
    "explosion_sheet": "Assets/Itens/flame.png",
    "shield": "Assets/Itens/shield.png",
    "enemy_level1": "Assets/Enemies/enemy_level1.png",
    "enemy_level2": "Assets/Enemies/enemy_level2.png",
    "enemy_level3": "Assets/Enemies/enemy_level3.png",
    "enemy_level32": "Assets/Enemies/enemy_level32.png",
}

# Dimensões padrão
class Sizes:
    PLAYER_IDLE = (80, 60)
    PLAYER_UP = (200, 140)
    ENEMY = (80, 60)
    ITEM = (32, 32)
    PLAYER_SPEED = 6
    BULLET = (6, 12)
    BULLET_SPEED = -12  # velocidade vertical (negativa = para cima)
    FIRE_COOLDOWN_MS = 200  # intervalo mínimo entre disparos contínuos

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

class Enemy(pygame.sprite.Sprite):
    """Representa uma nave inimiga como um Sprite"""
    def __init__(self, x: int, y: int, speed: int, image: pygame.Surface):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = speed

        self.screen_width = pygame.display.get_surface().get_width()
        self.screen_height = pygame.display.get_surface().get_height()

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > self.screen_height:
            self.randomize_position()

    def randomize_position(self):
        """Reposiciona no topo com posição X aleatória"""
        self.rect.y = random.randint(-100, -40)
        self.rect.x = random.randint(0, self.screen_width - self.rect.width)

class Item(pygame.sprite.Sprite):
    """Representa um item coletável como um Sprite"""
    def __init__(self, x: int, y: int, speed: int, image: pygame.Surface):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = speed
        self.screen_height = pygame.display.get_surface().get_height()

    def update(self):
        """Move para baixo. Se auto-destrói se sair da tela."""
        self.rect.y += self.speed
        if self.rect.top > self.screen_height:
            self.kill()

class Bullet(pygame.sprite.Sprite):
    """Projétil disparado pelo jogador (sobe e destrói naves inimigas)."""
    def __init__(self, x: int, y: int, color: tuple = Colors.YELLOW):
        super().__init__()
        self.image = pygame.Surface((Sizes.BULLET[0], Sizes.BULLET[1]))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.vy = Sizes.BULLET_SPEED

    def update(self):
        """Atualiza posição do projétil. Se auto-destrói se sair do topo."""
        self.rect.y += self.vy
        if self.rect.bottom < 0:
            self.kill()

class Explosion(pygame.sprite.Sprite):
    """Animação de explosão baseada em sprite sheet quando uma nave inimiga é destruída."""
    def __init__(self, center: tuple, frames: List[pygame.Surface], frame_time_ms: int = 40, scale: Optional[tuple] = None, lifetime_ms: int = 500):
        super().__init__()
        self.frames = frames
        if scale is not None and len(frames) > 0:
            self.frames = [pygame.transform.smoothscale(f, scale) for f in frames]
        self.frame_time_ms = frame_time_ms
        self.current = 0
        self.spawn_time = pygame.time.get_ticks()
        self.last_change = self.spawn_time
        self.lifetime_ms = lifetime_ms
        self.image = self.frames[0] if self.frames else pygame.Surface((40, 40), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=center)

    def update(self):
        if not self.frames:
            self.kill()
            return
        now = pygame.time.get_ticks()
        if now - self.spawn_time >= self.lifetime_ms:
            self.kill()
            return
        if now - self.last_change >= self.frame_time_ms:
            self.last_change = now
            self.current += 1
            if self.current >= len(self.frames):
                self.kill()
                return
            center = self.rect.center
            self.image = self.frames[self.current]
            self.rect = self.image.get_rect(center=center)

class Player(pygame.sprite.Sprite):
    """Representa o jogador como um Sprite"""

    def __init__(self, x: int, y: int, idle_img: pygame.Surface,
                 up_img: pygame.Surface):
        super().__init__()
        self.idle_img = idle_img
        self.up_img = up_img
        self.current_img = idle_img

        self.image = self.current_img
        self.rect = self.image.get_rect(center=(x, y))

        self.speed = Sizes.PLAYER_SPEED
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
        self.image = self.current_img

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

def _next_multiple_of_20_above(value: int) -> int:
    rem = value % 20
    return value + (20 - rem) if rem != 0 else value + 20

def _next_multiple_of_33_above(value: int) -> int:
    rem = value % 33
    return value + (33 - rem) if rem != 0 else value + 33


def _normalize_volume_value(value) -> float:
    if isinstance(value, int):
        if 0 <= value <= 100:
            return value / 100.0
        else:
            raise ValueError(f"Volume int fora do intervalo 0..100: {value}")
    try:
        f = float(value)
    except Exception:
        raise ValueError(f"Volume deve ser número (float 0..1 ou int 0..100): {value}")
    if not (0.0 <= f <= 1.0):
        raise ValueError(f"Volume float fora do intervalo 0.0..1.0: {f}")
    return f

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

        # Volumes (defaults)
        self.volumes = {
            "point": 0.3,  # Efeito de ponto
            "hit": 0.3,    # Efeito de dano
            "shoot": 0.2,  # Som do disparo
            "music": 0.3,  # Música de fundo
        }

        # Carrega recursos
        self._load_resources()

        # --- Grupos de Sprites ---
        self.all_sprites = pygame.sprite.Group()       # Grupo para desenhar tudo
        self.enemy_group = pygame.sprite.Group()      # Grupo para colisões com naves
        self.item_group = pygame.sprite.Group()        # Grupo para colisões com itens
        self.shield_group = pygame.sprite.Group()      # Grupo para o item de escudo
        self.bullet_group = pygame.sprite.Group()      # Grupo para colisões com balas
        self.explosion_group = pygame.sprite.Group()   # Grupo para animações de explosão
        self.player_group = pygame.sprite.GroupSingle() # Grupo especial para o jogador

        # Estado do jogo
        self.state = GameState.MENU
        self.difficulty = "Normal"
        self.score = 0
        self.lives = 0
        self.phase = 0
        self.player = None
        self.phase_victory_end = None
        # Progresso por fase
        self.items_collected = 0
        self.boss_defeated = False
        # Itens coletáveis e agendamento de spawn
        self.next_item_spawn_score: Optional[int] = None
        self.next_shield_spawn_score: Optional[int] = None
        # Estado de invulnerabilidade (escudo)
        self.invulnerable_until_ms: int = 0
        # Projéteis
        self.last_shot_ms: int = 0

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

        self.enemy_level1_img = self.resources.load_image(
            "enemy_level1", ASSETS["enemy_level1"], Sizes.ENEMY, Colors.RED
        )
        self.enemy_level2_img = self.resources.load_image(
            "enemy_level2", ASSETS["enemy_level2"], Sizes.ENEMY, Colors.YELLOW
        )
        self.enemy_level3_img = self.resources.load_image(
            "enemy_level3", ASSETS["enemy_level3"], Sizes.ENEMY, Colors.RED
        )
        self.enemy_level32_img = self.resources.load_image(
            "enemy_level32", ASSETS["enemy_level32"], Sizes.ENEMY, Colors.YELLOW
        )

        # Item coletável
        self.item_img = self.resources.load_image(
            "item_collect", ASSETS["item_collect"], Sizes.ITEM, Colors.YELLOW
        )
        # Shield coletável
        self.shield_img = self.resources.load_image(
            "shield", ASSETS["shield"], Sizes.ITEM, Colors.BLUE
        )

        # Sons
        self.sound_point = self.resources.load_sound("point", ASSETS["sound_point"]) 
        self.sound_hit = self.resources.load_sound("hit", ASSETS["sound_hit"]) 
        self.sound_shoot = self.resources.load_sound("shoot", ASSETS["sound_shoot"]) 
        self.resources.load_music(ASSETS["music"]) 

        self.explosion_frames: List[pygame.Surface] = []
        try:
            sheet_path = self.resources._resolve_path(ASSETS["explosion_sheet"])
            if os.path.exists(sheet_path):
                sheet = pygame.image.load(sheet_path).convert_alpha()
                sheet_w, sheet_h = sheet.get_width(), sheet.get_height()
                cols = 8
                rows = 8
                cell_w = sheet_w // cols
                cell_h = sheet_h // rows
                for r in range(rows):
                    for c in range(cols):
                        rect = pygame.Rect(c * cell_w, r * cell_h, cell_w, cell_h)
                        frame = sheet.subsurface(rect).copy()
                        self.explosion_frames.append(frame)
        except Exception as e:
            print(f"Aviso: falha ao carregar frames de explosão: {e}")

        try:
            self._apply_volumes()
        except Exception as e:
            print(f"Aviso: falha ao aplicar volumes: {e}")

    def _apply_volumes(self):
        # Sons (SFX)
        if hasattr(self, "sound_point") and self.sound_point:
            try:
                self.sound_point.set_volume(self.volumes.get("point"))
            except Exception:
                pass
        if hasattr(self, "sound_hit") and self.sound_hit:
            try:
                self.sound_hit.set_volume(self.volumes.get("hit"))
            except Exception:
                pass
        if hasattr(self, "sound_shoot") and self.sound_shoot:
            try:
                self.sound_shoot.set_volume(self.volumes.get("shoot"))
            except Exception:
                pass
        # Música
        try:
            pygame.mixer.music.set_volume(self.volumes.get("music"))
        except Exception:
            pass

    def set_volume(self, name: str, value):
        allowed = {"point", "hit", "shoot", "music"}
        if name not in allowed:
            raise ValueError(f"Nome de volume inválido: {name}. Válidos: {sorted(allowed)}")
        v = _normalize_volume_value(value)
        self.volumes[name] = v
        self._apply_volumes()

    def _get_enemy_images_for_phase(self) -> List[pygame.Surface]:
        """Retorna a lista de sprites de inimigos conforme a fase atual.
        Fase 1 (phase==0): enemy_level1
        Fase 2 (phase==1): enemy_level2
        Fase 3+ (phase>=2): inimigos aleatórios entre enemy_level3 e enemy_level32
        """
        if self.phase == 0:
            return [self.enemy_level1_img]
        elif self.phase == 1:
            return [self.enemy_level2_img]
        else:
            return [self.enemy_level3_img, self.enemy_level32_img]

    def _create_enemies(self, config: DifficultyConfig):
        """Cria naves inimigas e os ADICIONA AOS GRUPOS"""
        for _ in range(config.enemies):
            x = random.randint(0, self.config.WIDTH - Sizes.ENEMY[0])
            y = random.randint(-500, -40)
            speed = random.randint(config.speed_min, config.speed_max)
            enemy_imgs = self._get_enemy_images_for_phase()
            img = random.choice(enemy_imgs)

            enemy = Enemy(x, y, speed, img)

            # Adiciona aos grupos
            self.all_sprites.add(enemy)
            self.enemy_group.add(enemy)

    def _clear_game_groups(self):
        """Limpa todos os sprites do jogo (exceto o jogador)."""
        self.enemy_group.empty()
        self.item_group.empty()
        self.shield_group.empty()
        self.bullet_group.empty()
        self.explosion_group.empty()
        self.all_sprites.empty()
        if self.player:
            self.all_sprites.add(self.player)

    def new_game(self):
        """Inicia um novo jogo"""
        diff_config = DIFFICULTIES[self.difficulty]
        self.score = 0
        self.lives = diff_config.lives
        self.phase = 0
        self.items_collected = 0
        self.boss_defeated = False
        self.next_item_spawn_score = None
        self.next_shield_spawn_score = None
        self.invulnerable_until_ms = 0
        self.last_shot_ms = 0

        # Cria o jogador (se ainda não existir) ou reposiciona
        if not self.player:
            self.player = Player(
                self.config.WIDTH // 2, self.config.HEIGHT - 60,
                self.player_idle, self.player_up
            )
        else:
            self.player.reset_position(self.config.WIDTH // 2, self.config.HEIGHT - 60)

        # Adiciona o jogador aos grupos
        self.player_group.add(self.player)
        self.all_sprites.add(self.player)

        # Limpa sprites antigos
        self.enemy_group.empty()
        self.item_group.empty()
        self.shield_group.empty()
        self.bullet_group.empty()
        self.explosion_group.empty()

        # Cria novas naves inimigas
        self._create_enemies(diff_config.scale_for_phase(0))

        self._reset_item_spawn_schedule()
        self._reset_shield_spawn_schedule()
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
        self.items_collected = data.get("items_collected", 0)
        self.boss_defeated = data.get("boss_defeated", False)

        self.next_item_spawn_score = None
        self.next_shield_spawn_score = None
        self.invulnerable_until_ms = 0
        self.last_shot_ms = 0

        # Cria ou reposiciona o jogador
        if not self.player:
            self.player = Player(
                self.config.WIDTH // 2, self.config.HEIGHT - 60,
                self.player_idle, self.player_up
            )

        player_data = data.get("player", {})
        if player_data:
            self.player.rect.x = player_data.get("x", self.player.rect.x)
            self.player.rect.y = player_data.get("y", self.player.rect.y)

        self.player_group.add(self.player)
        self.all_sprites.add(self.player)

        self.enemy_group.empty()
        self.item_group.empty()
        self.shield_group.empty()
        self.bullet_group.empty()
        self.explosion_group.empty()

        diff_config = DIFFICULTIES[self.difficulty]
        self._create_enemies(diff_config.scale_for_phase(self.phase))

        self._reset_item_spawn_schedule()
        self._reset_shield_spawn_schedule()
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

    def _reset_item_spawn_schedule(self):
        """Inicializa o próximo marco de pontuação para spawn de item."""
        if self._is_item_enabled():
            self.next_item_spawn_score = _next_multiple_of_20_above(self.score)
        else:
            self.next_item_spawn_score = None

    def _reset_shield_spawn_schedule(self):
        """Inicializa o próximo marco de pontuação para spawn de shield (a cada 33 pontos, sempre ativo)."""
        self.next_shield_spawn_score = _next_multiple_of_33_above(self.score)

    def _spawn_item(self):
        """Cria um item e o adiciona aos grupos."""
        if len(self.item_group) > 0:
            return

        x = random.randint(0, self.config.WIDTH - Sizes.ITEM[0])
        y = random.randint(-200, -40)
        speed = self._item_speed_for_phase()

        item = Item(x, y, speed, self.item_img)
        self.all_sprites.add(item)
        self.item_group.add(item)

    def _spawn_shield(self):
        """Cria um shield e o adiciona aos grupos."""
        if len(self.shield_group) > 0:
            return
        x = random.randint(0, self.config.WIDTH - Sizes.ITEM[0])
        y = random.randint(-200, -40)
        speed = self._item_speed_for_phase() if hasattr(self, '_item_speed_for_phase') else 7
        shield = Item(x, y, speed, self.shield_img)
        self.all_sprites.add(shield)
        self.shield_group.add(shield)

    def _handle_enemy_collision(self):
        """Processa colisão com naves inimigas"""
        self.lives -= 1 # Dano de vida

        if 0 < self.score < 50:
            self.score = max(0, self.score - 2)
        elif self.score >= 50:
            self.score = max(0, self.score - 5)

        if self.sound_hit:
            self.sound_hit.play()

    def _advance_phase(self):
        """Avança para a próxima fase"""
        self.phase += 1
        self.items_collected = 0
        self.boss_defeated = False

        # Limpa todos os sprites (exceto o jogador)
        self.enemy_group.empty()
        self.item_group.empty()
        self.shield_group.empty()
        self.bullet_group.empty()
        self.explosion_group.empty()

        self.all_sprites.empty()
        self.all_sprites.add(self.player)

        self._reset_item_spawn_schedule()
        self._reset_shield_spawn_schedule()
        self.invulnerable_until_ms = 0
        self.last_shot_ms = 0

        self.player.reset_position(self.config.WIDTH // 2, self.config.HEIGHT - 60)
        diff_config = DIFFICULTIES[self.difficulty]
        self._create_enemies(diff_config.scale_for_phase(self.phase))

        self.state = GameState.PLAYING
        self.phase_victory_end = None

    def _try_shoot(self, keys):
        """Dispara projétil se Espaço estiver pressionado e cooldown permitir."""
        if not self.player:
            return
        if not keys[pygame.K_SPACE]:
            return
        now = pygame.time.get_ticks()
        if now - self.last_shot_ms < Sizes.FIRE_COOLDOWN_MS:
            return

        bx = self.player.rect.centerx - Sizes.BULLET[0] // 2
        by = self.player.rect.top - Sizes.BULLET[1]

        bullet = Bullet(bx, by)

        self.all_sprites.add(bullet)
        self.bullet_group.add(bullet)

        self.last_shot_ms = now

        if hasattr(self, "sound_shoot") and self.sound_shoot:
            try:
                self.sound_shoot.play()
            except Exception as e:
                print(f"Aviso: falha ao tocar som de tiro: {e}")

    def update_gameplay(self):
        """Atualiza lógica do gameplay usando grupos de sprites"""
        keys = pygame.key.get_pressed()

        self.player.update(keys, self.config.WIDTH, self.config.HEIGHT)

        self._try_shoot(keys)

        # Atualiza todos os outros sprites
        self.enemy_group.update()
        self.item_group.update()
        self.shield_group.update()
        self.bullet_group.update()
        self.explosion_group.update()

        diff_config = DIFFICULTIES[self.difficulty].scale_for_phase(self.phase)

        # --- 2. Verificação de Colisões ---

        # (False = Inimigo não é destruído na colisão, nós o reposicionamos)
        hits = pygame.sprite.spritecollide(self.player, self.enemy_group, False)
        if hits:
            now = pygame.time.get_ticks()
            inv_active = now < self.invulnerable_until_ms
            for enemy_hit in hits:
                if not inv_active:
                    self._handle_enemy_collision()  # Lógica de dano e penalidade
                # Sempre reposiciona a nave inimiga
                enemy_hit.randomize_position()
                enemy_hit.speed = random.randint(diff_config.speed_min, diff_config.speed_max)

                if self.lives <= 0 and not inv_active:
                    self.state = GameState.GAME_OVER
                    return

        # Colisão Projétil vs Naves inimigas
        # (True, True = destrói ambos, bala e nave inimiga)
        hits = pygame.sprite.groupcollide(self.bullet_group, self.enemy_group, True, True)
        if hits:
            for enemy_list in hits.values():
                for enemy in enemy_list:
                    if hasattr(self, "explosion_frames") and self.explosion_frames:
                        exp = Explosion(enemy.rect.center, self.explosion_frames, frame_time_ms=40, scale=(80, 80))
                        self.explosion_group.add(exp)
                    # Pontuação por destruir com tiro
                    self.score += 1
                    if self.sound_point:
                        self.sound_point.play()

                    # Cria um nova nave inimiga para substituir o destruída
                    x = random.randint(0, self.config.WIDTH - Sizes.ENEMY[0])
                    y = random.randint(-100, -40)
                    speed = random.randint(diff_config.speed_min, diff_config.speed_max)
                    enemy_imgs = self._get_enemy_images_for_phase()
                    img = random.choice(enemy_imgs)
                    new_enemy = Enemy(x, y, speed, img)
                    self.all_sprites.add(new_enemy)
                    self.enemy_group.add(new_enemy)

        # Colisão Jogador vs Itens
        # (True = destrói o item ao coletar)
        item_hits = pygame.sprite.spritecollide(self.player, self.item_group, True)
        if item_hits:
            self.items_collected += len(item_hits)
            if self.sound_point:
                self.sound_point.play()

        # Colisão Jogador vs Shield
        shield_hits = pygame.sprite.spritecollide(self.player, self.shield_group, True)
        if shield_hits:
            # 5 segundos de invulnerabilidade
            self.invulnerable_until_ms = pygame.time.get_ticks() + 5000
            if self.sound_point:
                self.sound_point.play()

        # --- 3. Lógica de Jogo (Spawns, Vitória) ---

        # (Os loops manuais de update e colisão foram todos removidos)

        # Spawns de itens por pontuação (Fase 2 e 3)
        if self._is_item_enabled():
            if self.next_item_spawn_score is None:
                self._reset_item_spawn_schedule()

            if self.next_item_spawn_score is not None and self.score >= self.next_item_spawn_score:
                if len(self.item_group) == 0:  # Checa se não há itens na tela
                    self._spawn_item()
                self.next_item_spawn_score += 20

        # Spawn de shield a cada 33 pontos (sempre ativo, independente da fase)
        if self.next_shield_spawn_score is None:
            self._reset_shield_spawn_schedule()
        if self.next_shield_spawn_score is not None and self.score >= self.next_shield_spawn_score:
            if len(self.shield_group) == 0:  # Checa se não há shield na tela
                self._spawn_shield()
            self.next_shield_spawn_score += 33

        # Verifica vitória da fase
        if self._has_phase_victory():
            self.state = GameState.PHASE_VICTORY
            self.phase_victory_end = pygame.time.get_ticks() + self.config.PHASE_VICTORY_DURATION

    def draw_gameplay(self):
        """Desenha o gameplay"""
        self.screen.blit(self._get_bg_for_current_phase(), (0, 0))

        # --- Desenha TODOS os sprites de uma vez ---
        self.all_sprites.draw(self.screen)
        # Explosões também são desenhadas (caso não estejam em all_sprites)
        self.explosion_group.draw(self.screen)

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

    def run_pause(self) -> bool:
        """Loop de pausa. Retorna False se deve encerrar o jogo; True caso contrário."""
        options = ["Continuar", "Salvar e voltar ao menu", "Salvar e fechar o jogo"]
        selected = 0

        paused = True
        while paused:
            self.draw_gameplay()

            overlay = pygame.Surface((self.config.WIDTH, self.config.HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))

            title = self.font_large.render("JOGO PAUSADO", True, Colors.YELLOW)
            self.screen.blit(title, (self.config.WIDTH // 2 - title.get_width() // 2, 120))

            for i, opt in enumerate(options):
                color = Colors.YELLOW if i == selected else Colors.WHITE
                label = self.font_small.render(opt, True, color)
                self.screen.blit(label, (self.config.WIDTH // 2 - label.get_width() // 2, 240 + i * 60))

            hint = self.font_tiny.render("ESC para continuar • ENTER para selecionar", True, Colors.WHITE)
            self.screen.blit(hint, (self.config.WIDTH // 2 - hint.get_width() // 2, self.config.HEIGHT - 80))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        selected = (selected + 1) % len(options)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        selected = (selected - 1) % len(options)
                    elif event.key == pygame.K_ESCAPE:
                        # Continuar
                        self.state = GameState.PLAYING
                        paused = False
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        choice = options[selected]
                        if choice == "Continuar":
                            self.state = GameState.PLAYING
                            paused = False
                        elif choice == "Salvar e voltar ao menu":
                            # Salva progresso atual e volta ao menu principal
                            if self.player is not None:
                                self.save_manager.save(
                                    self.difficulty, self.score, self.lives,
                                    self.phase, self.player.rect.center,
                                    items_collected=self.items_collected,
                                    boss_defeated=self.boss_defeated
                                )
                            self.state = GameState.MENU
                            paused = False
                        elif choice == "Salvar e fechar o jogo":
                            # Salva progresso atual e encerra aplicação
                            if self.player is not None:
                                self.save_manager.save(
                                    self.difficulty, self.score, self.lives,
                                    self.phase, self.player.rect.center,
                                    items_collected=self.items_collected,
                                    boss_defeated=self.boss_defeated
                                )
                            return False

            self.clock.tick(self.config.FPS)

        return True

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

            # Highscore
            high = self.save_manager.get_highscore()
            hs_label = self.font_tiny.render(f"Maior pontuação: {high}", True, Colors.WHITE)
            self.screen.blit(hs_label, (self.config.WIDTH // 2 - hs_label.get_width() // 2, 150))

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
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        # Pausar jogo
                        self.state = GameState.PAUSED
                    elif event.type == pygame.MOUSEMOTION:
                        self.player.move_to_position(event.pos[0], event.pos[1], self.config.WIDTH, self.config.HEIGHT)
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        self.player.move_to_position(event.pos[0], event.pos[1], self.config.WIDTH, self.config.HEIGHT)

                if running and self.state == GameState.PLAYING:
                    self.update_gameplay()
                    self.draw_gameplay()
                    pygame.display.flip()
                    self.clock.tick(self.config.FPS)

            elif self.state == GameState.PAUSED:
                running = self.run_pause()

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