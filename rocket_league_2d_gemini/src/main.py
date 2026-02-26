# main.py
import pygame
import sys
from settings import WIDTH, HEIGHT
import assets_loader
from menu import main_menu_loop
from game import run_match

# 1. Init Pygame
pygame.init()
pygame.mixer.init()

# 2. Setup Screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rocket Soccer: Ultimate Edition")
clock = pygame.time.Clock()

# 3. Load Assets
assets_loader.init_assets()

# 4. Main Application Loop
while True:
    # 4a. Show Main Menu -> Returns game configuration or None
    assets_loader.play_music("MENU")
    game_config = main_menu_loop(screen, clock)
    
    if game_config is None:
        # User selected Exit
        break 
    
    # 4b. Run Match Loop
    action = 'RESTART'
    while action == 'RESTART':
        action = run_match(screen, clock, game_config)
    
    # If action is 'MENU', loop continues to top. 
    # If action is 'QUIT', we break below.
    if action == 'QUIT':
        break

pygame.quit()
sys.exit()