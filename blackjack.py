import pygame
from draw_ui import draw_chips_ui, draw_card_ui, draw_win_fail_screen, draw_background
from betting import run_bets
from classes import Button, Card
from random import randint
from menu import run_menu
from setup import setup_cards

def run_blackjack(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid, cards, chips, quota, log):
    hit_button = Button(res[0]/2+300, res[1]-100, 200, 50, "hit", small_font, color_font, color_light, color_dark)
    stay_button = Button(res[0]/2-300, res[1]-100, 200, 50, "stay", small_font, color_font, color_light, color_dark)
    button_available = False #0 is no button, 1 is betting button, 2 is blackjack button
    game_state = "b"
    result = None
    overlay_y = -res[1]
    overlay_chips = chips
    FPS = 60
    clock = pygame.time.Clock()

    cards_array = start_blackjack(res, cards)

    while True:
        if len(cards) < 5:
            cards = setup_cards(res)
        
        if game_state == "b":
            bet = run_bets(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid, chips, quota, 10, 100, 1000)
            chips -= bet
            game_state = "p"
        else:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: 
                    pygame.quit() 

                #button 1
                if ev.type == pygame.MOUSEBUTTONDOWN: 
                    if button_available == True:
                        if hit_button.touching():
                            random = randint(0, len(cards) - 1)
                            cards_array[0].append(cards[random].set_y(res[1]-500))
                            cards.pop(random)
                            button_available = False

                        if stay_button.touching():
                            result = "stay"
                            cards_array[1][0].set_hidden(False)

                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        option = run_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid, log)
                        if option == "give up":
                            result == "epic fail"
                            chips = 0
                            overlay_y = 0
                        elif option == "load":
                            return option
                        elif option == "menu":
                            return option

                if ev.type == pygame.KEYDOWN or ev.type == pygame.MOUSEBUTTONDOWN: 
                        #restart
                    if overlay_y == 0:
                        if result == "player wins" or result == "dealer bust":
                            chips += bet*2
                        if result == "push":
                            chips += bet
                        if result == "natural blackjack":
                            chips += round(bet*2.5)

                        if chips >= quota or chips == 0:
                            return chips
                        
                        game_state = "b"
                        result = None
                        overlay_y = -res[1]
                        cards_array = start_blackjack(res, cards)
                    
            current_background = draw_background(screen, current_background, color_background)

            #button 1
            if button_available == True:
                hit_button.draw(screen)
                stay_button.draw(screen)

            #calc hand scores
            dealer_value = 0
            for i in cards_array[1]:
                if i.value[0].isnumeric():
                    dealer_value += int(i.value.split("_")[0])
                else:
                    match i.value.split("_")[0]:
                        case "jack":
                            dealer_value += 10
                        case "queen":
                            dealer_value += 10
                        case "king":
                            dealer_value += 10
                        case "ace":
                            dealer_value += 11
                            if dealer_value > 21:
                                dealer_value -= 10
            for i in range([i.value.split("_")[0] for i in cards_array[1]].count("ace")):
                if dealer_value > 21:
                    dealer_value -= 10
                    
            hand_value = 0
            for i in cards_array[0]:
                if i.value[0].isnumeric():
                    hand_value += int(i.value.split("_")[0])
                else:
                    match i.value.split("_")[0]:
                        case "jack":
                            hand_value += 10
                        case "queen":
                            hand_value += 10
                        case "king":
                            hand_value += 10
                        case "ace":
                            hand_value += 11
            
            for i in range([i.value.split("_")[0] for i in cards_array[0]].count("ace")):
                if hand_value > 21:
                    hand_value -= 10

            overlay_chips = draw_chips_ui(screen, res, small_font, big_font, color_font, chips, quota, overlay_chips)
            if len(cards_array) > 0:
                if draw_card_ui(screen, cards_array, res, 200, 300, 50):
                    if hand_value == 21 and len(cards_array[0]) == 2:
                        result = "natural blackjack"
                    elif hand_value > 21:
                        result = "player bust"
                        
                    elif dealer_value > 21:
                        result = "dealer bust"

                    elif dealer_value >= 17 and result != None:
                        if hand_value > dealer_value:
                            result = "player wins"

                        if hand_value < dealer_value:
                            result = "dealer wins"
                        
                        if hand_value == dealer_value:
                            result = "push"
                    
                    elif dealer_value < 17 and result != None:
                        random = randint(0, len(cards) - 1)
                        cards_array[1].append(cards[random].set_y(200))
                        cards.pop(random)

                    else:
                        button_available = True

            if result != None and result != "stay":
                draw_win_fail_screen(screen, result, overlay_y, big_font, res)
                if overlay_y < 0: 
                    overlay_y -= (overlay_y/5)
                    overlay_y += 5
                else:
                    overlay_y = 0

        pygame.display.update()
        clock.tick(FPS)

def start_blackjack(res, cards):
    cards_array = [[],[]]
    for i in range(2):
        random = randint(0, len(cards) - 1)
        cards_array[0].append(cards[random].set_y(res[1]-500))
        cards.pop(random)
    
    random = randint(0, len(cards) - 1)
    cards_array[1].append(cards[random].set_y(200).set_hidden(True))
    cards.pop(random)
    random = randint(0, len(cards) - 1)
    cards_array[1].append(cards[random].set_y(200))
    cards.pop(random)

    return cards_array