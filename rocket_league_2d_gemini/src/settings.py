# settings.py
import pygame

# --- SCREEN & GENERAL ---
WIDTH, HEIGHT = 1000, 600
FPS = 60

# --- COLORS ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (50, 50, 50)
LIGHT_GRAY = (180, 180, 180)

# Team Colors
BLUE = (40, 120, 255)
RED = (255, 80, 80)
DARK_BLUE = (20, 60, 128)
DARK_RED = (128, 40, 40)

# UI Colors
ORANGE = (255, 165, 0)
GREEN = (80, 200, 120)
HOVER_COLOR = (255, 200, 50)
TEXT_SHADOW = (20, 20, 20)

# Field Colors (Fallbacks)
FIELD_COLOR_GRASS = (30, 120, 30)
FIELD_COLOR_ICE = (200, 220, 255)
GRAY_TRANSPARENT = (0, 0, 0, 180) 

# --- GAME CONSTANTS ---
GK_SPEED_VAL = 4.5 
GOAL_WIDTH = 180
GOAL_TOP_Y = HEIGHT//2 - GOAL_WIDTH//2
GOAL_BOTTOM_Y = HEIGHT//2 + GOAL_WIDTH//2

# --- DEFAULT PHYSICS ---
# These are defaults, but Game Modes will override them
CAR_FRICTION = 0.980
BALL_FRICTION = 0.992

# --- GAME MODES ---
GAME_MODES = {
    'SOCCER': {
        'name': 'CLASSIC SOCCER',
        'desc': 'Traditional soccer on grass. Balanced physics.',
        'field_texture': 'field_grass', # Fallback to 'field' if not found
        'ball_texture': 'ball_soccer',
        'friction_car': 0.980,
        'friction_ball': 0.992,
        'ball_speed_mult': 1.0,
        'duration': 200,
        'bg_color': FIELD_COLOR_GRASS
    },
    'HOCKEY': {
        'name': 'ICE HOCKEY',
        'desc': 'Slippery ice, fast puck, high speed chaos!',
        'field_texture': 'field_ice',
        'ball_texture': 'ball_puck',
        'friction_car': 0.996, # Very slippery
        'friction_ball': 0.998,
        'ball_speed_mult': 1.3,
        'duration': 200,
        'bg_color': FIELD_COLOR_ICE
    }
}