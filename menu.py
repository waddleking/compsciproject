import pygame
from random import randint, choice
from classes import Button
from draw_ui import draw_background
# from saveload import save
from math import cos, sin, pi
import card_classes
import commander_classes
from deck_manager import load_deck_data

def run_start_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid):
    """
    Description:
    The main menu, the first thing the player sees when they launch the game.
    Shows four buttons and a spinning card animation in the centre of the
    screen. The card flips between the back and a random unlocked card from the
    player's collection every half-rotation, using cos() to fake a 3D card flip.
    The background colour slowly drifts toward a random target every 400 frames.

    Parameters:
        screen (pygame.Surface): the main display surface
        res (tuple): (width, height) screen resolution
        color_light (tuple): button highlight colour
        color_dark (tuple): button shadow colour
        current_background (list): mutable [r, g, b] for the lerping background
        color_background (list): target [r, g, b] the background is drifting toward
        small_font (pygame.font.Font): font for button labels
        big_font (pygame.font.Font): font for large titles (not used here)
        color_font (tuple): text colour
        color_invalid (tuple): colour for greyed-out/invalid buttons

    Returns:
        str: "start_game", "campaign", "deck_menu", or "watch" depending on
            which button the player pressed
    """
    resolution_sf = (res[0] / 1440, res[1] / 960)

    btn_w = int(200 * resolution_sf[0])
    btn_h = int(50  * resolution_sf[1])

    start_button = Button(res[0]/2, res[1]/2 + int(75  * resolution_sf[1]), btn_w, btn_h, "free play", small_font, color_font, color_light, color_dark)
    campaign_button = Button(res[0]/2, res[1]/2, btn_w, btn_h, "campaign", small_font, color_font, color_light, color_dark)
    watch_button = Button(res[0]/2, res[1]/2 + int(150  * resolution_sf[1]), btn_w, btn_h, "AI vs AI", small_font, color_font, color_light, color_dark)
    deck_button = Button(res[0]/2, res[1]/2 + int(225 * resolution_sf[1]), btn_w, btn_h, "deck", small_font, color_font, color_light, color_dark)
    buttons = [start_button, campaign_button, deck_button, watch_button]

    # pick a random unlocked card or commander to show on the menu
    card_image = None
    try:
        data = load_deck_data()
        available = data.get("available_cards", []) + data.get("available_commanders", [])
        if available:
            chosen_name = choice(available)
            if hasattr(card_classes, chosen_name):
                obj = getattr(card_classes, chosen_name)().setup()
            else:
                obj = getattr(commander_classes, chosen_name)().setup()
            card_image = pygame.image.load(obj.image_string).convert_alpha()
    except Exception:
        card_image = None  # fall back to back-of-card if anything goes wrong

    back_image = pygame.image.load("card_images/card_back.png").convert_alpha()

    card_display_w = int(200 * resolution_sf[0])
    card_display_h = int(300 * resolution_sf[1])
    card_y_base = int(75  * resolution_sf[1])
    card_y_amp = int(25  * resolution_sf[1])

    count = -1 + 400
    dx = 3.14
    flip = False
    dy = 0
    
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: 
                pygame.quit() 

            if ev.type == pygame.MOUSEBUTTONDOWN: 
                if start_button.touching():
                    return "start_game"
                if campaign_button.touching():
                    return "campaign"
                if deck_button.touching():
                    return "deck_menu"
                if watch_button.touching():
                    return "watch"
                
        current_background = draw_background(screen, current_background, color_background)
        count += 1
        for i in range(3):
            if current_background[i] < color_background[i]:
                current_background[i] += 0.1
            elif current_background[i] > color_background[i]:
                current_background[i] -= 0.1

        if count == 400:
            color_background = [randint(100, 200), randint(100, 200), randint(100, 200)]
            count = 0

        for button in buttons:
            button.draw(screen)

        dy += 0.008
        if dx > -3.14:
            dx -= 0.01
        else:
            dx = 3.14
        
        if abs(dx) < 1.58 and abs(dx) > 1.57:
            flip = not flip

        scaled_w = (cos(dx) ** 2) ** 0.5 * card_display_w
        blit_x = (res[0] - scaled_w) / 2
        blit_y = card_y_base + card_y_amp * sin(dy)

        if flip or card_image is None:
            frame = pygame.transform.scale(back_image, (scaled_w, card_display_h))
        else:
            frame = pygame.transform.scale(card_image, (scaled_w, card_display_h))

        screen.blit(frame, (blit_x, blit_y))

        pygame.display.update()

def run_over_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, log):
    """
    Description:
    The game over screen. Shows a table of game events and chip changes from
    the log, then waits for the player to press continue. This is mostly
    left over from when the project was a different game.

    Parameters:
        screen (pygame.Surface): the main display surface
        res (tuple): (width, height) screen resolution
        color_light (tuple): button highlight colour
        color_dark (tuple): button shadow colour
        current_background (list): mutable [r, g, b] lerping background colour
        color_background (list): target background colour
        small_font (pygame.font.Font): font for table text
        big_font (pygame.font.Font): font for the "game over" title
        color_font (tuple): text colour
        log (list): list of [game_type, chips, change] entries to display

    Returns:
        int: 0 when the player presses continue
    """
    resolution_sf = (res[0] / 1440, res[1] / 960)

    btn_w = int(200 * resolution_sf[0])
    btn_h = int(50  * resolution_sf[1])

    continue_button = Button(res[0]/2, res[1] - int(300 * resolution_sf[1]), btn_w, btn_h, "continue", small_font, color_font, color_light, color_dark)

    col_offset = int(500 * resolution_sf[0])
    header_y = int(200 * resolution_sf[1])
    row_y_start = int(300 * resolution_sf[1])
    row_spacing = int(50  * resolution_sf[1])

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: 
                pygame.quit() 

            if ev.type == pygame.MOUSEBUTTONDOWN: 
                if continue_button.touching():
                    return 0
            
        current_background = draw_background(screen, current_background, color_background)

        tw1, th1 = big_font.size("game over")
        screen.blit(big_font.render("game over", True, color_font), ((res[0] - tw1) / 2, 10))
        tw1, th1 = small_font.size("chips")

        screen.blit(small_font.render("game",   True, color_font), ((res[0] - tw1) / 2 - col_offset, header_y))
        for i in range(len(log)):
            game_label = "oops"
            match log[i][0]:
                case 0: game_label = "game start"
                case 1: game_label = "blackjack"
            screen.blit(small_font.render(game_label, True, color_font), ((res[0] - tw1) / 2 - col_offset, row_y_start + i * row_spacing))

        screen.blit(small_font.render("chips",  True, color_font), ((res[0] - tw1) / 2, header_y))
        for i in range(len(log)):
            screen.blit(small_font.render(f"{log[i][1]}", True, color_font), ((res[0] - tw1) / 2, row_y_start + i * row_spacing))
        
        screen.blit(small_font.render("change", True, color_font), ((res[0] - tw1) / 2 + col_offset, header_y))
        for i in range(len(log)):
            colour = color_font if log[i][2] >= 0 else (255, 0, 0)
            screen.blit(small_font.render(f"{log[i][2]}", True, colour), ((res[0] - tw1) / 2 + col_offset, row_y_start + i * row_spacing))
        
        continue_button.draw(screen)
        pygame.display.update()


def run_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid, log):
    """
    Description:
    A mid-game pause menu with four options: return to main menu, give up,
    load a save, or continue. Draws a semi-transparent black overlay over
    whatever was on screen before so the game is still visible underneath.
    Pressing Escape also continues without clicking the button.

    Parameters:
        screen (pygame.Surface): the main display surface
        res (tuple): (width, height) screen resolution
        color_light (tuple): button highlight colour
        color_dark (tuple): button shadow colour
        current_background (list): mutable lerping background colour
        color_background (list): target background colour
        small_font (pygame.font.Font): font for button labels
        big_font (pygame.font.Font): font for large text (not used here)
        color_font (tuple): text colour
        color_invalid (tuple): colour for invalid buttons
        log (list): game log passed through but not used in this menu

    Returns:
        str or int: "menu" to go to main menu, "give up" to forfeit,
            "load" to load a save, or 0 to continue the current game
    """
    resolution_sf = (res[0] / 1440, res[1] / 960)

    btn_w = int(500 * resolution_sf[0])
    btn_h = int(50  * resolution_sf[1])
    yo = int(150 * resolution_sf[1])

    menu_button = Button(res[0] / 2, res[1] / 2 - yo,      btn_w, btn_h, "menu",     small_font, color_font, color_light, color_dark)
    give_up_button = Button(res[0] / 2, res[1] / 2 - yo // 3, btn_w, btn_h, "give up",  small_font, color_font, color_light, color_dark)
    load_button = Button(res[0] / 2, res[1] / 2 + yo // 3, btn_w, btn_h, "load",     small_font, color_font, color_light, color_dark)
    continue_button = Button(res[0] / 2, res[1] / 2 + yo,      btn_w, btn_h, "continue", small_font, color_font, color_light, color_dark)
    
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: 
                pygame.quit() 

            if ev.type == pygame.MOUSEBUTTONDOWN:
                if menu_button.touching():
                    return "menu" 
                if give_up_button.touching():
                    return "give up"
                if load_button.touching():
                    return "load"
                if continue_button.touching():
                    return 0
                
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return 0
                
        current_background = draw_background(screen, current_background, color_background)

        s = pygame.Surface(res)  
        s.set_alpha(128)              
        s.fill((0, 0, 0))          
        screen.blit(s, (0, 0))

        menu_button.draw(screen)
        load_button.draw(screen)
        give_up_button.draw(screen)
        continue_button.draw(screen)

        pygame.display.update()

def run_game_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid):
    """
    Description:
    The in-game escape menu. Just one button right now, "menu" to go to the main menu.
    Pressing Escape again dismisses the menu and returns to the game.
    Draws a semi-transparent black overlay over the current game state.
    Called by big_game when the player presses Escape.

    Parameters:
        screen (pygame.Surface): the main display surface
        res (tuple): (width, height) screen resolution
        color_light (tuple): button highlight colour
        color_dark (tuple): button shadow colour
        current_background (list): mutable lerping background colour
        color_background (list): target background colour
        small_font (pygame.font.Font): font for the button label
        big_font (pygame.font.Font): not used here
        color_font (tuple): text colour
        color_invalid (tuple): not used here

    Returns:
        str or int: "menu" if the player chose to quit to menu,
            or 0 if they pressed Escape to resume the game
    """
    resolution_sf = (res[0] / 1440, res[1] / 960)

    btn_w = int(500 * resolution_sf[0])
    btn_h = int(50  * resolution_sf[1])

    menu_button = Button(res[0] / 2, res[1] / 2 - int(150 * resolution_sf[1]), btn_w, btn_h, "menu", small_font, color_font, color_light, color_dark)
    
    # current_background = draw_background(screen, current_background, color_background)
    s = pygame.Surface(res)  
    s.set_alpha(128)              
    s.fill((0, 0, 0))          
    screen.blit(s, (0, 0))
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: 
                pygame.quit() 

            if ev.type == pygame.MOUSEBUTTONDOWN:
                if menu_button.touching():
                    return "menu" 
                
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return 0
                
        

        

        menu_button.draw(screen)

        pygame.display.update()