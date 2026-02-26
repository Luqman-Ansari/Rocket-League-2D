# menu.py
import pygame
import math
from settings import *
import assets_loader

# --- UI ELEMENT CLASSES ---
class Button:
    def __init__(self, text, x, y, w=300, h=60, action=None):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.action = action
        self.hovered = False
        self.scale = 1.0
        
    def draw(self, screen):
        # Hover Animation Logic
        target_scale = 1.1 if self.hovered else 1.0
        self.scale += (target_scale - self.scale) * 0.2
        
        # Color & Font
        color = HOVER_COLOR if self.hovered else WHITE
        font = assets_loader.FONTS['ui']
        
        # Draw Text with Shadow
        shadow_surf = font.render(self.text, True, BLACK)
        text_surf = font.render(self.text, True, color)
        
        # Scaling
        if abs(self.scale - 1.0) > 0.01:
            w = int(text_surf.get_width() * self.scale)
            h = int(text_surf.get_height() * self.scale)
            text_surf = pygame.transform.scale(text_surf, (w, h))
            shadow_surf = pygame.transform.scale(shadow_surf, (w, h))

        # Center Position
        text_rect = text_surf.get_rect(center=self.rect.center)
        shadow_rect = shadow_surf.get_rect(center=(self.rect.centerx + 3, self.rect.centery + 3))
        
        screen.blit(shadow_surf, shadow_rect)
        screen.blit(text_surf, text_rect)

    def check_input(self, event):
        # 1. Handle Hover Effect (Visuals)
        if event.type == pygame.MOUSEMOTION:
            is_over = self.rect.collidepoint(event.pos)
            if is_over and not self.hovered:
                if assets_loader.SOUNDS['hover']: assets_loader.SOUNDS['hover'].play()
            self.hovered = is_over
            
        # 2. Handle Click (Action)
        if event.type == pygame.MOUSEBUTTONDOWN:
            # We check collidepoint directly here to be robust against fast clicks
            if self.rect.collidepoint(event.pos) and self.action:
                if assets_loader.SOUNDS['click']: assets_loader.SOUNDS['click'].play()
                return self.action
        return None

# --- MENU FUNCTIONS ---

def draw_background(screen):
    bg = assets_loader.GRAPHICS.get('menu_bg')
    if bg:
        screen.blit(bg, (0,0))
    else:
        # Dynamic Gradient Fallback
        for i in range(HEIGHT):
            r = 20 + (i * 40 // HEIGHT)
            g = 20 + (i * 40 // HEIGHT)
            b = 40 + (i * 40 // HEIGHT)
            pygame.draw.line(screen, (r,g,b), (0,i), (WIDTH, i))

def main_menu_loop(screen, clock):
    """ Main Menu Entry Point. Returns configuration dict or None (Quit) """
    
    state = "MAIN" 
    selected_mode_key = "HOCKEY"    # Default Game Mode
    duration_input_text = "200" 
    
    center_x = WIDTH // 2
    start_y = 215
    gap = 70
    
    # Main Menu Buttons
    btns_main = [
        Button("PLAY MATCH", center_x - 150, start_y, action="GOTO_DURATION"),
        Button("GAME MODE", center_x - 150, start_y + gap, action="MODE"),
        Button("CONTROLS", center_x - 150, start_y + gap*2, action="CONTROLS"),
        Button("HOW TO PLAY", center_x - 150, start_y + gap*3, action="HELP"),
        Button("EXIT", center_x - 150, start_y + gap*4, action="EXIT")
    ]
    
    # Back Button
    btn_back = Button("BACK", center_x - 100, HEIGHT - 100, 200, 60, action="BACK")

    # Play Button
    btn_play = Button("P L A Y", center_x - 100, HEIGHT - 200, 200, 60, action="PLAY")

    mode_rects = {
        'SOCCER': pygame.Rect(40, 175, 440, 295),
        'HOCKEY': pygame.Rect(520, 175, 440, 295)
    }
    mode_scales = {'SOCCER': 1.0, 'HOCKEY': 1.0}

    while True:
        screen.fill(BLACK)
        draw_background(screen)
        
        # --- HEADER ---
        logo = assets_loader.GRAPHICS.get('logo')
        
        if state == "MAIN" and logo:
            scale = 0.37 + 0.04 * math.sin(pygame.time.get_ticks() * 0.003)
            w = int(logo.get_width() * scale)
            h = int(logo.get_height() * scale)
            logo_scaled = pygame.transform.scale(logo, (w, h))
            screen.blit(logo_scaled, (WIDTH//2 - w//2, 50))
        else:
            title_text = "ROCKET SOCCER"
            if state == "MODE": title_text = "SELECT GAME MODE"
            elif state == "CONTROLS": title_text = "CONTROLS"
            elif state == "HELP": title_text = "HOW TO PLAY"
            elif state == "DURATION": title_text = "MATCH SETUP"
            
            t_surf = assets_loader.FONTS['title'].render(title_text, True, WHITE)
            screen.blit(t_surf, (WIDTH//2 - t_surf.get_width()//2, 50))

        # --- CONTENT ---
        
        if state == "MAIN":
            for btn in btns_main:
                btn.draw(screen)
            v_surf = assets_loader.FONTS['body'].render("v2.2 Stable", True, LIGHT_GRAY)
            screen.blit(v_surf, (WIDTH - 120, HEIGHT - 30))

        elif state == "DURATION":
            lbl = assets_loader.FONTS['ui'].render("ENTER MATCH DURATION (Seconds):", True, BLUE)
            screen.blit(lbl, (WIDTH//2 - lbl.get_width()//2, HEIGHT//2 - 100))
            
            input_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 40, 300, 80)
            pygame.draw.rect(screen, (0,0,0,150), input_rect, border_radius=10)
            pygame.draw.rect(screen, GREEN, input_rect, 3, border_radius=10)
            
            #txt_surf = assets_loader.FONTS['title'].render(duration_input_text + "_", True, WHITE)
            txt_surf = assets_loader.FONTS['title'].render(duration_input_text, True, WHITE)
            screen.blit(txt_surf, (input_rect.centerx - txt_surf.get_width()//2, input_rect.centery - txt_surf.get_height()//2))
            
            inst = assets_loader.FONTS['body'].render("Press ENTER or click PLAY to Start Match", True, ORANGE)
            screen.blit(inst, (WIDTH//2 - inst.get_width()//2, HEIGHT//2 + 60))

            btn_play.draw(screen)
            btn_back.draw(screen)

        elif state == "MODE":
            mouse_pos = pygame.mouse.get_pos()
            for key, base_rect in mode_rects.items():
                mode = GAME_MODES[key]
                is_hover = base_rect.collidepoint(mouse_pos)
                is_selected = (selected_mode_key == key)
                
                target_scale = 1.05 if is_hover else 1.0
                mode_scales[key] += (target_scale - mode_scales[key]) * 0.15
                current_scale = mode_scales[key]
                
                scaled_w = int(base_rect.width * current_scale)
                scaled_h = int(base_rect.height * current_scale)
                draw_rect = pygame.Rect(0, 0, scaled_w, scaled_h)
                draw_rect.center = base_rect.center

                field_tex = assets_loader.GRAPHICS.get(mode['field_texture'])
                if field_tex:
                    thumb = pygame.transform.scale(field_tex, (draw_rect.width, draw_rect.height))
                    screen.blit(thumb, draw_rect.topleft)
                else:
                    pygame.draw.rect(screen, GRAY, draw_rect)

                overlay = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160)) 
                screen.blit(overlay, draw_rect.topleft)

                border_color = ORANGE if is_selected else (WHITE if is_hover else LIGHT_GRAY)
                border_width = 4 if is_selected else 2
                pygame.draw.rect(screen, border_color, draw_rect, border_width)
                
                ball_img = assets_loader.GRAPHICS.get(mode['ball_texture'])
                if ball_img:
                    ball_img = pygame.transform.scale(ball_img, (64, 64))
                    screen.blit(ball_img, (draw_rect.centerx - 32, draw_rect.top + 40))
                
                name_surf = assets_loader.FONTS['ui'].render(mode['name'], True, WHITE)
                screen.blit(name_surf, (draw_rect.centerx - name_surf.get_width()//2, draw_rect.top + 120))
                
                desc_words = mode['desc'].split(' ')
                line1 = " ".join(desc_words[:len(desc_words)//2])
                line2 = " ".join(desc_words[len(desc_words)//2:])
                
                d1 = assets_loader.FONTS['body'].render(line1, True, LIGHT_GRAY)
                d2 = assets_loader.FONTS['body'].render(line2, True, LIGHT_GRAY)
                screen.blit(d1, (draw_rect.centerx - d1.get_width()//2, draw_rect.top + 180))
                screen.blit(d2, (draw_rect.centerx - d2.get_width()//2, draw_rect.top + 210))

            #info = assets_loader.FONTS['body'].render("Click to Select", True, WHITE)
            #screen.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT - 150))
            
            btn_back.draw(screen)

        elif state == "CONTROLS":
            y = 160
            lines = [
                "PLAYER 1 (BLUE): W,A,S,D + L-SHIFT (Boost)",
                "PLAYER 2 (RED): ARROWS + R-SHIFT (Boost)",
                "",
                "P / ESC: Pause Game",
                "R: Restart Match (Paused)",
                "M: Main Menu (Paused)",
                "Q: Quit Game (Paused)"
            ]
            for line in lines:
                if "PLAYER 1" in line:
                    surf = assets_loader.FONTS['ui_small'].render(line, True, BLUE)
                elif "PLAYER 2" in line:
                    surf = assets_loader.FONTS['ui_small'].render(line, True, RED)
                else:
                    surf = assets_loader.FONTS['ui_small'].render(line, True, LIGHT_GRAY)
                screen.blit(surf, (WIDTH//2 - surf.get_width()//2, y))
                if line == "":
                    y += 30
                else:
                    y += 50
            btn_back.draw(screen)

        elif state == "HELP":
            y = 190
            rules = [
                "OBJECTIVE: Score more goals than opponent!",
                "1. Each team has 1 Player + 1 AI Goalkeeper",
                "2. Hold SHIFT to Boost (1.5x Speed)",
                "3. Collisions transfer momentum",
                "4. Hockey Mode has low friction (slippery!)",
                "",
                "Good luck!"
            ]
            for line in rules:
                surf = assets_loader.FONTS['body'].render(line, True, LIGHT_GRAY)
                screen.blit(surf, (230, y))
                y += 40
            btn_back.draw(screen)

        # --- EVENT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            
            # 1. GLOBAL BACK BUTTON (FIXED LOGIC)
            if state in ["MODE", "CONTROLS", "HELP", "DURATION"]:
                if btn_back.check_input(event) == "BACK":
                    state = "MAIN"
                    if assets_loader.SOUNDS['click']: assets_loader.SOUNDS['click'].play()
                    continue # <--- Stop processing this event immediately!
            
            # 2. STATE SPECIFIC INPUTS
            if state == "MAIN":
                for btn in btns_main:
                    res = btn.check_input(event)
                    if res == "GOTO_DURATION":
                        state = "DURATION"
                    elif res == "MODE":
                        state = "MODE"
                    elif res == "CONTROLS":
                        state = "CONTROLS"
                    elif res == "HELP":
                        state = "HELP"
                    elif res == "EXIT":
                        return None
            
            elif state == "DURATION":
                # 1. Track if we should start the game
                start_match = False

                # Check Button Click (This handles Mouse Events internally)
                if btn_play.check_input(event) == "PLAY":
                    start_match = True

                # Check Keyboard Inputs
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        start_match = True
                    
                    elif event.key == pygame.K_BACKSPACE:
                        duration_input_text = duration_input_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        state = "MAIN"
                    elif event.unicode.isdigit() and len(duration_input_text) < 4:
                        duration_input_text += event.unicode

                # 2. Execute Start Logic if triggered by either Enter OR Button
                if start_match:
                    final_config = GAME_MODES[selected_mode_key].copy()
                    try:
                        d = int(duration_input_text)
                        if d < 10: d = 10 
                        if d > 9999: d = 9999
                        final_config['duration'] = d
                    except ValueError:
                        final_config['duration'] = 200
                    
                    if assets_loader.SOUNDS['click']: assets_loader.SOUNDS['click'].play()
                    return final_config

            elif state == "MODE":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if mode_rects['SOCCER'].collidepoint(event.pos):
                        selected_mode_key = 'SOCCER'
                        if assets_loader.SOUNDS['click']: assets_loader.SOUNDS['click'].play()
                    elif mode_rects['HOCKEY'].collidepoint(event.pos):
                        selected_mode_key = 'HOCKEY'
                        if assets_loader.SOUNDS['click']: assets_loader.SOUNDS['click'].play()
                
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = "MAIN"
            
            elif state in ["CONTROLS", "HELP"]:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = "MAIN"

        pygame.display.flip()
        clock.tick(60)