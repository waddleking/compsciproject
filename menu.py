import pygame
from random import randint, choice
from classes import Button
from draw_ui import draw_background
from saveload import save
from math import cos, sin, pi
from random import randint

def run_start_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid):

    start_button    = Button(res[0]/2, (res[1]/2),      200, 50, "start",    small_font, color_font, color_light, color_dark)
    campaign_button = Button(res[0]/2, (res[1]/2+75),   200, 50, "campaign", small_font, color_font, color_light, color_dark)
    deck_button     = Button(res[0]/2, (res[1]/2+150),  200, 50, "deck",     small_font, color_font, color_light, color_dark)
    buttons = [start_button, campaign_button, deck_button]

    count = -1 + 400

    card_file = choice(["red_joker", "black_joker"])
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
                
        current_background = draw_background(screen, current_background, color_background)
        count += 1
        for i in range(3):
            if current_background[i] < color_background[i]:
                current_background[i] += 0.1
            elif current_background[i] > color_background[i]:
                current_background[i] -= 0.1

        if count == 400:
            color_background = [randint(100,200), randint(100,200), randint(100,200)]
            count = 0

        mouse = pygame.mouse.get_pos()

        for button in buttons:
            button.draw(screen)

        dy += 0.008
        if dx > - 3.14:
            dx -= 0.01
        else:
            dx = 3.14
        
        if abs(dx) < 1.58 and abs(dx) > 1.57:
            if flip == True: flip = False
            else: flip = True

        if flip == False:
            screen.blit(pygame.transform.scale(pygame.image.load(f"cards/{card_file}.png").convert_alpha(), ((cos(dx)**2)**0.5 * 200, 300)), (((res[0]-(cos(dx)**2)**0.5 * 200)/2, 175+25*sin(dy))))
        else:
            screen.blit(pygame.transform.scale(pygame.image.load(f"cards/back.png").convert_alpha(), ((cos(dx)**2)**0.5 * 200, 300)), (((res[0]-(cos(dx)**2)**0.5 * 200)/2, 175+25*sin(dy))))

        pygame.display.update()

def run_over_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, log):
    continue_button = Button(res[0]/2, (res[1]-300), 200, 50, "continue", small_font, color_font, color_light, color_dark)
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: 
                pygame.quit() 

            if ev.type == pygame.MOUSEBUTTONDOWN: 
                if continue_button.touching():
                    return 0
            
        current_background = draw_background(screen, current_background, color_background)

        tw1, th1 = big_font.size("game over")
        screen.blit(big_font.render("game over", True, color_font), ((res[0]-tw1)/2, 10))
        tw1, th1 = small_font.size("chips")

        screen.blit(small_font.render(f"game", True, color_font), ((res[0]-tw1)/2-500, 200))
        for i in range(len(log)):
            game = "oops"
            match log[i][0]:
                case 0:
                    game = "game start"
                case 1:
                    game = "blackjack"
            screen.blit(small_font.render(f"{game}", True, color_font), ((res[0]-tw1)/2-500, (i*50)+300))

        screen.blit(small_font.render(f"chips", True, color_font), ((res[0]-tw1)/2, 200))
        for i in range(len(log)):
            screen.blit(small_font.render(f"{log[i][1]}", True, color_font), ((res[0]-tw1)/2, (i*50)+300))
        
        screen.blit(small_font.render(f"change", True, color_font), ((res[0]-tw1)/2+500, 200))
        for i in range(len(log)):
            if log[i][2] >= 0:
                screen.blit(small_font.render(f"{log[i][2]}", True, color_font), ((res[0]-tw1)/2+500, (i*50)+300))
            else:
                screen.blit(small_font.render(f"{log[i][2]}", True, (255,0,0)), ((res[0]-tw1)/2+500, (i*50)+300))
        
        continue_button.draw(screen)
        pygame.display.update()

def run_transition_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, quota, quota_mult, log):
    continue_button = Button(res[0]/2, (res[1]-300), 500, 50, "continue", small_font, color_font, color_light, color_dark)
    save_button = Button((res[0])/2, (res[1]-225), 500, 50, "save", small_font, color_font, color_light, color_dark)
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: 
                pygame.quit() 

            if ev.type == pygame.MOUSEBUTTONDOWN: 
            
                if continue_button.touching():
                    return 0
            
                if save_button.touching():
                    save(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, log)
            
        current_background = draw_background(screen, current_background, color_background)  

        text = "quota met!"
        tw1, th1 = big_font.size(text)
        screen.blit(big_font.render(text, True, color_font), ((res[0]-tw1)/2, 50))

        text = "old quota: "+str(quota)
        tw1, th1 = small_font.size(text)
        screen.blit(small_font.render(text, True, color_font), ((res[0]-tw1)/2, 350))

        text = "new quota: "+str(quota*quota_mult)
        tw1, th1 = small_font.size(text)
        screen.blit(small_font.render(text, True, color_font), ((res[0]-tw1)/2, 450))
        
        continue_button.draw(screen)
        save_button.draw(screen)
        pygame.display.update()

def run_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid, log):
    menu_button = Button((res[0])/2, (res[1]/2-150), 500, 50, "menu", small_font, color_font, color_light, color_dark)
    give_up_button = Button((res[0])/2, (res[1]/2-50), 500, 50, "give up", small_font, color_font, color_light, color_dark)
    load_button = Button((res[0])/2, (res[1]/2+50), 500, 50, "load", small_font, color_font, color_light, color_dark)
    continue_button = Button((res[0])/2, (res[1]/2+150), 500, 50, "continue", small_font, color_font, color_light, color_dark)
    
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
    menu_button = Button((res[0])/2, (res[1]/2-150), 500, 50, "menu", small_font, color_font, color_light, color_dark)
    
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
                
        current_background = draw_background(screen, current_background, color_background)

        s = pygame.Surface(res)  
        s.set_alpha(128)              
        s.fill((0, 0, 0))          
        screen.blit(s, (0, 0))

        menu_button.draw(screen)

        pygame.display.update()