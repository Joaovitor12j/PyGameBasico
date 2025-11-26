import pygame
import random
import os
import json
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional

CURRENT_GAME = None

# =============================================================================
# CONSTANTES
# =============================================================================

class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    PHASE_VICTORY = "phase_victory"
    GAME_OVER = "game_over"
    VICTORY = "victory"

@dataclass
class GameConfig:
    """Configurações gerais do jogo"""
    WIDTH: int = 800
    HEIGHT: int = 600
    FPS: int = 60
    TITLE: str = "🚀 Space Escape"
    SAVE_FILE: str = "savegame.json"
    PHASE_TARGET_BASE: int = 100
    PHASE_VICTORY_DURATION: int = 2000  # ms

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
    "endgame_bg": "Assets/endgame.png",
    "player": "Assets/Player/nave1.png",
    "player_up": "Assets/Player/nave2.png",
    "sound_point": "Assets/Sounds/sound_point.mp3",
    "sound_hit": "Assets/Sounds/sound_hit.mp3",
    "music": "Assets/Sounds/music.mp3",
    "item_collect": "Assets/Itens/star.png",
    "sound_shoot": "Assets/Sounds/laser.mp3",
    "explosion_sheet": "Assets/Itens/flame.png",
    "shield": "Assets/Itens/shield.png",
    "enemy_level1": "Assets/Enemies/enemy_level1.png",
    "enemy_level2": "Assets/Enemies/enemy_level2.png",
    "enemy_level3": "Assets/Enemies/enemy_level3.png",
    "enemy_level3_2": "Assets/Enemies/enemy_level3_2.png",
    "boss_sleep": "Assets/Boss/golem_boss_sleep.png",
    "boss_normal": "Assets/Boss/golem_boss.png",
    "boss_rage": "Assets/Boss/golem_boss_rage.png",
    "low_lifes": "Assets/Sounds/low_lifes.mp3",
    "boss_final": "Assets/Sounds/boss_final.mp3",
    "collect_star": "Assets/Sounds/collect_star.mp3",
    "gameover": "Assets/Sounds/gameover.mp3",
    "load_levels": "Assets/Sounds/load_levels.mp3",
    "boss_explosion": "Assets/Sounds/boss_explosion.mp3",
    "pause_game": "Assets/Sounds/pause_game.mp3",
    "space_bridge": "Assets/Sounds/space_bridge.mp3",
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
    BOSS = (220, 160)

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
        self.rect.y = random.randint(-100, -40)
        x_min = 0
        x_max = self.screen_width - self.rect.width
        game_current = globals().get('CURRENT_GAME', None)
        if game_current and getattr(game_current, 'boss_spawned', False) and getattr(game_current, 'boss', None) and not getattr(game_current, 'boss_defeated', False):
            forbid = game_current.get_boss_forbidden_x_range(self.rect.width)
            if forbid is not None:
                lx, rx = forbid
                left_end = max(x_min, lx - self.rect.width)
                right_start = min(x_max, rx + 1)
                intervals = []
                if left_end > x_min:
                    intervals.append((x_min, left_end))
                if right_start < x_max:
                    intervals.append((right_start, x_max))
                if intervals:
                    seg = random.choice(intervals)
                    self.rect.x = random.randint(seg[0], max(seg[0], seg[1]))
                    return
        self.rect.x = random.randint(x_min, x_max)

class Item(pygame.sprite.Sprite):
    """Representa um item coletável como um Sprite"""
    def __init__(self, x: int, y: int, speed: int, image: pygame.Surface):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = speed
        self.screen_height = pygame.display.get_surface().get_height()

    def update(self):
        """Move o item para baixo; remove quando sai da tela."""
        self.rect.y += self.speed
        if self.rect.top > self.screen_height:
            self.kill()

class Boss(pygame.sprite.Sprite):
    """Chefe final que aparece na fase 3+ quando objetivos estão cumpridos."""
    def __init__(self, image: pygame.Surface, screen_width: int):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.midtop = (screen_width // 2, 10)

    def update(self):
        return

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

class ShieldAura(pygame.sprite.Sprite):
    """Efeito visual de partículas orbitando a nave enquanto o escudo está ativo."""
    def __init__(self, player: pygame.sprite.Sprite, radius: Optional[int] = None, particles: int = 12,
                 color_main: tuple = Colors.BLUE, color_glow: tuple = (120, 180, 255)):
        super().__init__()
        self.player = player
        pr = player.rect
        base = max(pr.width, pr.height)
        self.radius = int((radius if radius is not None else base * 0.65))
        size = self.radius * 2 + 10
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=player.rect.center)
        self.particles = max(6, particles)
        self.angles = [i * (360.0 / self.particles) for i in range(self.particles)]
        self.angular_speed = 120.0  # graus por segundo
        self.last_update_ms = pygame.time.get_ticks()
        self.color_main = color_main
        self.color_glow = color_glow
        self.particle_radius = max(2, base // 20)
        self.glow_radius = self.particle_radius + 2
        self._redraw()

    def _redraw(self):
        self.image.fill((0, 0, 0, 0))
        cx = self.image.get_width() // 2
        cy = self.image.get_height() // 2
        for ang in self.angles:
            rad = ang * 3.14159265 / 180.0
            px = int(cx + self.radius * math.cos(rad))
            py = int(cy + self.radius * math.sin(rad))
            pygame.draw.circle(self.image, (*self.color_glow, 90), (px, py), self.glow_radius)
            pygame.draw.circle(self.image, self.color_main, (px, py), self.particle_radius)

    def update(self):
        if not hasattr(self.player, 'rect'):
            self.kill()
            return
        self.rect.center = self.player.rect.center
        now = pygame.time.get_ticks()
        dt = max(0, now - self.last_update_ms) / 1000.0
        self.last_update_ms = now
        delta_deg = self.angular_speed * dt
        self.angles = [(a + delta_deg) % 360.0 for a in self.angles]
        self._redraw()

class Player(pygame.sprite.Sprite):
    """Representa o jogador como um Sprite"""

    def __init__(self, x: int, y: int, idle_img: pygame.Surface,
                 up_img: pygame.Surface, control_scheme: str = "both"):
        super().__init__()
        self.idle_img = idle_img
        self.up_img = up_img
        self.current_img = idle_img
        self.control_scheme = control_scheme

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
        use_arrows = self.control_scheme in ("both", "arrows")
        use_wasd = self.control_scheme in ("both", "wasd")

        if ((use_arrows and keys[pygame.K_LEFT]) or (use_wasd and keys[pygame.K_a])) and self.rect.left > 0:
            self.rect.x -= self.speed
        if ((use_arrows and keys[pygame.K_RIGHT]) or (use_wasd and keys[pygame.K_d])) and self.rect.right < screen_width:
            self.rect.x += self.speed

        self.moving_up = False
        if ((use_arrows and keys[pygame.K_UP]) or (use_wasd and keys[pygame.K_w])) and self.rect.top > 0:
            self.rect.y -= self.speed
            self.moving_up = True
        if ((use_arrows and keys[pygame.K_DOWN]) or (use_wasd and keys[pygame.K_s])) and self.rect.bottom < screen_height:
            self.rect.y += self.speed

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
                "player": {"x": player_pos[0], "y": player_pos[1]} if player_pos is not None else None,
                "items_collected": items_collected,
                "boss_defeated": boss_defeated,
                "highscore": highscore,
            }
            try:
                if 'CURRENT_GAME' in globals() and CURRENT_GAME is not None:
                    data["volumes"] = dict(CURRENT_GAME.volumes)
                    data["sound_enabled"] = dict(CURRENT_GAME.sound_enabled)
            except Exception as e:
                print(f"Aviso: falha ao salvar configurações de som: {e}")
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

class SpaceAtaque:
    """Classe principal do jogo"""
    def __init__(self):
        pygame.init()
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.set_num_channels(32)
        except Exception:
            pass

        self.config = GameConfig()
        self.screen = pygame.display.set_mode((self.config.WIDTH, self.config.HEIGHT))
        pygame.display.set_caption(self.config.TITLE)
        self.clock = pygame.time.Clock()

        global CURRENT_GAME
        CURRENT_GAME = self

        asset_dir = os.path.dirname(os.path.abspath(__file__))
        self.resources = ResourceManager(asset_dir)
        self.save_manager = SaveManager(os.path.join(asset_dir, self.config.SAVE_FILE))

        self.volumes = {
            "point": 0.3,  # Efeito de ponto
            "hit": 0.3,    # Efeito de dano
            "shoot": 0.2,  # Som do disparo
            "music": 0.3,  # Música de fundo
        }

        self.sound_enabled = {
            "point": True,
            "hit": True,
            "shoot": True,
            "music": True,
        }

        try:
            saved = self.save_manager.load()
            if saved:
                if isinstance(saved.get("volumes"), dict):
                    for k, v in saved["volumes"].items():
                        if k in self.volumes:
                            try:
                                self.volumes[k] = _normalize_volume_value(v)
                            except Exception:
                                pass
                if isinstance(saved.get("sound_enabled"), dict):
                    for k, v in saved["sound_enabled"].items():
                        if k in self.sound_enabled and isinstance(v, bool):
                            self.sound_enabled[k] = v
        except Exception as e:
            print(f"Aviso: falha ao carregar configurações de som do save: {e}")

        self._load_resources()

        # --- Grupos de Sprites ---
        self.all_sprites = pygame.sprite.Group()       # Grupo para desenhar tudo
        self.enemy_group = pygame.sprite.Group()      # Grupo para colisões com naves
        self.item_group = pygame.sprite.Group()        # Grupo para colisões com itens
        self.shield_group = pygame.sprite.Group()      # Grupo para o item de escudo
        self.bullet_group = pygame.sprite.Group()      # Grupo para colisões com balas
        self.explosion_group = pygame.sprite.Group()   # Grupo para animações de explosão
        self.player_group = pygame.sprite.GroupSingle() # Grupo especial para o jogador
        self.boss_group = pygame.sprite.GroupSingle()   # Grupo para o chefe
        self.shield_aura_group = pygame.sprite.GroupSingle()  # Efeito visual do escudo

        # Estado do jogo
        self.state = GameState.MENU
        
        # Flags/estado para sons dinâmicos
        self._low_lifes_playing = False
        self._phase_wait_snd_playing = False
        self._pause_snd_playing = False
        self._space_bridge_playing = False
        self._boss_final_end_ms = None
        # Canais para sons em loop/temporizados
        self._chan_low_lifes = None
        self._chan_phase_wait = None
        self._chan_pause = None
        self._chan_space_bridge = None
        self._chan_boss_final = None

        self._sfx_duck = 1.0
        self._sfx_boost = {
            "low_lifes": 6.0,
            "space_bridge": 5.8,
            "load_levels": 6.0,
            "pause_game": 4.0,
            "boss_final": 6.0,
            "boss_explosion": 7.0,
            "gameover": 3.15,
            "collect_star": 5.2,
        }
        self.difficulty = "Normal"
        self.score = 0
        self.lives = 0
        self.phase = 0
        self.player = None
        self.player2 = None
        self.multiplayer = False
        self.phase_victory_end = None
        self.items_collected = 0
        self.boss_defeated = False
        self.boss = None
        self.boss_hp: float = 0.0
        self.boss_spawned: bool = False
        self.next_item_spawn_score: Optional[int] = None
        self.next_shield_spawn_score: Optional[int] = None
        self.invulnerable_until_ms: int = 0
        self.last_shot_ms: int = 0
        self.last_shot_ms_p1: int = 0
        self.last_shot_ms_p2: int = 0

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
        self.enemy_level3_2_img = self.resources.load_image(
            "enemy_level3_2", ASSETS["enemy_level3_2"], Sizes.ENEMY, Colors.YELLOW
        )

        # Item coletável
        self.item_img = self.resources.load_image(
            "item_collect", ASSETS["item_collect"], Sizes.ITEM, Colors.YELLOW
        )
        # Shield coletável
        self.shield_img = self.resources.load_image(
            "shield", ASSETS["shield"], Sizes.ITEM, Colors.BLUE
        )

        # Boss images
        self.boss_img_sleep = self.resources.load_image(
            "boss_sleep", ASSETS["boss_sleep"], Sizes.BOSS, Colors.RED
        )
        self.boss_img_normal = self.resources.load_image(
            "boss_normal", ASSETS["boss_normal"], Sizes.BOSS, Colors.RED
        )
        self.boss_img_rage = self.resources.load_image(
            "boss_rage", ASSETS["boss_rage"], Sizes.BOSS, Colors.RED
        )

        # Sons
        self.sound_point = self.resources.load_sound("point", ASSETS["sound_point"]) 
        self.sound_hit = self.resources.load_sound("hit", ASSETS["sound_hit"]) 
        self.sound_shoot = self.resources.load_sound("shoot", ASSETS["sound_shoot"]) 
        # Novos sons
        self.sound_low_lifes = self.resources.load_sound("low_lifes", ASSETS["low_lifes"]) 
        self.sound_boss_final = self.resources.load_sound("boss_final", ASSETS["boss_final"]) 
        self.sound_collect_star = self.resources.load_sound("collect_star", ASSETS["collect_star"]) 
        self.sound_gameover = self.resources.load_sound("gameover", ASSETS["gameover"]) 
        self.sound_load_levels = self.resources.load_sound("load_levels", ASSETS["load_levels"]) 
        self.sound_boss_explosion = self.resources.load_sound("boss_explosion", ASSETS["boss_explosion"]) 
        self.sound_pause_game = self.resources.load_sound("pause_game", ASSETS["pause_game"]) 
        self.sound_space_bridge = self.resources.load_sound("space_bridge", ASSETS["space_bridge"]) 
        
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

        self.enemy_3_2_explosion_frames: List[pygame.Surface] = []
        try:
            dir_path = self.resources._resolve_path("Assets/Enemies/enemy_3_2_explosion")
            if os.path.isdir(dir_path):
                for fname in sorted(os.listdir(dir_path)):
                    if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                        fpath = os.path.join(dir_path, fname)
                        try:
                            img = pygame.image.load(fpath).convert_alpha()
                            self.enemy_3_2_explosion_frames.append(img)
                        except Exception as e:
                            print(f"Aviso: falha ao carregar frame enemy_level3_2 '{fname}': {e}")
        except Exception as e:
            print(f"Aviso: falha ao listar frames enemy_3_2_Explosion: {e}")

        self.enemy_1_explosion_frames: List[pygame.Surface] = []
        try:
            dir_path = self.resources._resolve_path("Assets/Enemies/enemy_1_explosion")
            if os.path.isdir(dir_path):
                for fname in sorted(os.listdir(dir_path)):
                    if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                        fpath = os.path.join(dir_path, fname)
                        try:
                            img = pygame.image.load(fpath).convert_alpha()
                            self.enemy_1_explosion_frames.append(img)
                        except Exception as e:
                            print(f"Aviso: falha ao carregar frame enemy_1 '{fname}': {e}")
        except Exception as e:
            print(f"Aviso: falha ao listar frames enemy_1_Explosion: {e}")

        self.enemy_2_explosion_frames: List[pygame.Surface] = []
        try:
            dir_path = self.resources._resolve_path("Assets/Enemies/enemy_2_explosion")
            if os.path.isdir(dir_path):
                for fname in sorted(os.listdir(dir_path)):
                    if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                        fpath = os.path.join(dir_path, fname)
                        try:
                            img = pygame.image.load(fpath).convert_alpha()
                            self.enemy_2_explosion_frames.append(img)
                        except Exception as e:
                            print(f"Aviso: falha ao carregar frame enemy_2 '{fname}': {e}")
        except Exception as e:
            print(f"Aviso: falha ao listar frames enemy_2_Explosion: {e}")

    def _apply_volumes(self):
        point_vol = self.volumes.get("point", 0.0) if self.sound_enabled.get("point", True) else 0.0
        hit_vol = self.volumes.get("hit", 0.0) if self.sound_enabled.get("hit", True) else 0.0
        shoot_vol = self.volumes.get("shoot", 0.0) if self.sound_enabled.get("shoot", True) else 0.0
        music_base_vol = self.volumes.get("music", 0.0) if self.sound_enabled.get("music", True) else 0.0
        try:
            sfx_candidates = []
            if self.sound_enabled.get("point", True):
                sfx_candidates.append(point_vol)
            if self.sound_enabled.get("hit", True):
                sfx_candidates.append(hit_vol)
            if self.sound_enabled.get("shoot", True):
                sfx_candidates.append(shoot_vol)
            sfx_vol = max(sfx_candidates) if sfx_candidates else 0.0
        except Exception:
            sfx_vol = point_vol
        try:
            sfx_vol_any = max(
                float(self.volumes.get("point", 0.0)),
                float(self.volumes.get("hit", 0.0)),
                float(self.volumes.get("shoot", 0.0)),
            )
        except Exception:
            sfx_vol_any = sfx_vol

        def _clamp01(v: float) -> float:
            try:
                return max(0.0, min(1.0, float(v)))
            except Exception:
                return 0.0

        def _apply_sound_with_boost(attr_name: str, base_vol: float, apply_duck: bool = True, chan_attr: str = None):
            try:
                snd = getattr(self, attr_name, None)
                if not snd:
                    return
                key = attr_name.replace("sound_", "")
                boost = 1.0
                try:
                    boost = self._sfx_boost.get(key, 1.0)
                except Exception:
                    boost = 1.0
                duck = self._sfx_duck if apply_duck else 1.0
                vol = _clamp01(base_vol * boost * duck)
                snd.set_volume(vol)
                if chan_attr:
                    ch = getattr(self, chan_attr, None)
                    if ch:
                        try:
                            ch.set_volume(vol)
                        except Exception:
                            pass
            except Exception:
                pass

        if hasattr(self, "sound_point") and self.sound_point:
            try:
                self.sound_point.set_volume(point_vol)
            except Exception:
                pass
        if hasattr(self, "sound_hit") and self.sound_hit:
            try:
                self.sound_hit.set_volume(hit_vol)
            except Exception:
                pass
        if hasattr(self, "sound_shoot") and self.sound_shoot:
            try:
                self.sound_shoot.set_volume(shoot_vol)
            except Exception:
                pass

        _apply_sound_with_boost("sound_low_lifes", sfx_vol, apply_duck=True, chan_attr="_chan_low_lifes")
        boss_base = sfx_vol if sfx_vol > 0.0 else sfx_vol_any
        _apply_sound_with_boost("sound_boss_final", boss_base, apply_duck=True, chan_attr="_chan_boss_final")
        collect_base = sfx_vol if sfx_vol > 0.0 else sfx_vol_any
        _apply_sound_with_boost("sound_collect_star", collect_base, apply_duck=True)
        _apply_sound_with_boost("sound_gameover", sfx_vol, apply_duck=True)
        _apply_sound_with_boost("sound_boss_explosion", boss_base, apply_duck=True)
        _apply_sound_with_boost("sound_pause_game", sfx_vol, apply_duck=True, chan_attr="_chan_pause")
        _apply_sound_with_boost("sound_space_bridge", sfx_vol, apply_duck=True, chan_attr="_chan_space_bridge")
        load_base = sfx_vol if sfx_vol > 0.0 else sfx_vol_any
        _apply_sound_with_boost("sound_load_levels", load_base, apply_duck=False, chan_attr="_chan_phase_wait")

        try:
            music_vol = _clamp01(music_base_vol * (self._sfx_duck if self.sound_enabled.get("music", True) else 1.0))
            pygame.mixer.music.set_volume(music_vol)
            if not self.sound_enabled.get("music", True):
                try:
                    pygame.mixer.music.pause()
                except Exception:
                    pass
            else:
                try:
                    pygame.mixer.music.unpause()
                except Exception:
                    pass
        except Exception:
            pass

    def _is_sfx_enabled(self) -> bool:
        try:
            return any(self.sound_enabled.get(k, True) for k in ("point", "hit", "shoot"))
        except Exception:
            return True

    def _start_loop(self, sound_attr: str, flag_attr: str, chan_attr: str, *, bypass_flags: bool = False, use_any_base: bool = False):
        try:
            if not getattr(self, flag_attr, False):
                snd = getattr(self, sound_attr, None)
                if snd and (bypass_flags or self._is_sfx_enabled()):
                    ch = snd.play(-1)
                    setattr(self, flag_attr, True)
                    setattr(self, chan_attr, ch)
                    try:
                        if use_any_base:
                            point_vol = float(self.volumes.get("point", 0.0))
                            hit_vol = float(self.volumes.get("hit", 0.0))
                            shoot_vol = float(self.volumes.get("shoot", 0.0))
                        else:
                            point_vol = self.volumes.get("point", 0.0) if self.sound_enabled.get("point", True) else 0.0
                            hit_vol = self.volumes.get("hit", 0.0) if self.sound_enabled.get("hit", True) else 0.0
                            shoot_vol = self.volumes.get("shoot", 0.0) if self.sound_enabled.get("shoot", True) else 0.0
                        sfx_base = max([v for v in (point_vol, hit_vol, shoot_vol)]) if (use_any_base or any(
                            [self.sound_enabled.get(k, True) for k in ("point", "hit", "shoot")]
                        )) else 0.0
                        key = sound_attr.replace("sound_", "")
                        try:
                            boost = self._sfx_boost.get(key, 1.0)
                        except Exception:
                            boost = 1.0
                        apply_duck = (sound_attr != "sound_load_levels")
                        duck = self._sfx_duck if apply_duck else 1.0
                        vol = max(0.0, min(1.0, float(sfx_base) * float(boost) * float(duck)))
                        if ch:
                            ch.set_volume(vol)
                    except Exception:
                        pass
        except Exception:
            pass

    def _stop_loop(self, flag_attr: str, chan_attr: str):
        try:
            if getattr(self, flag_attr, False):
                ch = getattr(self, chan_attr, None)
                if ch:
                    try:
                        ch.stop()
                    except Exception:
                        pass
                setattr(self, flag_attr, False)
                setattr(self, chan_attr, None)
        except Exception:
            pass

    def _update_dynamic_sounds(self):
        if self.state == GameState.PLAYING and self.lives <= 3:
            self._start_loop("sound_low_lifes", "_low_lifes_playing", "_chan_low_lifes", bypass_flags=True, use_any_base=True)
        else:
            self._stop_loop("_low_lifes_playing", "_chan_low_lifes")
        if self._boss_final_end_ms is not None and pygame.time.get_ticks() >= self._boss_final_end_ms:
            try:
                if self._chan_boss_final:
                    self._chan_boss_final.stop()
            except Exception:
                pass
            self._boss_final_end_ms = None
            self._chan_boss_final = None

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
        Fase 3+ (phase>=2): inimigos aleatórios entre enemy_level3 e enemy_level3_2
        """
        if self.phase == 0:
            return [self.enemy_level1_img]
        elif self.phase == 1:
            return [self.enemy_level2_img]
        else:
            return [self.enemy_level3_img, self.enemy_level3_2_img]

    def _create_enemies(self, config: DifficultyConfig):
        """Cria naves inimigas e os ADICIONA AOS GRUPOS"""
        for _ in range(config.enemies):
            x = self._rand_x_avoiding_boss_column(Sizes.ENEMY[0])
            y = random.randint(-500, -40)
            speed = random.randint(config.speed_min, config.speed_max)
            enemy_imgs = self._get_enemy_images_for_phase()
            img = random.choice(enemy_imgs)

            enemy = Enemy(x, y, speed, img)

            self.all_sprites.add(enemy)
            self.enemy_group.add(enemy)

    def _clear_game_groups(self):
        """Limpa todos os sprites do jogo (exceto o jogador)."""
        self.enemy_group.empty()
        self.item_group.empty()
        self.shield_group.empty()
        self.bullet_group.empty()
        self.explosion_group.empty()
        self.boss_group.empty()
        self.all_sprites.empty()
        if hasattr(self, 'shield_aura_group'):
            self.shield_aura_group.empty()
        if self.player:
            self.all_sprites.add(self.player)

    def new_game(self):
        """Inicia um novo jogo (single-player)"""
        self.multiplayer = False
        self.player2 = None
        diff_config = DIFFICULTIES[self.difficulty]
        self.score = 0
        self.lives = diff_config.lives
        self.phase = 0
        self.items_collected = 0
        self.boss_defeated = False
        self.boss_spawned = False
        self.boss_hp = 0.0
        self.boss_group.empty()
        self.next_item_spawn_score = None
        self.next_shield_spawn_score = None
        self.invulnerable_until_ms = 0
        self.last_shot_ms = 0
        self.last_shot_ms_p1 = 0
        self.last_shot_ms_p2 = 0

        if not self.player:
            self.player = Player(
                self.config.WIDTH // 2, self.config.HEIGHT - 60,
                self.player_idle, self.player_up, control_scheme="both"
            )
        else:
            self.player.control_scheme = "both"
            self.player.reset_position(self.config.WIDTH // 2, self.config.HEIGHT - 60)

        self.player_group.add(self.player)
        self.all_sprites.add(self.player)

        self.enemy_group.empty()
        self.item_group.empty()
        self.shield_group.empty()
        self.bullet_group.empty()
        self.explosion_group.empty()
        if hasattr(self, 'shield_aura_group'):
            self.shield_aura_group.empty()

        self._create_enemies(diff_config.scale_for_phase(0))

        self._reset_item_spawn_schedule()
        self._reset_shield_spawn_schedule()
        self.state = GameState.PLAYING

    def new_game_multiplayer(self):
        """Inicia um novo jogo em modo Multiplayer (2 jogadores, tiros automáticos)"""
        self.multiplayer = True
        diff_config = DIFFICULTIES[self.difficulty]
        self.score = 0
        self.lives = diff_config.lives
        self.phase = 0
        self.items_collected = 0
        self.boss_defeated = False
        self.boss_spawned = False
        self.boss_hp = 0.0
        self.boss_group.empty()
        self.next_item_spawn_score = None
        self.next_shield_spawn_score = None
        self.invulnerable_until_ms = 0
        now = pygame.time.get_ticks()
        self.last_shot_ms_p1 = now
        self.last_shot_ms_p2 = now

        self.player = Player(
            self.config.WIDTH // 3, self.config.HEIGHT - 60,
            self.player_idle, self.player_up, control_scheme="arrows"
        )
        self.player2 = Player(
            (self.config.WIDTH * 2) // 3, self.config.HEIGHT - 60,
            self.player_idle, self.player_up, control_scheme="wasd"
        )

        self.enemy_group.empty()
        self.item_group.empty()
        self.shield_group.empty()
        self.bullet_group.empty()
        self.explosion_group.empty()
        if hasattr(self, 'shield_aura_group'):
            self.shield_aura_group.empty()
        self.all_sprites.empty()
        self.all_sprites.add(self.player)
        self.all_sprites.add(self.player2)

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

        try:
            if isinstance(data.get("volumes"), dict):
                for k, v in data["volumes"].items():
                    if k in self.volumes:
                        try:
                            self.volumes[k] = _normalize_volume_value(v)
                        except Exception:
                            pass
            if isinstance(data.get("sound_enabled"), dict):
                for k, v in data["sound_enabled"].items():
                    if k in self.sound_enabled and isinstance(v, bool):
                        self.sound_enabled[k] = v
            self._apply_volumes()
        except Exception as e:
            print(f"Aviso: falha ao aplicar configurações de som do save: {e}")

        self.boss_spawned = False
        self.boss_hp = 0.0
        self.boss_group.empty()

        self.next_item_spawn_score = None
        self.next_shield_spawn_score = None
        self.invulnerable_until_ms = 0
        self.last_shot_ms = 0

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
        if hasattr(self, 'shield_aura_group'):
            self.shield_aura_group.empty()

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
        if self.score < self._get_phase_target():
            return False
        if self.items_collected < self._get_phase_required_items():
            return False
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
        return self.phase >= 1

    def _item_speed_for_phase(self) -> int:
        return 7 if self.phase == 1 else 8

    def _reset_item_spawn_schedule(self):
        if self._is_item_enabled():
            self.next_item_spawn_score = _next_multiple_of_20_above(self.score)
        else:
            self.next_item_spawn_score = None

    def _reset_shield_spawn_schedule(self):
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
        self.lives -= 1

        if 0 < self.score < 50:
            self.score = max(0, self.score - 2)
        elif self.score >= 50:
            self.score = max(0, self.score - 5)

        if self.sound_hit:
            self.sound_hit.play()

    def _advance_phase(self):
        """Avança para a próxima fase"""
        try:
            self._stop_loop("_phase_wait_snd_playing", "_chan_phase_wait")
        except Exception:
            pass
        self._sfx_duck = 1.0
        try:
            self._apply_volumes()
        except Exception:
            pass
        self.phase += 1
        self.items_collected = 0
        self.boss_defeated = False
        self.boss_spawned = False
        self.boss_hp = 0.0

        self.enemy_group.empty()
        self.item_group.empty()
        self.shield_group.empty()
        self.bullet_group.empty()
        self.explosion_group.empty()
        self.boss_group.empty()

        self.all_sprites.empty()
        if self.player:
            self.all_sprites.add(self.player)
        if self.multiplayer and getattr(self, 'player2', None):
            self.all_sprites.add(self.player2)

        self._reset_item_spawn_schedule()
        self._reset_shield_spawn_schedule()
        self.invulnerable_until_ms = 0
        self.last_shot_ms = 0
        self.last_shot_ms_p1 = 0
        self.last_shot_ms_p2 = 0

        if self.player:
            self.player.reset_position(self.config.WIDTH // 2, self.config.HEIGHT - 60)
        if self.multiplayer and getattr(self, 'player2', None):
            self.player.reset_position(self.config.WIDTH // 3, self.config.HEIGHT - 60)
            self.player2.reset_position((self.config.WIDTH * 2) // 3, self.config.HEIGHT - 60)
        diff_config = DIFFICULTIES[self.difficulty]
        self._create_enemies(diff_config.scale_for_phase(self.phase))

        self.state = GameState.PLAYING
        self.phase_victory_end = None

    def _try_shoot(self, keys):
        """Dispara projétil se Espaço estiver pressionado."""
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

    def _spawn_boss_if_ready(self):
        """Spawna o boss na fase 3+ quando objetivos base (pontos/itens) estiverem completos."""
        if self.boss_spawned or self.boss_defeated:
            return
        if not self._is_boss_required():
            return
        if self.score < self._get_phase_target():
            return
        if self.items_collected < self._get_phase_required_items():
            return
        boss_sprite = Boss(self.boss_img_sleep, self.config.WIDTH)
        self.boss_group.add(boss_sprite)
        self.all_sprites.add(boss_sprite)
        self.boss = boss_sprite
        self.boss_hp = 100.0
        self.boss_spawned = True
        self.boss_next_move_threshold = 90.0
        try:
            if hasattr(self, 'sound_boss_final') and self.sound_boss_final:
                self._chan_boss_final = self.sound_boss_final.play()
                try:
                    point_vol = self.volumes.get("point", 0.0) if self.sound_enabled.get("point", True) else 0.0
                    hit_vol = self.volumes.get("hit", 0.0) if self.sound_enabled.get("hit", True) else 0.0
                    shoot_vol = self.volumes.get("shoot", 0.0) if self.sound_enabled.get("shoot", True) else 0.0
                    sfx_base_enabled = max([point_vol, hit_vol, shoot_vol]) if any([
                        self.sound_enabled.get(k, True) for k in ("point", "hit", "shoot")
                    ]) else 0.0
                    sfx_base_any = max(float(self.volumes.get("point", 0.0)), float(self.volumes.get("hit", 0.0)), float(self.volumes.get("shoot", 0.0)))
                    base = sfx_base_enabled if sfx_base_enabled > 0.0 else sfx_base_any
                    boost = self._sfx_boost.get("boss_final", 1.0) if hasattr(self, "_sfx_boost") else 1.0
                    duck = self._sfx_duck if hasattr(self, "_sfx_duck") else 1.0
                    vol = max(0.0, min(1.0, float(base) * float(boost) * float(duck)))
                    if self._chan_boss_final:
                        self._chan_boss_final.set_volume(vol)
                except Exception:
                    pass
                self._boss_final_end_ms = pygame.time.get_ticks() + 5000
        except Exception:
            pass

    def get_boss_forbidden_x_range(self, sprite_w: int):
        if not self.boss_spawned or self.boss_defeated or not self.boss:
            return None
        boss_left = self.boss.rect.left
        boss_right = self.boss.rect.right
        pad = max(0, sprite_w // 2)
        left = max(0, boss_left - pad)
        right = min(self.config.WIDTH - 1, boss_right + pad)
        if left >= right:
            return None
        return left, right

    def _rand_x_avoiding_boss_column(self, sprite_w: int) -> int:
        forbid = self.get_boss_forbidden_x_range(sprite_w)
        x_min = 0
        x_max = self.config.WIDTH - sprite_w
        if not forbid:
            return random.randint(x_min, x_max)
        lx, rx = forbid
        left_end = max(x_min, lx - sprite_w)
        right_start = min(x_max, rx + 1)
        intervals = []
        if left_end > x_min:
            intervals.append((x_min, left_end))
        if right_start < x_max:
            intervals.append((right_start, x_max))
        if not intervals:
            return random.randint(x_min, x_max)
        seg = random.choice(intervals)
        return random.randint(seg[0], max(seg[0], seg[1]))

    def _move_boss_random_top(self):
        if not self.boss or not self.boss_spawned:
            return
        y = random.randint(10, max(10, self.config.HEIGHT // 4))
        half_w = self.boss.rect.width // 2
        cx = random.randint(half_w, self.config.WIDTH - half_w)
        self.boss.rect.midtop = (cx, y)

    def _update_boss_sprite_by_hp(self):
        """Atualiza o sprite do boss conforme a vida.
        Inicial: sleep
        ← 90%: normal (golem boss)
        ← 50%: volta ao sleep (golem_boss_sleep)
        """
        if not self.boss_spawned or not self.boss:
            return
        if self.boss_hp <= 50.0:
            img = self.boss_img_rage
        elif self.boss_hp <= 90.0:
            img = self.boss_img_normal
        else:
            img = self.boss_img_sleep
        prev_midtop = self.boss.rect.midtop
        self.boss.image = img
        self.boss.rect = self.boss.image.get_rect()
        self.boss.rect.midtop = prev_midtop

    def _draw_boss_health_bar(self):
        if not self.boss_spawned or not self.boss or self.boss_defeated:
            return
        bar_width = self.boss.rect.width
        bar_height = 10
        x = self.boss.rect.left
        y = self.boss.rect.top - bar_height - 6
        pygame.draw.rect(self.screen, (50,50,50), (x, y, bar_width, bar_height))
        pct = max(0.0, min(100.0, self.boss_hp))
        fill_w = int(bar_width * (pct / 100.0))
        color = (0, 200, 0) if pct > 50 else (220, 180, 0) if pct > 20 else (200, 50, 50)
        pygame.draw.rect(self.screen, color, (x, y, fill_w, bar_height))
        txt = self.font_tiny.render(f"{pct:.0f}%", True, Colors.WHITE)
        self.screen.blit(txt, (x + bar_width//2 - txt.get_width()//2, y - 2 - txt.get_height()))

    def update_gameplay(self):
        """Atualiza lógica do gameplay usando grupos de sprites"""
        keys = pygame.key.get_pressed()

        if self.multiplayer and getattr(self, 'player2', None):
            self.player.update(keys, self.config.WIDTH, self.config.HEIGHT)
            self.player2.update(keys, self.config.WIDTH, self.config.HEIGHT)
        else:
            self.player.update(keys, self.config.WIDTH, self.config.HEIGHT)

        if self.multiplayer and getattr(self, 'player2', None):
            now = pygame.time.get_ticks()
            if now - self.last_shot_ms_p1 >= Sizes.FIRE_COOLDOWN_MS:
                bx = self.player.rect.centerx - Sizes.BULLET[0] // 2
                by = self.player.rect.top - Sizes.BULLET[1]
                bullet = Bullet(bx, by)
                self.all_sprites.add(bullet)
                self.bullet_group.add(bullet)
                self.last_shot_ms_p1 = now
                if hasattr(self, "sound_shoot") and self.sound_shoot:
                    try:
                        self.sound_shoot.play()
                    except Exception:
                        pass
            if now - self.last_shot_ms_p2 >= Sizes.FIRE_COOLDOWN_MS:
                bx = self.player2.rect.centerx - Sizes.BULLET[0] // 2
                by = self.player2.rect.top - Sizes.BULLET[1]
                bullet = Bullet(bx, by)
                self.all_sprites.add(bullet)
                self.bullet_group.add(bullet)
                self.last_shot_ms_p2 = now
                if hasattr(self, "sound_shoot") and self.sound_shoot:
                    try:
                        self.sound_shoot.play()
                    except Exception:
                        pass
        else:
            self._try_shoot(keys)

        self.enemy_group.update()
        self.item_group.update()
        self.shield_group.update()
        self.bullet_group.update()
        self.explosion_group.update()
        self.boss_group.update()

        self._spawn_boss_if_ready()
        try:
            self._update_dynamic_sounds()
        except Exception:
            pass

        diff_config = DIFFICULTIES[self.difficulty].scale_for_phase(self.phase)

        aura_active = hasattr(self, 'shield_aura_group') and getattr(self, 'shield_aura_group', None) is not None and len(self.shield_aura_group) > 0
        now_ms = pygame.time.get_ticks()
        inv_active = now_ms < self.invulnerable_until_ms
        owner = getattr(self, 'aura_owner', self.player)
        if inv_active and not aura_active and owner is not None:
            try:
                self.shield_aura_group = getattr(self, 'shield_aura_group', pygame.sprite.GroupSingle())
                if len(self.shield_aura_group) > 0:
                    for s in self.shield_aura_group.sprites():
                        s.kill()
                aura = ShieldAura(owner)
                self.shield_aura_group.add(aura)
            except Exception:
                pass
        elif not inv_active and aura_active:
            try:
                for s in self.shield_aura_group.sprites():
                    s.kill()
            except Exception:
                pass
        if hasattr(self, 'shield_aura_group') and self.shield_aura_group:
            self.shield_aura_group.update()

        def process_player_enemy_collisions(plyr):
            hits_local = pygame.sprite.spritecollide(plyr, self.enemy_group, False)
            if hits_local:
                now_loc = pygame.time.get_ticks()
                inv_loc = now_loc < self.invulnerable_until_ms
                for enemy_hit in hits_local:
                    if not inv_loc:
                        self._handle_enemy_collision()
                    enemy_hit.randomize_position()
                    enemy_hit.speed = random.randint(diff_config.speed_min, diff_config.speed_max)
                if self.lives <= 0 and not inv_loc:
                    self.state = GameState.GAME_OVER
                    return True
            return False

        if process_player_enemy_collisions(self.player):
            return
        if self.multiplayer and getattr(self, 'player2', None):
            if process_player_enemy_collisions(self.player2):
                return

        hits = pygame.sprite.groupcollide(self.bullet_group, self.enemy_group, True, True)
        if hits:
            for enemy_list in hits.values():
                for enemy in enemy_list:
                    frames_to_use = None
                    try:
                        if enemy.image == self.enemy_level3_2_img and hasattr(self, "enemy_3_2_explosion_frames") and self.enemy_3_2_explosion_frames:
                            frames_to_use = self.enemy_3_2_explosion_frames
                        elif enemy.image == self.enemy_level1_img and hasattr(self, "enemy_1_explosion_frames") and self.enemy_1_explosion_frames:
                            frames_to_use = self.enemy_1_explosion_frames
                        elif enemy.image == self.enemy_level2_img and hasattr(self, "enemy_2_explosion_frames") and self.enemy_2_explosion_frames:
                            frames_to_use = self.enemy_2_explosion_frames
                    except Exception:
                        frames_to_use = None
                    if not frames_to_use and hasattr(self, "explosion_frames") and self.explosion_frames:
                        frames_to_use = self.explosion_frames
                    if frames_to_use:
                        exp = Explosion(enemy.rect.center, frames_to_use, frame_time_ms=40, scale=(80, 80))
                        self.explosion_group.add(exp)
                    self.score += 1
                    if self.sound_point:
                        self.sound_point.play()

                    x = self._rand_x_avoiding_boss_column(Sizes.ENEMY[0])
                    y = random.randint(-100, -40)
                    speed = random.randint(diff_config.speed_min, diff_config.speed_max)
                    enemy_imgs = self._get_enemy_images_for_phase()
                    img = random.choice(enemy_imgs)
                    new_enemy = Enemy(x, y, speed, img)
                    self.all_sprites.add(new_enemy)
                    self.enemy_group.add(new_enemy)

        if self.boss_spawned and not self.boss_defeated:
            boss_hits = pygame.sprite.groupcollide(self.bullet_group, self.boss_group, True, False)
            if boss_hits:
                total_hits = len(boss_hits.keys())
                if total_hits > 0:
                    self.boss_hp = max(0.0, self.boss_hp - 0.3 * total_hits)
                if hasattr(self, 'boss_next_move_threshold') and self.boss_spawned and not self.boss_defeated:
                    while self.boss_hp <= getattr(self, 'boss_next_move_threshold', -10.0):
                        self._move_boss_random_top()
                        self.boss_next_move_threshold -= 10.0
                        if self.boss_next_move_threshold < 0.0:
                            break

                self._update_boss_sprite_by_hp()
                if self.boss_hp <= 0.0 and self.boss:
                    self.boss_defeated = True
                    self.boss_spawned = False
                    try:
                        if hasattr(self, 'sound_boss_explosion') and self.sound_boss_explosion:
                            try:
                                point_v = float(self.volumes.get("point", 0.0))
                                hit_v = float(self.volumes.get("hit", 0.0))
                                shoot_v = float(self.volumes.get("shoot", 0.0))
                                base = max(point_v, hit_v, shoot_v)
                                boost = self._sfx_boost.get("boss_explosion", 1.0) if hasattr(self, "_sfx_boost") else 1.0
                                duck = self._sfx_duck if hasattr(self, "_sfx_duck") else 1.0
                                vol = max(0.0, min(1.0, base * boost * duck))
                                self.sound_boss_explosion.set_volume(vol)
                            except Exception:
                                pass
                            self.sound_boss_explosion.play()
                    except Exception:
                        pass
                    try:
                        if self._chan_boss_final:
                            self._chan_boss_final.stop()
                    except Exception:
                        pass
                    try:
                        self.boss.kill()
                    except Exception:
                        pass
                    self.boss = None
                    self.score += 5
                    self.state = GameState.VICTORY
                    return

        def process_item_pickups(plyr):
            item_hits_local = pygame.sprite.spritecollide(plyr, self.item_group, True)
            if item_hits_local:
                self.items_collected += len(item_hits_local)
                try:
                    snd = getattr(self, 'sound_collect_star', None)
                    if snd:
                        try:
                            point_v = float(self.volumes.get("point", 0.0))
                            hit_v = float(self.volumes.get("hit", 0.0))
                            shoot_v = float(self.volumes.get("shoot", 0.0))
                            base = max(point_v, hit_v, shoot_v)
                            boost = self._sfx_boost.get("collect_star", 1.0) if hasattr(self, "_sfx_boost") else 1.0
                            duck = self._sfx_duck if hasattr(self, "_sfx_duck") else 1.0
                            vol = max(0.0, min(1.0, base * boost * duck))
                            snd.set_volume(vol)
                        except Exception:
                            pass
                        snd.play()
                    elif self.sound_point:
                        self.sound_point.play()
                except Exception:
                    pass
        process_item_pickups(self.player)
        if self.multiplayer and getattr(self, 'player2', None):
            process_item_pickups(self.player2)

        def process_shield_pickups(plyr):
            shield_hits_local = pygame.sprite.spritecollide(plyr, self.shield_group, True)
            if shield_hits_local:
                self.invulnerable_until_ms = pygame.time.get_ticks() + 5000
                self.aura_owner = plyr
                if self.sound_point:
                    self.sound_point.play()
        process_shield_pickups(self.player)
        if self.multiplayer and getattr(self, 'player2', None):
            process_shield_pickups(self.player2)

        # --- 3. Lógica de Jogo (Spawns, Vitória) ---
        if self._is_item_enabled():
            if self.next_item_spawn_score is None:
                self._reset_item_spawn_schedule()
            if self.next_item_spawn_score is not None and self.score >= self.next_item_spawn_score:
                if len(self.item_group) == 0:
                    self._spawn_item()
                self.next_item_spawn_score += 20

        if self.next_shield_spawn_score is None:
            self._reset_shield_spawn_schedule()
        if self.next_shield_spawn_score is not None and self.score >= self.next_shield_spawn_score:
            if len(self.shield_group) == 0:
                self._spawn_shield()
            self.next_shield_spawn_score += 33

        if self._has_phase_victory():
            self.state = GameState.PHASE_VICTORY
            self.phase_victory_end = pygame.time.get_ticks() + self.config.PHASE_VICTORY_DURATION

    def draw_gameplay(self):
        """Desenha o gameplay"""
        self.screen.blit(self._get_bg_for_current_phase(), (0, 0))

        self.all_sprites.draw(self.screen)
        if hasattr(self, 'shield_aura_group') and self.shield_aura_group:
            self.shield_aura_group.draw(self.screen)
        self.explosion_group.draw(self.screen)
        self._draw_boss_health_bar()

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
        # Tocar som de tela de espera da fase
        try:
            # Garante que o aviso de poucas vidas não concorra com o som da tela de espera
            self._stop_loop("_low_lifes_playing", "_chan_low_lifes")
            if not self._phase_wait_snd_playing:
                # Ativa ducking dos demais sons enquanto a música de espera toca
                self._sfx_duck = 0.4
                self._apply_volumes()
            # Inicia mesmo com SFX base desativados e usa o maior slider para volume
            self._start_loop("sound_load_levels", "_phase_wait_snd_playing", "_chan_phase_wait", bypass_flags=True, use_any_base=True)
        except Exception:
            pass

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

        # Tocar som de pausa em loop
        try:
            # interrompe aviso de poucas vidas durante a pausa
            self._stop_loop("_low_lifes_playing", "_chan_low_lifes")
            self._start_loop("sound_pause_game", "_pause_snd_playing", "_chan_pause")
        except Exception:
            pass

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
                    try:
                        self._stop_loop("_pause_snd_playing", "_chan_pause")
                    except Exception:
                        pass
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
                        try:
                            self._stop_loop("_pause_snd_playing", "_chan_pause")
                        except Exception:
                            pass
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        choice = options[selected]
                        if choice == "Continuar":
                            self.state = GameState.PLAYING
                            paused = False
                            try:
                                self._stop_loop("_pause_snd_playing", "_chan_pause")
                            except Exception:
                                pass
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
                            try:
                                self._stop_loop("_pause_snd_playing", "_chan_pause")
                            except Exception:
                                pass
                        elif choice == "Salvar e fechar o jogo":
                            # Salva progresso atual e encerra aplicação
                            if self.player is not None:
                                self.save_manager.save(
                                    self.difficulty, self.score, self.lives,
                                    self.phase, self.player.rect.center,
                                    items_collected=self.items_collected,
                                    boss_defeated=self.boss_defeated
                                )
                            try:
                                self._stop_loop("_pause_snd_playing", "_chan_pause")
                            except Exception:
                                pass
                            return False

            self.clock.tick(self.config.FPS)

        return True

    def run_menu(self) -> bool:
        """Executa menu. Retorna False se deve sair do jogo"""
        menu_options = ["Novo jogo", "Multiplayer", "Carregar jogo salvo", "Escolher dificuldade", "Configurações", "Sair"]
        selected = 0
        message = ""
        message_timer = 0

        while self.state == GameState.MENU:
            self.screen.blit(self.bg_menu, (0, 0))

            # Título
            title = self.font_medium.render("SPACE ATAQUE", True, Colors.YELLOW)
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
                        elif choice == "Multiplayer":
                            self.new_game_multiplayer()
                        elif choice == "Carregar jogo salvo":
                            if not self.load_game():
                                message = "Nenhum jogo salvo encontrado."
                                message_timer = self.config.FPS * 2
                        elif choice == "Escolher dificuldade":
                            self._difficulty_menu()
                        elif choice == "Configurações":
                            self._settings_menu()
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
        # Som de ponte espacial durante a escolha de dificuldade
        try:
            self._start_loop("sound_space_bridge", "_space_bridge_playing", "_chan_space_bridge")
        except Exception:
            pass

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
                    try:
                        self._stop_loop("_space_bridge_playing", "_chan_space_bridge")
                    except Exception:
                        pass
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        selected = (selected + 1) % len(diffs)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        selected = (selected - 1) % len(diffs)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.difficulty = diffs[selected]
                        choosing = False
                        try:
                            self._stop_loop("_space_bridge_playing", "_chan_space_bridge")
                        except Exception:
                            pass
                    elif event.key == pygame.K_ESCAPE:
                        choosing = False
                        try:
                            self._stop_loop("_space_bridge_playing", "_chan_space_bridge")
                        except Exception:
                            pass

            self.clock.tick(self.config.FPS)

    def _settings_menu(self):
        """Menu de configurações de áudio (volumes e ativação por som)."""
        options = [
            ("music", "Música"),
            ("point", "Som de ponto"),
            ("hit", "Som de dano"),
            ("shoot", "Som de tiro"),
        ]
        selected = 0
        choosing = True
        # Som de ponte espacial durante a configuração do som
        try:
            self._start_loop("sound_space_bridge", "_space_bridge_playing", "_chan_space_bridge")
        except Exception:
            pass

        def _vol_to_percent(v: float) -> int:
            try:
                return max(0, min(100, int(round(v * 100))))
            except Exception:
                return 0

        while choosing:
            self.screen.blit(self.bg_menu, (0, 0))

            title = self.font_medium.render("Configurações de Áudio", True, Colors.YELLOW)
            self.screen.blit(title, (self.config.WIDTH // 2 - title.get_width() // 2, 80))

            start_y = 200
            for i, (key, label_text) in enumerate(options):
                enabled = self.sound_enabled.get(key, True)
                vol = _vol_to_percent(self.volumes.get(key, 0.0))
                status = "Ligado" if enabled else "Desligado"
                text = f"{label_text}: {vol}%  ({status})"
                color = Colors.YELLOW if i == selected else Colors.WHITE
                label = self.font_tiny.render(text, True, color)
                self.screen.blit(label, (self.config.WIDTH // 2 - label.get_width() // 2, start_y + i * 40))

            hint1 = self.font_tiny.render("↑/↓ selecionar  •  ←/→ volume  •  ENTER/ESPAÇO liga/desliga  •  ESC voltar", True, Colors.WHITE)
            self.screen.blit(hint1, (self.config.WIDTH // 2 - hint1.get_width() // 2, 420))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    choosing = False
                    self.state = GameState.MENU
                    try:
                        self._stop_loop("_space_bridge_playing", "_chan_space_bridge")
                    except Exception:
                        pass
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        selected = (selected + 1) % len(options)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        selected = (selected - 1) % len(options)
                    elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                        key, _ = options[selected]
                        step = -5 if event.key in (pygame.K_LEFT, pygame.K_a) else 5
                        current = _vol_to_percent(self.volumes.get(key, 0.0))
                        new_percent = max(0, min(100, current + step))
                        self.volumes[key] = new_percent / 100.0
                        self._apply_volumes()
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        key, _ = options[selected]
                        self.sound_enabled[key] = not self.sound_enabled.get(key, True)
                        # aplica imediatamente
                        if key == "music":
                            if self.sound_enabled[key]:
                                try:
                                    pygame.mixer.music.unpause()
                                except Exception:
                                    pass
                            else:
                                try:
                                    pygame.mixer.music.pause()
                                except Exception:
                                    pass
                        self._apply_volumes()
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

        # Parar loops e sons persistentes
        try:
            self._stop_loop("_pause_snd_playing", "_chan_pause")
            self._stop_loop("_low_lifes_playing", "_chan_low_lifes")
            self._stop_loop("_phase_wait_snd_playing", "_chan_phase_wait")
            self._stop_loop("_space_bridge_playing", "_chan_space_bridge")
        except Exception:
            pass
        try:
            if self._chan_boss_final:
                self._chan_boss_final.stop()
        except Exception:
            pass

        # Restaura ducking para normal antes de tocar o som de game over
        self._sfx_duck = 1.0
        try:
            self._apply_volumes()
        except Exception:
            pass

        pygame.mixer.music.stop()
        # Som de game over
        try:
            if hasattr(self, 'sound_gameover') and self.sound_gameover and self._is_sfx_enabled():
                self.sound_gameover.play()
        except Exception:
            pass

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

    def run_victory(self) -> bool:
        try:
            highscore = self.save_manager.save(
                self.difficulty, self.score, self.lives,
                self.phase, self.player.rect.center if self.player else (self.config.WIDTH//2, self.config.HEIGHT-60),
                items_collected=self.items_collected,
                boss_defeated=True
            )
        except Exception:
            highscore = self.save_manager.get_highscore()

        try:
            self._stop_loop("_pause_snd_playing", "_chan_pause")
            self._stop_loop("_low_lifes_playing", "_chan_low_lifes")
            self._stop_loop("_phase_wait_snd_playing", "_chan_phase_wait")
            self._stop_loop("_space_bridge_playing", "_chan_space_bridge")
        except Exception:
            pass
        try:
            if self._chan_boss_final:
                self._chan_boss_final.stop()
        except Exception:
            pass

        self._sfx_duck = 1.0
        try:
            self._apply_volumes()
        except Exception:
            pass
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        try:
            self.screen.blit(self.bg_endgame, (0, 0))
        except Exception:
            self.screen.fill((0, 0, 0))

        title = self.font_large.render("VITÓRIA!", True, Colors.YELLOW)
        subtitle = self.font_small.render("Você derrotou o chefe final!", True, Colors.WHITE)

        labels = [
            f"Fase: {self.phase + 1}",
            f"Dificuldade: {self.difficulty}",
            f"Pontuação: {self.score}",
            f"Maior pontuação: {highscore}"
        ]

        self.screen.blit(title, (self.config.WIDTH // 2 - title.get_width() // 2, 120))
        self.screen.blit(subtitle, (self.config.WIDTH // 2 - subtitle.get_width() // 2, 190))

        start_y = 260
        for i, text in enumerate(labels):
            label = self.font_small.render(text, True, Colors.WHITE)
            self.screen.blit(label, (self.config.WIDTH // 2 - label.get_width() // 2, start_y + i * 50))

        hint = self.font_tiny.render("Pressione qualquer tecla para voltar ao menu", True, Colors.WHITE)
        self.screen.blit(hint, (self.config.WIDTH // 2 - hint.get_width() // 2, self.config.HEIGHT - 80))

        pygame.display.flip()

        waiting = True
        start_time = pygame.time.get_ticks()
        TIMEOUT_MS = 5000
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    waiting = False
                    self.state = GameState.MENU
            if pygame.time.get_ticks() - start_time >= TIMEOUT_MS:
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

            elif self.state == GameState.VICTORY:
                running = self.run_victory()

        pygame.quit()


# =============================================================================
# EXECUÇÃO
# =============================================================================

if __name__ == "__main__":
    game = SpaceAtaque()
    game.run()