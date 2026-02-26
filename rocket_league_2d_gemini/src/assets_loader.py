# assets_loader.py
import pygame
import os
from src.settings import WIDTH, HEIGHT


class AssetsLoader:
    """Manages loading and storing game assets (graphics, sounds, fonts, music)"""
    
    def __init__(self):
        self.GRAPHICS = {}
        self.SOUNDS = {}
        self.FONTS = {}
    
    @staticmethod
    def load_texture(name, width=None, height=None):
        """Load a texture from the assets/textures folder"""
        path = os.path.join("assets", "textures", name)
        try:
            img = pygame.image.load(path).convert_alpha()
            if width and height:
                img = pygame.transform.scale(img, (width, height))
            return img
        except (FileNotFoundError, pygame.error):
            # Silent fail is okay, we handle None in drawing
            return None
    
    @staticmethod
    def load_sound(name):
        """Load a sound effect from the assets/sfx folder"""
        path = os.path.join("assets", "sfx", name)
        try:
            return pygame.mixer.Sound(path)
        except (FileNotFoundError, pygame.error):
            return None
    
    @staticmethod
    def load_font(name, size):
        """Load a font from the assets/fonts folder"""
        path = os.path.join("assets", "fonts", name)
        try:
            return pygame.font.Font(path, size)
        except (FileNotFoundError, pygame.error):
            # Fallback system font
            return pygame.font.SysFont("Arial", size, bold=True)
    
    def init_assets(self):
        """Initialize all game assets"""
        # --- TEXTURES ---
        # UI / Menu
        self.GRAPHICS['menu_bg'] = self.load_texture('menu_bg.png', WIDTH, HEIGHT)
        # Adjust Transparency (Check if it loaded first to avoid crashes)
        if self.GRAPHICS['menu_bg']:
            self.GRAPHICS['menu_bg'].set_alpha(80)
            # 50  = Very transparent (ghostly)
            # 128 = 50% transparent
            # 200 = Slight transparency
            # 255 = Fully solid (Default)
        self.GRAPHICS['logo'] = self.load_texture('logo.png')  # Don't resize yet
        self.GRAPHICS['button'] = self.load_texture('button_normal.png', 300, 60)
        
        # Field Variants
        self.GRAPHICS['field'] = self.load_texture('field.png', WIDTH, HEIGHT)  # Legacy
        self.GRAPHICS['field_grass'] = self.load_texture('field_grass.png', WIDTH, HEIGHT)
        self.GRAPHICS['field_ice'] = self.load_texture('field_ice.png', WIDTH, HEIGHT)

        # Balls
        self.GRAPHICS['ball'] = self.load_texture('ball.png', 32, 32)  # Legacy
        self.GRAPHICS['ball_soccer'] = self.load_texture('ball_soccer.png', 32, 32)
        self.GRAPHICS['ball_puck'] = self.load_texture('ball_puck.png', 32, 32)

        # Cars
        self.GRAPHICS['car_blue'] = self.load_texture('car_blue.png', 50, 50)
        self.GRAPHICS['car_red'] = self.load_texture('car_red.png', 50, 50)
        self.GRAPHICS['gk_blue'] = self.load_texture('gk_blue.png', 50, 50)
        self.GRAPHICS['gk_red'] = self.load_texture('gk_red.png', 50, 50)

        # --- SOUNDS ---
        self.SOUNDS['click'] = self.load_sound('click.wav')
        self.SOUNDS['hover'] = self.load_sound('hover.wav')
        self.SOUNDS['goal'] = self.load_sound('goal.wav')
        self.SOUNDS['bounce'] = self.load_sound('bounce.wav')
        self.SOUNDS['boost'] = self.load_sound('boost.wav')

        # --- FONTS ---
        # Attempting to load specific fonts requested
        self.FONTS['title'] = self.load_font('title_font.ttf', 80)  # Black Ops One / Bungee
        self.FONTS['header'] = self.load_font('title_font.ttf', 60)
        self.FONTS['ui'] = self.load_font('main_font.ttf', 40)  # Orbitron
        self.FONTS['ui_small'] = self.load_font('main_font.ttf', 28)
        self.FONTS['body'] = self.load_font('body_font.ttf', 24)  # Exo 2
        self.FONTS['hud'] = self.load_font('main_font.ttf', 36)
        self.FONTS['hud_big'] = self.load_font('main_font.ttf', 70)

        # --- MUSIC ---
        # We load menu music by default
        music_path = os.path.join("assets", "music", "menu_music.mp3")
        if os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.3)
                pygame.mixer.music.play(-1)
            except:
                pass
    
    def play_music(self, type_name):
        """Helper to switch music tracks"""
        filename = "menu_music.mp3" if type_name == "MENU" else "game_music.mp3"
        path = os.path.join("assets", "music", filename)
        if os.path.exists(path):
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(0.3)
                pygame.mixer.music.play(-1)
            except:
                pass


# Create singleton instance
assets_loader = AssetsLoader()