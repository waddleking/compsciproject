import pygame
import card_classes
import commander_classes
from classes import Button, Text
from draw_ui import draw_background
from deck_manager import load_deck_data, save_deck_data
from random import sample, choice

STAGES = [
    {
        "name": "Stage 1",
        "subtitle": "Tutorial Type",
        "desc": "Opponent: weak cards, no mana bonus",
        "card_pool": ["Amogus", "IceCube", "Bin"],
        "commander_pool": ["Alchemist"],
        "mana_bonus": 0,
        "hand_size": 4,
        "deck_size": 40,
    },
    {
        "name": "Stage 2",
        "subtitle": "Hatsune Messiah",
        "desc": "Opponent: medium cards, no mana bonus",
        "card_pool": ["Amogus", "IceCube", "Thorn", "Pump", "BagOfGold"],
        "commander_pool": ["Miku", "Jesus"],
        "mana_bonus": 0,
        "hand_size": 5,
        "deck_size": 40,
    },
    {
        "name": "Stage 3",
        "subtitle": "Malarkey in the Test Chamber",
        "desc": "Opponent: +1 mana per turn, strong cards, larger hand",
        "card_pool": ["Amogus", "Thorn", "Pump", "Hong", "Sponge",
                      "Musketeer", "Retriever"],
        "commander_pool": ["Biden", "GLaDOS"],
        "mana_bonus": 1,
        "hand_size": 6,
        "deck_size": 40,
    },
    {
        "name": "Stage 4",
        "subtitle": "Sonic x Shadow",
        "desc": "Opponent: +1 mana per turn, full card pool",
        "card_pool": ["Hong", "Sponge", "Musketeer", "Thorn", "Pump", "Snowball",
                      "Net", "Kamikaze", "B52", "BagOfGold"],
        "commander_pool": ["Sonic", "Shadow"],
        "mana_bonus": 1,
        "hand_size": 7,
        "deck_size": 40,
    },
]

REWARD_CHOICES = 3


def generate_campaign_deck(stage, deck_size):
    # builds a deck using only the cards and commanders defined for this stage
    card_classes_map = {name: getattr(card_classes, name) for name in stage["card_pool"] if hasattr(card_classes, name)}
    comm_classes_map = {name: getattr(commander_classes, name) for name in stage["commander_pool"] if hasattr(commander_classes, name)}

    deck = []

    comm_class = choice(list(comm_classes_map.values()))
    commander = comm_class()
    deck.append(commander)

    card_list = list(card_classes_map.values())
    for _ in range(deck_size - 1):
        card_obj = choice(card_list)()
        deck.append(card_obj)

    for card in deck:
        card.setup()

    return deck


def run_campaign_menu(screen, res, settings):
    # stage select screen. Returns (stage_index, stage_data) or 'menu'
    _, _, color_light, color_dark, current_background, color_background, \
        small_font, big_font, color_font, color_invalid = settings

    data = load_deck_data()
    current_stage = data.get("campaign_stage", 0)

    back_button = Button(res[0] / 2, res[1] - 70, 200, 50, "back", small_font, color_font, color_light, color_dark)

    stage_buttons = []
    for i, stage in enumerate(STAGES):
        y = res[1] / 2 - 120 + i * 80
        stage_buttons.append(Button(res[0] / 2, y, 300, 55, stage["name"], small_font, color_font, color_light, color_dark, color_invalid))

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if back_button.touching():
                    return "menu"
                for i, btn in enumerate(stage_buttons):
                    if btn.touching() and i <= current_stage:
                        return i, STAGES[i]

        current_background = draw_background(screen, current_background,
                                             color_background)

        tw, _ = big_font.size("Campaign")
        screen.blit(big_font.render("Campaign", True, color_font),
                    ((res[0] - tw) / 2, 60))

        for i, (btn, stage) in enumerate(zip(stage_buttons, STAGES)):
            unlocked = i <= current_stage
            completed = i < current_stage

            btn.draw(screen, greyed=not unlocked)

            label = "completed" if completed else ("play" if unlocked else "locked")
            label_color = (150, 255, 150) if completed else color_font
            screen.blit(
                small_font.render(label, True, label_color),
                (res[0] / 2 + 165, btn.y + 15)
            )
            sw, _ = small_font.size(stage["subtitle"])
            screen.blit(
                small_font.render(stage["subtitle"], True, color_font),
                (res[0] / 2 - sw - 165, btn.y + 15)
            )

        back_button.draw(screen)
        pygame.display.update()


def run_reward_screen(screen, res, settings):
    # gambling
    _, _, color_light, color_dark, current_background, color_background, \
        small_font, big_font, color_font, color_invalid = settings

    data = load_deck_data()

    locked_cards = [c for c in data.get("all_cards", [])
                    if c not in data.get("available_cards", [])]
    locked_commanders = [c for c in data.get("all_commanders", [])
                         if c not in data.get("available_commanders", [])]
    locked = locked_cards + locked_commanders

    # nothing left to unlock
    if not locked:
        continue_button = Button(res[0] / 2, res[1] / 2 + 100, 200, 50, "continue",
                                 small_font, color_font, color_light, color_dark)
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    if continue_button.touching():
                        return None
            current_background = draw_background(screen, current_background,
                                                 color_background)
            tw, _ = big_font.size("No new cards!")
            screen.blit(big_font.render("No new cards!", True, color_font),
                        ((res[0] - tw) / 2, res[1] / 2 - 80))
            continue_button.draw(screen)
            pygame.display.update()

    choices = sample(locked, min(REWARD_CHOICES, len(locked)))
    card_w, card_h = 125, 175
    card_g = 20

    # instantiate objects so we can call .draw()
    card_objects = []
    for name in choices:
        try:
            if hasattr(card_classes, name):
                cls = getattr(card_classes, name)
            elif hasattr(commander_classes, name):
                cls = getattr(commander_classes, name)
            else:
                continue
            obj = cls().setup()
            obj.set_w(card_w)
            obj.set_h(card_h)
            card_objects.append((name, obj))
        except AttributeError:
            pass

    total_w = len(card_objects) * (card_w + card_g) - card_g
    start_x = (res[0] - total_w) / 2

    select_buttons = []
    for i, (name, obj) in enumerate(card_objects):
        x = start_x + i * (card_w + card_g)
        y = res[1] / 2 - card_h / 2
        obj.x, obj.y = x, y
        select_buttons.append(
            Button(x + card_w / 2, y + card_h + card_g, card_w, 35, "pick",
                   small_font, color_font, color_light, color_dark)
        )

    chosen = None

    while chosen is None:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                for i, btn in enumerate(select_buttons):
                    if btn.touching():
                        chosen = card_objects[i][0]

        current_background = draw_background(screen, current_background,
                                             color_background)

        tw, _ = big_font.size("Pick a card to unlock")
        screen.blit(big_font.render("Pick a card to unlock", True, color_font),
                    ((res[0] - tw) / 2, 80))

        for (name, obj), btn in zip(card_objects, select_buttons):
            obj.draw(screen)
            btn.draw(screen)

        pygame.display.update()

    # write the unlock to JSON
    if chosen in locked_cards:
        data["available_cards"].append(chosen)
    elif chosen in locked_commanders:
        data["available_commanders"].append(chosen)
    save_deck_data(data)

    return chosen
