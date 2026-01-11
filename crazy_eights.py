import pygame
from draw_ui import draw_chips_ui, draw_card_ui, draw_win_fail_screen, draw_background
from betting import run_bets
from classes import Button, Card
from random import randint
from menu import run_menu
from setup import setup_cards

def run_crazy_eights(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid, cards, chips, quota, log):
    button_available = False #0 for cards
    players = randint(2, 2)
    player = 0
    result = None
    overlay_y = -res[1]
    overlay_chips = chips
    turn = 0
    card_w, card_h, gap = 100, 150, 10
    available_cards = []

    cards_array, current_card = start_crazy_eights(res, cards, players, card_w, card_h)
    last_current_card = current_card
    deck_pos = ((res[0]-card_w)/2-150, (res[1]-card_h)/2)

    while True:
        mouse = pygame.mouse.get_pos()
        if len(cards) < 5:
            cards = setup_cards(res)
    
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: 
                pygame.quit() 
            #button 1
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if turn%players == player: 
                    
                    for card in cards_array[player]:
                        if card.x <= mouse[0] <= card.x+(card_w) and card.y <= mouse[1] <= card.y+(card_h) and card in available_cards:
                            last_current_card = current_card
                            current_card = card
                            current_card.desired_x, current_card.desired_y = (res[0]-card_w)/2, (res[1]-card_h)/2
                            
                            cards_array[player].remove(card)
                            turn += 1
                    if deck_pos[0] <= mouse[0] <= deck_pos[0]+(card_w) and deck_pos[1] <= mouse[1] <= deck_pos[1]+(card_h):
                        random = randint(0, len(cards) - 1)
                        cards_array[player].append(cards[random].set_x(deck_pos[0]).set_y(deck_pos[1]).set_desired_y(res[1]-200))
                        cards.pop(random)
                        available_cards = []
                        for card in cards_array[turn%players]:
                            if card.value.split("_")[0] == current_card.value.split("_")[0] or card.value.split("_")[-1] == current_card.value.split("_")[-1]:
                                available_cards.append(card)
                        if len(available_cards) == 0:
                            turn += 1

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
                    if chips >= quota or chips == 0:
                        return chips
                    
                    result = None
                    overlay_y = -res[1]
                    cards_array, current_card = start_crazy_eights(res, cards, players, card_w, card_h)
        
        current_background = draw_background(screen, current_background, color_background)

        #middle card
        screen.blit(pygame.transform.scale(pygame.image.load(f"cards/back.png").convert_alpha(), (card_w, card_h)), (deck_pos))

        if last_current_card.x != last_current_card.desired_x:
            distance = last_current_card.desired_x - last_current_card.x
            if distance**2 < 50:
                last_current_card.x = last_current_card.desired_x
            else:
                last_current_card.x += (distance)/5
            
        if last_current_card.y != last_current_card.desired_y:
            distance = last_current_card.desired_y - last_current_card.y
            if distance**2 < 50:
                last_current_card.y = last_current_card.desired_y
            else:
                last_current_card.y += (distance)/5
        screen.blit(pygame.transform.scale(pygame.image.load(f"cards/{last_current_card.value}.png").convert_alpha(), (card_w, card_h)), ((last_current_card.x, last_current_card.y)))

        if current_card.x != current_card.desired_x:
            distance = current_card.desired_x - current_card.x
            if distance**2 < 50:
                current_card.x = current_card.desired_x
            else:
                current_card.x += (distance)/5
            
        if current_card.y != current_card.desired_y:
            distance = current_card.desired_y - current_card.y
            if distance**2 < 50:
                current_card.y = current_card.desired_y
            else:
                current_card.y += (distance)/5
        screen.blit(pygame.transform.scale(pygame.image.load(f"cards/{current_card.value}.png").convert_alpha(), (card_w, card_h)), ((current_card.x, current_card.y)))

        available_cards = []
        available_cards_suit = {"clubs": 0, "diamonds": 0, "hearts":0, "spades": 0}
        
        for card in cards_array[turn%players]:
            if card.value.split("_")[0] == current_card.value.split("_")[0] or card.value.split("_")[-1] == current_card.value.split("_")[-1]:
                available_cards.append(card)
                available_cards_suit[card.value.split("_")[-1]] += 1

        
        
        # for card in cards_array[turn%players]:
        #     if card.value.split("_")[-1] == current_card.value.split("_")[-1]:
        #         available_cards.append(card)
                
        #ai
        if turn%players != player and current_card.x == current_card.desired_x and current_card.y == current_card.desired_y:
            if len(available_cards) == 0:
                random = randint(0, len(cards) - 1)
                cards_array[turn%players].append(cards[random].set_desired_y(50).set_hidden(True))
                cards.pop(random)
                available_cards = []
                for card in cards_array[turn%players]:
                    if card.value.split("_")[0] == current_card.value.split("_")[0] or card.value.split("_")[-1] == current_card.value.split("_")[-1]:
                        available_cards.append(card)
                if len(available_cards) == 0:
                    turn += 1
                
            else:

                available_cards_suit = sorted(available_cards_suit, key=available_cards_suit.get, reverse=True)

                for card in available_cards:
                    if card.value.split("_")[-1] != available_cards_suit[0]:
                        available_cards.remove(card)
                #random = randint(0, len(available_cards) - 1)
                card = available_cards[0]
                last_current_card = current_card
                current_card = card
                current_card.desired_x, current_card.desired_y = (res[0]-card_w)/2, (res[1]-card_h)/2
                
                cards_array[turn%players].remove(card)
                turn += 1
                

        for card in cards_array[player]:
            if card.x <= mouse[0] <= card.x+(card_w) and card.y <= mouse[1] <= card.y+(card_h) and card in available_cards:
                card.desired_y = res[1]-250
            else:
                card.desired_y = res[1]-200
        
        if len(cards_array) > 0:
            if draw_card_ui(screen, cards_array, res, card_w, card_h, gap):
                for i in range(players):
                    if len(cards_array[i]) == 0:
                        result = f"player {i} wins"

                    if result != None:
                        button_available = True

        if result != None:
            draw_win_fail_screen(screen, result, overlay_y, big_font, res)
            if overlay_y < 0: 
                overlay_y -= (overlay_y/5)
                overlay_y += 5
            else:
                overlay_y = 0

        pygame.display.update()


def start_crazy_eights(res, cards, players, card_w, card_h):
    if players == 2:
        cards_array = [[],[]]
        for i in range(7):
            random = randint(0, len(cards) - 1)
            cards_array[0].append(cards[random].set_y(res[1]-200).set_x(res[0]/2))
            cards.pop(random)

        for i in range(7):
            random = randint(0, len(cards) - 1)
            cards_array[1].append(cards[random].set_y(50).set_x(res[0]/2).set_hidden(True))
            cards.pop(random)
    
    random = randint(0, len(cards) - 1)
    current_card = cards[random].set_y((res[1]-150)/2).set_x((res[0]-100)/2)
    current_card.desired_x, current_card.desired_y = (res[0]-card_w)/2, (res[1]-card_h)/2
    cards.pop(random)
    
    # for i in range(len(cards_array)):
    #     cards_array[i] = cards_array[i].set_y()

    return cards_array, current_card