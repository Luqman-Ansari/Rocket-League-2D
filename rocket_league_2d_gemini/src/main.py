# main.py
import pygame
import sys
from src.settings import WIDTH, HEIGHT
from src.assets_loader import assets_loader
from src.menu import MenuManager
from src.game import Match


class Game:
    """Main game application class managing the game loop."""
    
    def __init__(self):
        """Initialize pygame and game components."""
        pygame.init()
        pygame.mixer.init()
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Rocket Soccer: Ultimate Edition")
        self.clock = pygame.time.Clock()
        
        # Load assets once at startup
        assets_loader.init_assets()
        
        # Initialize managers
        self.menu_manager = MenuManager(self.screen, self.clock)
        
    def run(self):
        """Main application loop."""
        while True:
            # Show main menu and get game configuration
            assets_loader.play_music("MENU")
            game_config = self.menu_manager.show()
            
            if game_config is None:
                # User selected Exit
                break
            
            # Run match with the selected configuration
            action = 'RESTART'
            while action == 'RESTART':
                match = Match(self.screen, self.clock, game_config)
                action = match.run()
            
            # If action is 'MENU', loop continues to top
            # If action is 'QUIT', we break below
            if action == 'QUIT':
                break
        
        self.quit()
    
    def quit(self):
        """Clean shutdown."""
        pygame.quit()
        sys.exit()


def main():
    """Entry point for the application."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()