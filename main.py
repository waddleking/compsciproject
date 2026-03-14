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
from deck_manager import get_deck, generate_deck, generate_player_deck, load_deck_data, save_deck_data
from campaign import run_campaign_menu, run_reward_screen, generate_campaign_deck
import card_classes
import commander_classes

game_state = 0
pygame.init() 

width, height = pygame.display.Info().current_w, pygame.display.Info().current_h
res = (width, height)
screen = pygame.display.set_mode(res)

color_font = (255, 255, 255) 
color_light = (170, 170, 170) 
color_dark = (100, 100, 100) 
color_invalid = (130, 70, 70)
color_background = [randint(50, 150), randint(50, 150), randint(50, 150)]
current_background = color_background

small_font = pygame.font.SysFont('Arial', 25) 
big_font = pygame.font.SysFont('Arial', 100) 

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
    "max_hand": 7,
}

decks = [[], []]
decks[0] = get_deck()
decks[1] = generate_deck(max_deck_size)

while True:
    game_state = run_start_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid)

    if game_state == "start_game":
        decks[1] = generate_player_deck(max_deck_size)
        result = run_big_game(settings, decks, **game_settings)

    if game_state == "campaign":
        campaign_result = run_campaign_menu(screen, res, settings)
        if campaign_result != "menu":
            stage_index, stage = campaign_result

            decks[1] = generate_campaign_deck(stage, stage["deck_size"])

            result = run_big_game(
                settings, decks,
                hp=game_settings["hp"],
                mana=game_settings["mana"],
                hand_size=5,
                ai_hand_size=stage["ai_hand_size"],
                max_active=game_settings["max_active"],
                max_hand=game_settings["max_hand"],
                cost=game_settings["cost"],
                ai_mana_bonus=stage["mana_bonus"],
                stage_desc=stage["desc"],
                starting_player=1,
            )

            # player 0 is always the human player
            if result == 0:
                data = load_deck_data()
                # only advance the stage counter if this is the furthest they've reached
                if stage_index >= data.get("campaign_stage", 0):
                    data["campaign_stage"] = stage_index + 1
                    save_deck_data(data)
                run_reward_screen(screen, res, settings)
                # reload deck in case they just unlocked something
                decks[0] = get_deck()

    if game_state == "deck_menu":
        game_state = run_deck_menu(screen, res, settings, max_deck_size)
        decks[0] = get_deck()
