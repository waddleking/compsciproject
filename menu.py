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
    help_button = Button((res[0])/2, (res[1]/2 + int(300 * resolution_sf[1])), 200, 50, "help", small_font, color_font, color_light, color_dark)
    buttons = [start_button, campaign_button, deck_button, watch_button, help_button]

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
                if help_button.touching():
                    run_help_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, small_font, big_font, color_font, color_invalid)
                
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

    menu_button = Button(res[0] / 2, res[1] / 2 - yo, btn_w, btn_h, "menu", small_font, color_font, color_light, color_dark)
    give_up_button = Button(res[0] / 2, res[1] / 2 - yo // 3, btn_w, btn_h, "give up", small_font, color_font, color_light, color_dark)
    load_button = Button(res[0] / 2, res[1] / 2 + yo // 3, btn_w, btn_h, "load", small_font, color_font, color_light, color_dark)
    continue_button = Button(res[0] / 2, res[1] / 2 + yo, btn_w, btn_h, "continue", small_font, color_font, color_light, color_dark)
    
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
    help_button = Button(res[0]/2, res[1]/2 - int(75 * resolution_sf[1]), 500, 50, "help", small_font, color_font, color_light, color_dark)
    
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
                if help_button.touching():
                    run_help_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, small_font, big_font, color_font, color_invalid)
                
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return 0
                
        

        menu_button.draw(screen)
        help_button.draw(screen)
        pygame.display.update()

def run_help_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, medium_font, big_font, color_font, color_invalid):
    rules = """
##Basic Mechanics

#Mana
Mana is the resource used to play cards, retreat cards, and some card actions. Each turn you gain a base amount of 3 mana. Unspent mana carries over to the next turn, but your total can never exceed 6 (double the base). Certain cards like Pump generate additional mana each turn on top of this.

#Commander
Your commander sits permanently on the board and losing them loses you the game. Each commander has a unique passive ability that shapes how your deck should be played. Your commander can be attacked directly when no enemy taunt cards are blocking.

#Taunt
Taunt is an integer value on cards and commanders. When an enemy has one or more cards with taunt, you can only attack targets whose taunt value equals the highest taunt on their side. Cards with no taunt (value 0) are protected while a taunt card is alive. Cards with ignore taunt can attack any target regardless of taunt values.

#Cards
There are three zones for your cards: deck, hand, and active. Your deck is where unplayed cards wait. Your hand holds up to 8 cards at once, cards here are hidden from your opponent and do nothing passively. Your active zone holds cards that are on the board and can act, up to a maximum of 6 at once. Cards with no remaining actions this turn appear transparent.


##Gameplay

#Objective
Reduce the enemy commander's HP to 0. The commander is a valid attack target whenever no taunt cards are blocking the path to them.

#Game Start
Both players draw 5 cards. Cards played on your very first turn cannot act, even if they have haste, to prevent the first-turn advantage being too strong.


##Your Turn

#Turn Start
At the start of your turn you draw 1 card. All on turn start abilities trigger. You receive your 3 base mana (plus any carry-over, up to a max of 6). All your active cards have their actions reset to their maximum (usually 1, but Retriever resets to 2).

#Playing Cards
Click a card in your hand play it if you can afford it. Playing a card deducts its mana cost and moves it to your active zone. Cards without haste cannot act on the turn they are played. Cards with haste (Bin, Net) can act immediately. You can play cards and use actions in any order.

#Playing Spells
Spells (Bag of Gold, B52, Kamikaze, FatMan) are played like cards but do not enter the active zone. Their effect resolves immediately and the card is removed from the game. Spells ignore the 6-card active limit and can always be played regardless of board state. They do not show attack or health values.

#Retreating Cards
You can pay a card's retreat cost to return it from your active zone back to your hand. Select a card in your active zone, then press the right button (retreat) to see the cost and confirm. Retreating frees up board space.

#Card Actions
Each active card has a number of actions available per turn. Select a card in your active zone, then press the left button (action) to use it. Most cards attack an enemy target, after pressing action, click the enemy card or commander you want to target. Taunt restrictions apply. Some cards have special actions. Cards with no target needed (like Retriever) act immediately without selecting a target.
"""

    image = pygame.image.load("ui_images/examples.png")
    x_cushion = 50
    y_offset = 50
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: 
                pygame.quit() 
                
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return 0
                
            if ev.type == pygame.MOUSEWHEEL:
                y_offset += ev.y * 30
            
                
        current_background = draw_background(screen, current_background, color_background)
        # mouse = pygame.mouse.get_pos()

        s = pygame.Surface(res)  
        s.set_alpha(128)              
        s.fill((0, 0, 0))          
        screen.blit(s, (0, 0))

        #desc
        # rules = desc.split(' ')  # 2D array where each row is a list of words.
        
        max_width = res[0]-x_cushion*2
        pos = (x_cushion, y_offset)
        x, y = pos
        current_font = small_font
        for line in rules.split("\n"):
            if line.count("#") == 1:
                current_font = medium_font
                line = line.replace("#","")
            elif line.count("#") == 2:
                current_font = big_font
                line = line.replace("#","")
            else:
                current_font = small_font
            space = current_font.size(' ')[0]  # The width of a space.
            for word in line.split(" "):
                word_surface = current_font.render(word, 0, color_font)
                word_width, word_height = word_surface.get_size()
                if x + word_width >= max_width:
                    x = pos[0]  # Reset the x.
                    y += word_height  # Start on new row.
                screen.blit(word_surface, (x, y))
                x += word_width + space
            x = pos[0]  # Reset the x.
            y += word_height  # Start on new row.

        screen.blit(pygame.transform.scale(image, ((res[0]-x_cushion*4), (res[0]-x_cushion*4)*0.562)), ((x_cushion*2, res[1]*1.7+y_offset)))
        

        pygame.display.update()

