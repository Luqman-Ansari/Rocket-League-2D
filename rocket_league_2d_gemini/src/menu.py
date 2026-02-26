# menu.py
import pygame
import math
import os
from src.settings import *
from src.assets_loader import assets_loader


class Button:
    """Interactive button with hover animations."""
    
    def __init__(self, text, x, y, w=300, h=60, action=None):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.action = action
        self.hovered = False
        self.scale = 1.0
        
    def draw(self, screen):
        """Draw button with hover animation."""
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
        """Handle mouse events for the button."""
        # Handle Hover Effect (Visuals)
        if event.type == pygame.MOUSEMOTION:
            is_over = self.rect.collidepoint(event.pos)
            if is_over and not self.hovered:
                if assets_loader.SOUNDS['hover']:
                    assets_loader.SOUNDS['hover'].play()
            self.hovered = is_over
            
        # Handle Click (Action)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos) and self.action:
                if assets_loader.SOUNDS['click']:
                    assets_loader.SOUNDS['click'].play()
                return self.action
        return None


class MenuManager:
    """Manages all menu screens and navigation."""
    
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        
        # Menu state
        self.state = "MAIN"
        self.selected_mode_key = "HOCKEY"
        self.duration_input_text = "200"
        self.opponent_type = "HUMAN"
        
        # Setup UI elements
        center_x = WIDTH // 2
        start_y = 215
        gap = 70
        
        # Main Menu Buttons
        self.btns_main = [
            Button("PLAY MATCH", center_x - 150, start_y, action="PLAYMODE"),
            Button("GAME MODE", center_x - 150, start_y + gap, action="MODE"),
            Button("CONTROLS", center_x - 150, start_y + gap*2, action="CONTROLS"),
            Button("HOW TO PLAY", center_x - 150, start_y + gap*3, action="HELP"),
            Button("EXIT", center_x - 150, start_y + gap*4, action="EXIT")
        ]
        
        # Navigation Buttons
        self.btn_back = Button("BACK", center_x - 100, HEIGHT - 100, 200, 60, action="BACK")
        self.btn_play = Button("P L A Y", center_x - 100, HEIGHT - 200, 200, 60, action="PLAY")
        
        # Play Mode Buttons
        self.btns_playmode = [
            Button("1 PLAYER (VS BOT)", center_x - 200, HEIGHT//2 - 60, 400, 60, action="BOTSELECT"),
            Button("2 PLAYER (LOCAL)", center_x - 200, HEIGHT//2 + 20, 400, 60, action="2PLAYER")
        ]
        
        # Bot Selection Buttons (dynamically generated)
        self.bot_buttons = []
        
        # Mode selection rects and animations
        self.mode_rects = {
            'SOCCER': pygame.Rect(40, 175, 440, 295),
            'HOCKEY': pygame.Rect(520, 175, 440, 295)
        }
        self.mode_scales = {'SOCCER': 1.0, 'HOCKEY': 1.0}
    
    def show(self):
        """Show the menu and return game configuration or None (quit)."""
        while True:
            self._draw()
            
            result = self._handle_events()
            # Only return if we got a valid result (None for quit, dict for game start)
            if result is None or isinstance(result, dict):
                return result
            
            pygame.display.flip()
            self.clock.tick(60)
    
    def _draw(self):
        """Draw the current menu screen."""
        self.screen.fill(BLACK)
        self._draw_background()
        self._draw_header()
        self._draw_content()
    
    def _draw_background(self):
        """Draw menu background."""
        bg = assets_loader.GRAPHICS.get('menu_bg')
        if bg:
            self.screen.blit(bg, (0, 0))
        else:
            # Dynamic Gradient Fallback
            for i in range(HEIGHT):
                r = 20 + (i * 40 // HEIGHT)
                g = 20 + (i * 40 // HEIGHT)
                b = 40 + (i * 40 // HEIGHT)
                pygame.draw.line(self.screen, (r, g, b), (0, i), (WIDTH, i))
    
    def _draw_header(self):
        """Draw the header/title for current screen."""
        logo = assets_loader.GRAPHICS.get('logo')
        
        if self.state == "MAIN" and logo:
            scale = 0.37 + 0.04 * math.sin(pygame.time.get_ticks() * 0.003)
            w = int(logo.get_width() * scale)
            h = int(logo.get_height() * scale)
            logo_scaled = pygame.transform.scale(logo, (w, h))
            self.screen.blit(logo_scaled, (WIDTH//2 - w//2, 50))
        else:
            title_text = {
                "MAIN": "ROCKET SOCCER",
                "MODE": "SELECT GAME MODE",
                "CONTROLS": "CONTROLS",
                "HELP": "HOW TO PLAY",
                "DURATION": "MATCH SETUP",
                "PLAYMODE": "SELECT PLAY MODE",
                "BOTSELECT": "SELECT OPPONENT"
            }.get(self.state, "ROCKET SOCCER")
            
            t_surf = assets_loader.FONTS['title'].render(title_text, True, WHITE)
            self.screen.blit(t_surf, (WIDTH//2 - t_surf.get_width()//2, 50))
    
    def _draw_content(self):
        """Draw content based on current state."""
        if self.state == "MAIN":
            self._draw_main_menu()
        elif self.state == "DURATION":
            self._draw_duration_input()
        elif self.state == "MODE":
            self._draw_mode_selection()
        elif self.state == "CONTROLS":
            self._draw_controls()
        elif self.state == "HELP":
            self._draw_help()
        elif self.state == "PLAYMODE":
            self._draw_playmode_selection()
        elif self.state == "BOTSELECT":
            self._draw_bot_selection()
    
    def _draw_main_menu(self):
        """Draw main menu buttons."""
        for btn in self.btns_main:
            btn.draw(self.screen)
        v_surf = assets_loader.FONTS['body'].render("v2.2 Stable", True, LIGHT_GRAY)
        self.screen.blit(v_surf, (WIDTH - 120, HEIGHT - 30))
    
    def _draw_duration_input(self):
        """Draw duration input screen."""
        lbl = assets_loader.FONTS['ui'].render("ENTER MATCH DURATION (Seconds):", True, BLUE)
        self.screen.blit(lbl, (WIDTH//2 - lbl.get_width()//2, HEIGHT//2 - 100))
        
        input_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 40, 300, 80)
        pygame.draw.rect(self.screen, (0, 0, 0, 150), input_rect, border_radius=10)
        pygame.draw.rect(self.screen, GREEN, input_rect, 3, border_radius=10)
        
        txt_surf = assets_loader.FONTS['title'].render(self.duration_input_text, True, WHITE)
        self.screen.blit(txt_surf, (input_rect.centerx - txt_surf.get_width()//2, 
                                    input_rect.centery - txt_surf.get_height()//2))
        
        inst = assets_loader.FONTS['body'].render("Press ENTER or click PLAY to Start Match", True, ORANGE)
        self.screen.blit(inst, (WIDTH//2 - inst.get_width()//2, HEIGHT//2 + 60))
        
        self.btn_play.draw(self.screen)
        self.btn_back.draw(self.screen)
    
    def _draw_mode_selection(self):
        """Draw game mode selection screen."""
        mouse_pos = pygame.mouse.get_pos()
        
        for key, base_rect in self.mode_rects.items():
            mode = GAME_MODES[key]
            is_hover = base_rect.collidepoint(mouse_pos)
            is_selected = (self.selected_mode_key == key)
            
            target_scale = 1.05 if is_hover else 1.0
            self.mode_scales[key] += (target_scale - self.mode_scales[key]) * 0.15
            current_scale = self.mode_scales[key]
            
            scaled_w = int(base_rect.width * current_scale)
            scaled_h = int(base_rect.height * current_scale)
            draw_rect = pygame.Rect(0, 0, scaled_w, scaled_h)
            draw_rect.center = base_rect.center
            
            # Draw field texture
            field_tex = assets_loader.GRAPHICS.get(mode['field_texture'])
            if field_tex:
                thumb = pygame.transform.scale(field_tex, (draw_rect.width, draw_rect.height))
                self.screen.blit(thumb, draw_rect.topleft)
            else:
                pygame.draw.rect(self.screen, GRAY, draw_rect)
            
            # Overlay
            overlay = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, draw_rect.topleft)
            
            # Border
            border_color = ORANGE if is_selected else (WHITE if is_hover else LIGHT_GRAY)
            border_width = 4 if is_selected else 2
            pygame.draw.rect(self.screen, border_color, draw_rect, border_width)
            
            # Ball icon
            ball_img = assets_loader.GRAPHICS.get(mode['ball_texture'])
            if ball_img:
                ball_img = pygame.transform.scale(ball_img, (64, 64))
                self.screen.blit(ball_img, (draw_rect.centerx - 32, draw_rect.top + 40))
            
            # Mode name
            name_surf = assets_loader.FONTS['ui'].render(mode['name'], True, WHITE)
            self.screen.blit(name_surf, (draw_rect.centerx - name_surf.get_width()//2, draw_rect.top + 120))
            
            # Description
            desc_words = mode['desc'].split(' ')
            line1 = " ".join(desc_words[:len(desc_words)//2])
            line2 = " ".join(desc_words[len(desc_words)//2:])
            
            d1 = assets_loader.FONTS['body'].render(line1, True, LIGHT_GRAY)
            d2 = assets_loader.FONTS['body'].render(line2, True, LIGHT_GRAY)
            self.screen.blit(d1, (draw_rect.centerx - d1.get_width()//2, draw_rect.top + 180))
            self.screen.blit(d2, (draw_rect.centerx - d2.get_width()//2, draw_rect.top + 210))
        
        self.btn_back.draw(self.screen)
    
    def _draw_controls(self):
        """Draw controls screen."""
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
            self.screen.blit(surf, (WIDTH//2 - surf.get_width()//2, y))
            y += 30 if line == "" else 50
        
        self.btn_back.draw(self.screen)
    
    def _draw_help(self):
        """Draw help/instructions screen."""
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
            self.screen.blit(surf, (230, y))
            y += 40
        
        self.btn_back.draw(self.screen)
    
    def _draw_playmode_selection(self):
        """Draw play mode selection screen."""
        for btn in self.btns_playmode:
            btn.draw(self.screen)
        
        info = assets_loader.FONTS['body'].render("Choose your play mode", True, LIGHT_GRAY)
        self.screen.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT//2 - 120))
        
        self.btn_back.draw(self.screen)
    
    def _draw_bot_selection(self):
        """Draw bot selection screen."""
        for btn in self.bot_buttons:
            btn.draw(self.screen)
        
        info = assets_loader.FONTS['body'].render("Select your AI opponent", True, LIGHT_GRAY)
        self.screen.blit(info, (WIDTH//2 - info.get_width()//2, 150))
        
        hint = assets_loader.FONTS['body'].render(f"Selected: {self.opponent_type}", True, ORANGE)
        self.screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 160))
        
        self.btn_back.draw(self.screen)
    
    def _handle_events(self):
        """Handle all menu events. Returns config dict when starting game, None to quit, False to continue."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            
            # Global back button handler
            if self.state in ["MODE", "CONTROLS", "HELP", "DURATION", "PLAYMODE", "BOTSELECT"]:
                if self.btn_back.check_input(event) == "BACK":
                    self._navigate_back()
                    continue
            
            # State-specific handlers
            result = self._handle_state_events(event)
            if result is not None and result is not False:  # Only propagate meaningful results
                return result
        
        return False  # Continue showing menu
    
    def _navigate_back(self):
        """Handle back navigation based on current state."""
        if self.state == "BOTSELECT":
            self.state = "PLAYMODE"
        elif self.state == "PLAYMODE":
            self.state = "MAIN"
        elif self.state == "DURATION":
            self.state = "PLAYMODE"
        else:
            self.state = "MAIN"
    
    def _handle_state_events(self, event):
        """Handle events specific to current state."""
        if self.state == "MAIN":
            return self._handle_main_events(event)
        elif self.state == "PLAYMODE":
            return self._handle_playmode_events(event)
        elif self.state == "BOTSELECT":
            return self._handle_botselect_events(event)
        elif self.state == "DURATION":
            return self._handle_duration_events(event)
        elif self.state == "MODE":
            return self._handle_mode_events(event)
        elif self.state in ["CONTROLS", "HELP"]:
            return self._handle_info_screen_events(event)
        
        return False
    
    def _handle_main_events(self, event):
        """Handle main menu events."""
        for btn in self.btns_main:
            res = btn.check_input(event)
            if res == "PLAYMODE":
                self.state = "PLAYMODE"
            elif res == "MODE":
                self.state = "MODE"
            elif res == "CONTROLS":
                self.state = "CONTROLS"
            elif res == "HELP":
                self.state = "HELP"
            elif res == "EXIT":
                return None
        return False
    
    def _handle_playmode_events(self, event):
        """Handle play mode selection events."""
        for btn in self.btns_playmode:
            res = btn.check_input(event)
            if res == "BOTSELECT":
                self.bot_buttons = self._scan_bot_models()
                self.state = "BOTSELECT"
            elif res == "2PLAYER":
                self.opponent_type = "HUMAN"
                self.state = "DURATION"
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = "MAIN"
        
        return False
    
    def _handle_botselect_events(self, event):
        """Handle bot selection events."""
        for btn in self.bot_buttons:
            res = btn.check_input(event)
            if res and res.startswith("BOT:"):
                self.opponent_type = res.split(":", 1)[1]
                self.state = "DURATION"
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = "PLAYMODE"
        
        return False
    
    def _handle_duration_events(self, event):
        """Handle duration input events."""
        start_match = False
        
        # Check button click
        if self.btn_play.check_input(event) == "PLAY":
            start_match = True
        
        # Handle keyboard input
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                start_match = True
            elif event.key == pygame.K_BACKSPACE:
                self.duration_input_text = self.duration_input_text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.state = "MAIN"
            elif event.unicode.isdigit() and len(self.duration_input_text) < 4:
                self.duration_input_text += event.unicode
        
        # Start match if triggered
        if start_match:
            return self._create_game_config()
        
        return False
    
    def _handle_mode_events(self, event):
        """Handle mode selection events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.mode_rects['SOCCER'].collidepoint(event.pos):
                self.selected_mode_key = 'SOCCER'
                if assets_loader.SOUNDS['click']:
                    assets_loader.SOUNDS['click'].play()
            elif self.mode_rects['HOCKEY'].collidepoint(event.pos):
                self.selected_mode_key = 'HOCKEY'
                if assets_loader.SOUNDS['click']:
                    assets_loader.SOUNDS['click'].play()
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = "MAIN"
        
        return False
    
    def _handle_info_screen_events(self, event):
        """Handle controls/help screen events."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = "MAIN"
        return False
    
    def _create_game_config(self):
        """Create game configuration dictionary."""
        final_config = GAME_MODES[self.selected_mode_key].copy()
        
        try:
            d = int(self.duration_input_text)
            d = max(10, min(9999, d))  # Clamp between 10 and 9999
            final_config['duration'] = d
        except ValueError:
            final_config['duration'] = 200
        
        final_config['opponent_type'] = self.opponent_type
        
        if assets_loader.SOUNDS['click']:
            assets_loader.SOUNDS['click'].play()
        
        return final_config
    
    def _scan_bot_models(self):
        """Scan for available bot models and create selection buttons."""
        buttons = []
        y_offset = 200
        center_x = WIDTH // 2
        
        # Always add basic bot first
        buttons.append(Button("Basic Bot", center_x - 150, y_offset, 300, 50, action="BOT:Basic"))
        y_offset += 60
        
        # Scan for trained models
        versions_path = os.path.join("..", "rl", "versions")
        if os.path.exists(versions_path) and os.path.isdir(versions_path):
            zip_files = [f for f in os.listdir(versions_path) if f.endswith('.zip')]
            zip_files.sort()
            
            for zip_file in zip_files:
                model_name = zip_file[:-4]
                buttons.append(Button(f"Model: {model_name}", center_x - 150, y_offset, 300, 50, 
                                     action=f"BOT:{model_name}"))
                y_offset += 60
        
        return buttons


# Legacy function for backwards compatibility
def main_menu_loop(screen, clock):
    """Legacy function - use MenuManager instead."""
    menu = MenuManager(screen, clock)
    return menu.show()