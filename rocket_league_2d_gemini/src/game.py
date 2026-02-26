# game.py
import pygame
import os
import numpy as np
from src.settings import *
from src.assets_loader import assets_loader
from src.objects import Car, Goalkeeper, Ball, SimpleAICar, TrainedAICar
from src.physics import Physics

try:
    from stable_baselines3 import PPO
    SB3_AVAILABLE = True
except ImportError:
    SB3_AVAILABLE = False
    print("Warning: stable_baselines3 not installed. Trained models will not work.")


class HUD:
    """Manages game HUD rendering."""
    
    @staticmethod
    def draw(screen, score, time_left, winner_text=""):
        """Draw the game HUD."""
        # Score
        score_txt = assets_loader.FONTS['header'].render(f"{score[0]} - {score[1]}", True, WHITE)
        screen.blit(score_txt, (WIDTH//2 - score_txt.get_width()//2, 20))
        
        # Timer
        col = RED if time_left < 10 else WHITE
        timer_txt = assets_loader.FONTS['hud'].render(f"{int(time_left)}", True, col)
        screen.blit(timer_txt, (WIDTH//2 - timer_txt.get_width()//2, 80))
        
        if winner_text:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill(GRAY_TRANSPARENT)
            screen.blit(ov, (0, 0))
            
            t = assets_loader.FONTS['title'].render("GAME OVER", True, WHITE)
            screen.blit(t, (WIDTH//2 - t.get_width()//2, 200))
            
            w = assets_loader.FONTS['header'].render(winner_text, True, ORANGE)
            screen.blit(w, (WIDTH//2 - w.get_width()//2, 300))
            
            i = assets_loader.FONTS['ui'].render("[R] Restart   [M] Menu", True, GREEN)
            screen.blit(i, (WIDTH//2 - i.get_width()//2, 400))
    
    @staticmethod
    def draw_goal_message(screen):
        """Draw goal celebration message."""
        gm = assets_loader.FONTS['hud_big'].render("GOAL!", True, ORANGE)
        screen.blit(gm, (WIDTH//2 - gm.get_width()//2, HEIGHT//2 - 40))
    
    @staticmethod
    def draw_pause_menu(screen):
        """Draw pause overlay."""
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill(GRAY_TRANSPARENT)
        screen.blit(ov, (0, 0))
        
        t = assets_loader.FONTS['title'].render("PAUSED", True, WHITE)
        screen.blit(t, (WIDTH//2 - t.get_width()//2, 200))
        
        i = assets_loader.FONTS['ui'].render("Press [P] to Resume", True, WHITE)
        screen.blit(i, (WIDTH//2 - i.get_width()//2, 300))
        
        m = assets_loader.FONTS['body'].render("[M] Menu   [R] Restart   [Q] Quit", True, ORANGE)
        screen.blit(m, (WIDTH//2 - m.get_width()//2, 380))


class Match:
    """Manages a single game match."""
    
    def __init__(self, screen, clock, mode_config):
        """Initialize match with configuration."""
        self.screen = screen
        self.clock = clock
        self.config = mode_config
        
        # Extract configuration
        self.friction_car = mode_config['friction_car']
        self.friction_ball = mode_config['friction_ball']
        self.ball_texture = mode_config['ball_texture']
        self.field_texture = mode_config.get('field_texture', 'field')
        self.duration = mode_config['duration']
        self.opponent_type = mode_config.get('opponent_type', 'HUMAN')
        
        # Game state
        self.game_state = "PLAYING"
        self.score = [0, 0]
        self.goal_timer = 0
        self.winner_text = ""
        
        # Time management
        self.start_ticks = pygame.time.get_ticks()
        self.paused_at_ticks = 0
        self.total_pause_duration = 0
        
        # Initialize game objects
        self.rl_model = None
        self._init_players()
        self._init_ball()
        
        # Start game music
        assets_loader.play_music("GAME")
    
    def _init_players(self):
        """Initialize players based on opponent type."""
        if self.opponent_type == "HUMAN":
            # Both players are human-controlled
            self.p1 = Car(200, HEIGHT//2, BLUE,
                         {'up': pygame.K_w, 'down': pygame.K_s, 'left': pygame.K_a, 
                          'right': pygame.K_d, 'boost': pygame.K_LSHIFT},
                         'car_blue', self.friction_car)
            
            self.p2 = Car(WIDTH-200, HEIGHT//2, RED,
                         {'up': pygame.K_UP, 'down': pygame.K_DOWN, 'left': pygame.K_LEFT,
                          'right': pygame.K_RIGHT, 'boost': pygame.K_m},
                         'car_red', self.friction_car)
        else:
            # p2 (Red/Right) is Human, p1 (Blue/Left) is Bot
            self.p2 = Car(WIDTH-200, HEIGHT//2, RED,
                         {'up': pygame.K_UP, 'down': pygame.K_DOWN, 'left': pygame.K_LEFT,
                          'right': pygame.K_RIGHT, 'boost': pygame.K_m},
                         'car_red', self.friction_car)
            
            if self.opponent_type == "Basic":
                self.p1 = SimpleAICar(200, HEIGHT//2, BLUE, 'car_blue', self.friction_car)
            else:
                self.p1 = TrainedAICar(200, HEIGHT//2, BLUE, 'car_blue', self.friction_car)
                self._load_ai_model()
        
        # Initialize goalkeepers
        self.gk1 = Goalkeeper(50, HEIGHT//2, DARK_BLUE, 'left', 'gk_blue', self.friction_car)
        self.gk2 = Goalkeeper(WIDTH-50, HEIGHT//2, DARK_RED, 'right', 'gk_red', self.friction_car)
        
        self.all_cars = [self.p1, self.p2, self.gk1, self.gk2]
    
    def _init_ball(self):
        """Initialize the ball."""
        self.ball = Ball(self.ball_texture, self.friction_ball)
    
    def _load_ai_model(self):
        """Load trained AI model if available."""
        if not SB3_AVAILABLE:
            print("stable_baselines3 not available, using Basic AI")
            self.p1 = SimpleAICar(200, HEIGHT//2, BLUE, 'car_blue', self.friction_car)
            return
        
        model_path = os.path.join("..", "rl", "versions", f"{self.opponent_type}.zip")
        if os.path.exists(model_path):
            try:
                self.rl_model = PPO.load(model_path)
                print(f"Loaded AI model: {self.opponent_type}")
            except Exception as e:
                print(f"Error loading model {self.opponent_type}: {e}")
                self.p1 = SimpleAICar(200, HEIGHT//2, BLUE, 'car_blue', self.friction_car)
        else:
            print(f"Model file not found: {model_path}")
            self.p1 = SimpleAICar(200, HEIGHT//2, BLUE, 'car_blue', self.friction_car)
    
    def run(self):
        """Main match loop. Returns action string: 'MENU', 'RESTART', or 'QUIT'."""
        while True:
            # Handle events
            action = self._handle_events()
            if action:
                return action
            
            # Update game state
            self._update()
            
            # Render
            self._draw()
            
            pygame.display.flip()
            self.clock.tick(FPS)
    
    def _handle_events(self):
        """Handle pygame events. Returns action if leaving match."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'QUIT'
            
            if event.type == pygame.KEYDOWN:
                if self.game_state == "PLAYING":
                    if event.key in [pygame.K_ESCAPE, pygame.K_p]:
                        self._pause()
                
                elif self.game_state == "PAUSED":
                    if event.key in [pygame.K_ESCAPE, pygame.K_p]:
                        self._resume()
                    elif event.key == pygame.K_m:
                        return 'MENU'
                    elif event.key == pygame.K_r:
                        return 'RESTART'
                    elif event.key == pygame.K_q:
                        return 'QUIT'
                
                elif self.game_state == "GAMEOVER":
                    if event.key == pygame.K_m:
                        return 'MENU'
                    elif event.key == pygame.K_r:
                        return 'RESTART'
                    elif event.key == pygame.K_q:
                        return 'QUIT'
        
        return None
    
    def _pause(self):
        """Pause the game."""
        self.game_state = "PAUSED"
        self.paused_at_ticks = pygame.time.get_ticks()
    
    def _resume(self):
        """Resume the game."""
        self.game_state = "PLAYING"
        self.total_pause_duration += (pygame.time.get_ticks() - self.paused_at_ticks)
    
    def _update(self):
        """Update game state."""
        # Calculate time
        time_left = self._calculate_time_left()
        
        # Check for game over
        if time_left == 0 and self.game_state != "GAMEOVER":
            self._end_game()
        
        # Update only if playing
        if self.game_state == "PLAYING":
            if self.goal_timer == 0:
                self._update_gameplay()
            else:
                self.goal_timer -= 1
                if self.goal_timer == 0:
                    self._reset_positions()
    
    def _calculate_time_left(self):
        """Calculate remaining time."""
        if self.game_state in ["PLAYING", "GAMEOVER"]:
            current_ticks = pygame.time.get_ticks()
            time_elapsed = (current_ticks - self.start_ticks - self.total_pause_duration) / 1000
            return max(0, self.duration - time_elapsed)
        return 0
    
    def _update_gameplay(self):
        """Update game entities and physics."""
        keys = pygame.key.get_pressed()
        
        # Handle player controls
        if self.opponent_type == "HUMAN":
            self.p1.handle(keys)
            self.p2.handle(keys)
        else:
            self.p2.handle(keys)
            self._update_bot()
        
        # Update entities
        if self.opponent_type == "HUMAN":
            self.p1.update()
        self.p2.update()
        
        self.gk1.update_ai(self.ball)
        self.gk2.update_ai(self.ball)
        self.ball.update()
        
        # Physics collisions
        for car in self.all_cars:
            Physics.resolve_car_ball(car, self.ball)
        
        for i in range(len(self.all_cars)):
            for j in range(i + 1, len(self.all_cars)):
                Physics.resolve_car_car(self.all_cars[i], self.all_cars[j])
        
        # Goal detection
        self._check_goals()
    
    def _update_bot(self):
        """Update bot AI behavior."""
        if isinstance(self.p1, SimpleAICar):
            self.p1.chase_ball(self.ball)
        elif isinstance(self.p1, TrainedAICar) and self.rl_model is not None:
            obs = self._create_observation()
            action, _ = self.rl_model.predict(obs, deterministic=True)
            self.p1.apply_ai_action(action)
        else:
            self.p1.update()
    
    def _create_observation(self):
        """Create observation array for trained AI."""
        max_speed = 7.0
        return np.array([
            self.p1.x / WIDTH,
            self.p1.y / HEIGHT,
            self.p1.vx / max_speed,
            self.p1.vy / max_speed,
            self.p2.x / WIDTH,
            self.p2.y / HEIGHT,
            self.p2.vx / max_speed,
            self.p2.vy / max_speed,
            self.ball.x / WIDTH,
            self.ball.y / HEIGHT,
            self.ball.vx / 15.0,
            self.ball.vy / 15.0,
            self.gk1.y / HEIGHT,
            self.gk2.y / HEIGHT
        ], dtype=np.float32)
    
    def _check_goals(self):
        """Check if a goal was scored."""
        # Left goal (Red scores)
        if self.ball.x - self.ball.radius < 0 and GOAL_TOP_Y < self.ball.y < GOAL_BOTTOM_Y:
            self.score[1] += 1
            self.goal_timer = 90
            if assets_loader.SOUNDS['goal']:
                assets_loader.SOUNDS['goal'].play()
        
        # Right goal (Blue scores)
        elif self.ball.x + self.ball.radius > WIDTH and GOAL_TOP_Y < self.ball.y < GOAL_BOTTOM_Y:
            self.score[0] += 1
            self.goal_timer = 90
            if assets_loader.SOUNDS['goal']:
                assets_loader.SOUNDS['goal'].play()
    
    def _reset_positions(self):
        """Reset all entities to starting positions."""
        self.ball.reset()
        self.p1.x, self.p1.y = 200, HEIGHT//2
        self.p1.vx = self.p1.vy = 0
        self.p2.x, self.p2.y = WIDTH-200, HEIGHT//2
        self.p2.vx = self.p2.vy = 0
        self.gk1.x, self.gk1.y = 50, HEIGHT//2
        self.gk1.vx = self.gk1.vy = 0
        self.gk2.x, self.gk2.y = WIDTH-50, HEIGHT//2
        self.gk2.vx = self.gk2.vy = 0
    
    def _end_game(self):
        """End the game and determine winner."""
        self.game_state = "GAMEOVER"
        if self.score[0] > self.score[1]:
            self.winner_text = "BLUE TEAM WINS!"
        elif self.score[1] > self.score[0]:
            self.winner_text = "RED TEAM WINS!"
        else:
            self.winner_text = "MATCH DRAW!"
    
    def _draw(self):
        """Draw all game elements."""
        self._draw_field()
        self._draw_goals()
        self._draw_entities()
        self._draw_hud()
        self._draw_overlays()
    
    def _draw_field(self):
        """Draw the field background."""
        field_img = assets_loader.GRAPHICS.get(self.field_texture)
        if field_img:
            self.screen.blit(field_img, (0, 0))
        else:
            # Fallback with simple field markings
            bg_col = self.config.get('bg_color', FIELD_COLOR_GRASS)
            self.screen.fill(bg_col)
            pygame.draw.rect(self.screen, WHITE, (0, 0, WIDTH, HEIGHT), 3)
            pygame.draw.line(self.screen, WHITE, (WIDTH//2, 0), (WIDTH//2, HEIGHT), 3)
            pygame.draw.circle(self.screen, WHITE, (WIDTH//2, HEIGHT//2), 70, 3)
    
    def _draw_goals(self):
        """Draw goal boxes."""
        pygame.draw.rect(self.screen, WHITE, (0, GOAL_TOP_Y, 60, GOAL_WIDTH), 3)
        pygame.draw.rect(self.screen, WHITE, (WIDTH-60, GOAL_TOP_Y, 60, GOAL_WIDTH), 3)
    
    def _draw_entities(self):
        """Draw all game entities."""
        self.ball.draw(self.screen)
        for car in self.all_cars:
            car.draw(self.screen)
    
    def _draw_hud(self):
        """Draw HUD elements."""
        time_left = self._calculate_time_left()
        winner = self.winner_text if self.game_state == "GAMEOVER" else ""
        HUD.draw(self.screen, self.score, time_left, winner)
    
    def _draw_overlays(self):
        """Draw overlays (goal message, pause menu, etc)."""
        if self.goal_timer > 0 and self.game_state == "PLAYING":
            HUD.draw_goal_message(self.screen)
        
        if self.game_state == "PAUSED":
            HUD.draw_pause_menu(self.screen)


# Legacy function for backwards compatibility
def run_match(screen, clock, mode_config):
    """Legacy function - use Match class instead."""
    match = Match(screen, clock, mode_config)
    return match.run()
    field_tex_key = mode_config.get('field_texture', 'field')
    duration = mode_config['duration']
    opponent_type = mode_config.get('opponent_type', 'HUMAN')
    
    # 2. Init Players based on Opponent Type
    rl_model = None  # For trained AI models
    
    if opponent_type == "HUMAN":
        # Both players are human-controlled
        p1 = Car(200, HEIGHT//2, BLUE, 
                 {'up':pygame.K_w,'down':pygame.K_s,'left':pygame.K_a,'right':pygame.K_d,'boost':pygame.K_LSHIFT}, 
                 'car_blue', friction_car)
        
        p2 = Car(WIDTH-200, HEIGHT//2, RED, 
                 {'up':pygame.K_UP,'down':pygame.K_DOWN,'left':pygame.K_LEFT,'right':pygame.K_RIGHT,'boost':pygame.K_m},
                 'car_red', friction_car)
    else:
        # p2 (Red/Right) is Human, p1 (Blue/Left) is Bot
        p2 = Car(WIDTH-200, HEIGHT//2, RED, 
                 {'up':pygame.K_UP,'down':pygame.K_DOWN,'left':pygame.K_LEFT,'right':pygame.K_RIGHT,'boost':pygame.K_m},
                 'car_red', friction_car)
        
        if opponent_type == "Basic":
            # Hardcoded simple AI
            p1 = SimpleAICar(200, HEIGHT//2, BLUE, 'car_blue', friction_car)
        else:
            # Trained RL model
            p1 = TrainedAICar(200, HEIGHT//2, BLUE, 'car_blue', friction_car)
            
            # Load the model
            if SB3_AVAILABLE:
                model_path = os.path.join("..", "rl", "versions", f"{opponent_type}.zip")
                if os.path.exists(model_path):
                    try:
                        rl_model = PPO.load(model_path)
                        print(f"Loaded AI model: {opponent_type}")
                    except Exception as e:
                        print(f"Error loading model {opponent_type}: {e}")
                        # Fallback to basic AI
                        p1 = SimpleAICar(200, HEIGHT//2, BLUE, 'car_blue', friction_car)
                else:
                    print(f"Model file not found: {model_path}")
                    # Fallback to basic AI
                    p1 = SimpleAICar(200, HEIGHT//2, BLUE, 'car_blue', friction_car)
            else:
                print("stable_baselines3 not available, using Basic AI")
                p1 = SimpleAICar(200, HEIGHT//2, BLUE, 'car_blue', friction_car)
    
    gk1 = Goalkeeper(50, HEIGHT//2, DARK_BLUE, 'left', 'gk_blue', friction_car)
    gk2 = Goalkeeper(WIDTH-50, HEIGHT//2, DARK_RED, 'right', 'gk_red', friction_car)
    
    all_cars = [p1, p2, gk1, gk2]
    ball = Ball(ball_tex, friction_ball)
    
    score = [0,0]
    
    # 3. Time Management
    start_ticks = pygame.time.get_ticks()
    paused_at_ticks = 0 
    total_pause_duration = 0
    goal_timer = 0
    game_state = "PLAYING"
    winner_text = ""

    assets_loader.play_music("GAME")

    while True:
        current_ticks = pygame.time.get_ticks()
        
        # --- INPUT ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'QUIT'
            
            if event.type == pygame.KEYDOWN:
                if game_state == "PLAYING":
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                        game_state = "PAUSED"
                        paused_at_ticks = current_ticks
                
                elif game_state == "PAUSED":
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                        game_state = "PLAYING"
                        total_pause_duration += (current_ticks - paused_at_ticks)
                    elif event.key == pygame.K_m: return 'MENU'
                    elif event.key == pygame.K_r: return 'RESTART'
                    elif event.key == pygame.K_q: return 'QUIT'
                        
                elif game_state == "GAMEOVER":
                    if event.key == pygame.K_m: return 'MENU'
                    elif event.key == pygame.K_r: return 'RESTART'
                    elif event.key == pygame.K_q: return 'QUIT'

        # --- UPDATE ---
        time_left = 0
        if game_state == "PLAYING" or game_state == "GAMEOVER":
            time_elapsed = (current_ticks - start_ticks - total_pause_duration) / 1000
            time_left = max(0, duration - time_elapsed)
            
            if time_left == 0 and game_state != "GAMEOVER":
                game_state = "GAMEOVER"
                if score[0] > score[1]: winner_text = "BLUE TEAM WINS!"
                elif score[1] > score[0]: winner_text = "RED TEAM WINS!"
                else: winner_text = "MATCH DRAW!"

        if game_state == "PLAYING":
            keys = pygame.key.get_pressed()
            
            # Handle player controls
            if opponent_type == "HUMAN":
                # Both players are human
                p1.handle(keys)
                p2.handle(keys)
            else:
                # Only p2 (Red) is human
                p2.handle(keys)
            
            if goal_timer == 0:
                # Handle AI bot actions
                if opponent_type != "HUMAN":
                    if isinstance(p1, SimpleAICar):
                        # Basic hardcoded bot
                        p1.chase_ball(ball)
                    elif isinstance(p1, TrainedAICar) and rl_model is not None:
                        # Trained RL model
                        # Create observation array (14 float32 values)
                        max_speed = 7.0  # Should match Car.max_speed
                        obs = np.array([
                            p1.x / WIDTH,
                            p1.y / HEIGHT,
                            p1.vx / max_speed,
                            p1.vy / max_speed,
                            p2.x / WIDTH,
                            p2.y / HEIGHT,
                            p2.vx / max_speed,
                            p2.vy / max_speed,
                            ball.x / WIDTH,
                            ball.y / HEIGHT,
                            ball.vx / 15.0,
                            ball.vy / 15.0,
                            gk1.y / HEIGHT,
                            gk2.y / HEIGHT
                        ], dtype=np.float32)
                        
                        # Get action from model
                        action, _states = rl_model.predict(obs, deterministic=True)
                        p1.apply_ai_action(action)
                    else:
                        # Fallback: just update position
                        p1.update()
                else:
                    # Both human players, regular update
                    p1.update()
                
                p2.update()
                gk1.update_ai(ball); gk2.update_ai(ball)
                ball.update()

                # Physics
                for car in all_cars: resolve_car_ball(car, ball)
                for i in range(len(all_cars)):
                    for j in range(i + 1, len(all_cars)):
                        resolve_car_car(all_cars[i], all_cars[j])

                # Goal Check
                if ball.x - ball.radius < 0 and GOAL_TOP_Y < ball.y < GOAL_BOTTOM_Y:
                    score[1] += 1; goal_timer = 90
                    if assets_loader.SOUNDS['goal']: assets_loader.SOUNDS['goal'].play()
                elif ball.x + ball.radius > WIDTH and GOAL_TOP_Y < ball.y < GOAL_BOTTOM_Y:
                    score[0] += 1; goal_timer = 90
                    if assets_loader.SOUNDS['goal']: assets_loader.SOUNDS['goal'].play()
            else:
                goal_timer -= 1
                if goal_timer == 0:
                    ball.reset()
                    p1.x, p1.y = 200, HEIGHT//2; p1.vx=p1.vy=0
                    p2.x, p2.y = WIDTH-200, HEIGHT//2; p2.vx=p2.vy=0
                    gk1.x, gk1.y = 50, HEIGHT//2; gk1.vx=gk1.vy=0
                    gk2.x, gk2.y = WIDTH-50, HEIGHT//2; gk2.vx=gk2.vy=0

        # --- DRAWING ---
        # Draw Field
        field_img = assets_loader.GRAPHICS.get(field_tex_key)
        if field_img:
            screen.blit(field_img, (0,0))
        else:
            # Fallback Color
            bg_col = mode_config.get('bg_color', FIELD_COLOR_GRASS)
            screen.fill(bg_col)
            pygame.draw.rect(screen, WHITE, (0, 0, WIDTH, HEIGHT), 3)
            pygame.draw.line(screen, WHITE, (WIDTH//2, 0), (WIDTH//2, HEIGHT), 3)
            pygame.draw.circle(screen, WHITE, (WIDTH//2, HEIGHT//2), 70, 3)

        # Draw Goal Boxes
        pygame.draw.rect(screen, WHITE, (0, GOAL_TOP_Y, 60, GOAL_WIDTH), 3)
        pygame.draw.rect(screen, WHITE, (WIDTH-60, GOAL_TOP_Y, 60, GOAL_WIDTH), 3)

        # Entities
        ball.draw(screen)
        for car in all_cars: car.draw(screen)

        # HUD / Overlays
        draw_hud(screen, score, time_left, winner_text if game_state == "GAMEOVER" else "")
        
        if goal_timer > 0 and game_state == "PLAYING":
            gm = assets_loader.FONTS['hud_big'].render("GOAL!", True, ORANGE)
            screen.blit(gm, (WIDTH//2 - gm.get_width()//2, HEIGHT//2 - 40))
            
        if game_state == "PAUSED":
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill(GRAY_TRANSPARENT)
            screen.blit(ov, (0,0))
            t = assets_loader.FONTS['title'].render("PAUSED", True, WHITE)
            screen.blit(t, (WIDTH//2 - t.get_width()//2, 200))
            i = assets_loader.FONTS['ui'].render("Press [P] to Resume", True, WHITE)
            screen.blit(i, (WIDTH//2 - i.get_width()//2, 300))
            m = assets_loader.FONTS['body'].render("[M] Menu   [R] Restart   [Q] Quit", True, ORANGE)
            screen.blit(m, (WIDTH//2 - m.get_width()//2, 380))

        pygame.display.flip()
        clock.tick(FPS)