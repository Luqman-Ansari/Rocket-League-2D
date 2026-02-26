# game.py
import pygame
from settings import *
import assets_loader
from objects import Car, Goalkeeper, Ball
from physics import resolve_car_ball, resolve_car_car

def draw_hud(screen, score, time_left, winner_text=""):
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
        screen.blit(ov, (0,0))
        
        t = assets_loader.FONTS['title'].render("GAME OVER", True, WHITE)
        screen.blit(t, (WIDTH//2 - t.get_width()//2, 200))
        
        w = assets_loader.FONTS['header'].render(winner_text, True, ORANGE)
        screen.blit(w, (WIDTH//2 - w.get_width()//2, 300))
        
        i = assets_loader.FONTS['ui'].render("[R] Restart   [M] Menu", True, GREEN)
        screen.blit(i, (WIDTH//2 - i.get_width()//2, 400))

def run_match(screen, clock, mode_config):
    """ 
    Runs the game loop. 
    mode_config: Dictionary from settings.GAME_MODES 
    """
    
    # 1. Setup based on Mode
    friction_car = mode_config['friction_car']
    friction_ball = mode_config['friction_ball']
    ball_tex = mode_config['ball_texture']
    field_tex_key = mode_config.get('field_texture', 'field')
    duration = mode_config['duration']
    
    # 2. Init Objects
    p1 = Car(200, HEIGHT//2, BLUE, 
             {'up':pygame.K_w,'down':pygame.K_s,'left':pygame.K_a,'right':pygame.K_d,'boost':pygame.K_LSHIFT}, 
             'car_blue', friction_car)
    
    p2 = Car(WIDTH-200, HEIGHT//2, RED, 
             {'up':pygame.K_UP,'down':pygame.K_DOWN,'left':pygame.K_LEFT,'right':pygame.K_RIGHT,'boost':pygame.K_m},   # K_RSHIFT
             'car_red', friction_car)
    
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
            p1.handle(keys); p2.handle(keys)
            
            if goal_timer == 0:
                p1.update(); p2.update()
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