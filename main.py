import pygame
from menu import run_start_menu, run_over_menu, run_transition_menu
from blackjack import run_blackjack
from crazy_eights import run_crazy_eights
from big_game import run_big_game
from random import randint, choice
from saveload import load
from classes import Card
from setup import setup_game, setup_cards
from deck_menu import run_deck_menu
from deck_manager import get_deck, generate_deck
import card_classes
import commander_classes

game_state = 0
pygame.init() 

width, height = pygame.display.Info().current_w, pygame.display.Info().current_h
res = (width, height)
screen = pygame.display.set_mode(res)

# white 
color_font = (255, 255, 255) 

# light 
color_light = (170, 170, 170) 

# ddark
color_dark = (100, 100, 100) 

color_invalid = (130, 70, 70)

#background
color_background = (128, 212, 121)
color_background = [randint(50, 150), randint(50, 150), randint(50, 150)]
current_background = color_background

# font
small_font = pygame.font.SysFont('Arial',25) 
big_font = pygame.font.SysFont('Arial',100) 

quota_mult = 2

settings = [
    screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid
]

max_deck_size = 40

game_settings = {
    "hp": 20,
    "mana": 3,
    "hand_size": 5,
    "cost": 1,
    "max_active": 6,
}

decks = [
    [],
    [],
]

#load decks and random ai deck
decks[0] = get_deck()

# pick a random class, then () to make a new one
decks[1] = generate_deck(max_deck_size)

while True:
    game_state = run_start_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid)
    if game_state == "start_game":
        decks[1] = generate_deck(max_deck_size)
        result = run_big_game(settings, decks, **game_settings)
    if game_state == "deck_menu":
        game_state = run_deck_menu(screen, res, settings, max_deck_size)
        decks[0] = get_deck()

#old other stuff
while False:
    if game_state == 0:
        chips, quota, game_state, stats = setup_game()
        cards = setup_cards(res)
        game_state = run_start_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid, cards)
    
    if game_state == 1:
        chips = run_blackjack(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid, cards, chips, quota, stats)
    if game_state == 2:
        chips = run_crazy_eights(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid, cards, chips, quota, stats)
    if game_state == 3:
        chips = run_big_game(settings, cards, chips, quota, stats, deck, **game_settings)
    
    if chips == "load" or game_state == "load":
        
        (chips, game_state)
        chips, quota, game_state, stats = setup_game(*load(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font))
        print(chips, quota, game_state, stats)
    elif chips == "menu":
        game_state = 0
    # print(stats)
    else:
        stats.append([game_state, chips, chips-stats[-1][1]])
    
        if chips == 0:
            game_state = run_over_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, stats)
            chips, quota, game_state, stats = setup_game()
        else:
            run_transition_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, quota, quota_mult, stats)
            quota *= 2
    color_background = [randint(100,200), randint(100,200), randint(100,200)]