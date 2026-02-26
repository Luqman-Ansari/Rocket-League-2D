# assets_loader.py
import pygame
import os
from settings import WIDTH, HEIGHT

GRAPHICS = {}
SOUNDS = {}
FONTS = {}

def load_texture(name, width=None, height=None):
    # Try multiple subfolders if necessary, but stick to structure
    path = os.path.join("assets", "textures", name)
    try:
        img = pygame.image.load(path).convert_alpha()
        if width and height:
            img = pygame.transform.scale(img, (width, height))
        return img
    except (FileNotFoundError, pygame.error):
        # Silent fail is okay, we handle None in drawing
        return None

def load_sound(name):
    path = os.path.join("assets", "sfx", name)
    try:
        return pygame.mixer.Sound(path)
    except (FileNotFoundError, pygame.error):
        return None

def load_font(name, size):
    path = os.path.join("assets", "fonts", name)
    try:
        return pygame.font.Font(path, size)
    except (FileNotFoundError, pygame.error):
        # Fallback system font
        return pygame.font.SysFont("Arial", size, bold=True)

def init_assets():
    # --- TEXTURES ---
    # UI / Menu
    GRAPHICS['menu_bg'] = load_texture('menu_bg.png', WIDTH, HEIGHT)
    # Adjust Transparency (Check if it loaded first to avoid crashes)
    if GRAPHICS['menu_bg']:
        GRAPHICS['menu_bg'].set_alpha(80)
        # 50  = Very transparent (ghostly)
        # 128 = 50% transparent
        # 200 = Slight transparency
        # 255 = Fully solid (Default)
    GRAPHICS['logo'] = load_texture('logo.png') # Don't resize yet
    GRAPHICS['button'] = load_texture('button_normal.png', 300, 60)
    
    # Field Variants
    GRAPHICS['field'] = load_texture('field.png', WIDTH, HEIGHT) # Legacy
    GRAPHICS['field_grass'] = load_texture('field_grass.png', WIDTH, HEIGHT)
    GRAPHICS['field_ice'] = load_texture('field_ice.png', WIDTH, HEIGHT)

    # Balls
    GRAPHICS['ball'] = load_texture('ball.png', 32, 32) # Legacy
    GRAPHICS['ball_soccer'] = load_texture('ball_soccer.png', 32, 32)
    GRAPHICS['ball_puck'] = load_texture('ball_puck.png', 32, 32)

    # Cars
    GRAPHICS['car_blue'] = load_texture('car_blue.png', 50, 50)
    GRAPHICS['car_red'] = load_texture('car_red.png', 50, 50)
    GRAPHICS['gk_blue'] = load_texture('gk_blue.png', 50, 50)
    GRAPHICS['gk_red'] = load_texture('gk_red.png', 50, 50)

    # --- SOUNDS ---
    SOUNDS['click'] = load_sound('click.wav')
    SOUNDS['hover'] = load_sound('hover.wav')
    SOUNDS['goal'] = load_sound('goal.wav')
    SOUNDS['bounce'] = load_sound('bounce.wav')
    SOUNDS['boost'] = load_sound('boost.wav')

    # --- FONTS ---
    # Attempting to load specific fonts requested
    FONTS['title'] = load_font('title_font.ttf', 80) # Black Ops One / Bungee
    FONTS['header'] = load_font('title_font.ttf', 60)
    FONTS['ui'] = load_font('main_font.ttf', 40)     # Orbitron
    FONTS['ui_small'] = load_font('main_font.ttf', 28)
    FONTS['body'] = load_font('body_font.ttf', 24)   # Exo 2
    FONTS['hud'] = load_font('main_font.ttf', 36)
    FONTS['hud_big'] = load_font('main_font.ttf', 70)

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

def play_music(type_name):
    """ Helper to switch tracks """
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