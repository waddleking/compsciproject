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
        "card_pool": ["Amogus", "IceCube", "Skeleton"],
        "commander_pool": ["Alchemist"],
        "mana_bonus": 0,
        "ai_hand_size": 4,
        "deck_size": 40,
    },
    {
        "name": "Stage 2",
        "subtitle": "Hatsune Messiah",
        "desc": "Opponent: medium cards",
        "card_pool": ["Amogus", "IceCube", "Thorn", "Pump", "BagOfGold"],
        "commander_pool": ["Miku", "Jesus"],
        "mana_bonus": 0,
        "ai_hand_size": 5,
        "deck_size": 40,
    },
    {
        "name": "Stage 3",
        "subtitle": "Malarkey in the Test Chamber",
        "desc": "Opponent: +1 mana per turn, strong cards",
        "card_pool": ["Amogus", "Thorn", "Pump", "Hong", "Sponge", "Musketeer", "Retriever"],
        "commander_pool": ["Biden", "GLaDOS"],
        "mana_bonus": 1,
        "ai_hand_size": 6,
        "deck_size": 40,
    },
    {
        "name": "Stage 4",
        "subtitle": "Sonic x Shadow",
        "desc": "Opponent: +1 mana per turn",
        "card_pool": ["Hong", "Sponge", "Musketeer", "Thorn", "Pump", "Snowball", "Net", "Kamikaze", "BagOfGold"],
        "commander_pool": ["Sonic", "Shadow"],
        "mana_bonus": 1,
        "ai_hand_size": 7,
        "deck_size": 40,
    },
    {
        "name": "Stage 5",
        "subtitle": "Sleeper No More",
        "desc": "Opponent: +1 mana per turn",
        "card_pool": ["Pump", "IceCube", "Thorn", "Hong", "BagOfGold", "Medic", "Kamikaze"],
        "commander_pool": ["Biden"],
        "mana_bonus": 1,
        "ai_hand_size": 7,
        "deck_size": 40,
    },
    {
        "name": "Stage 6",
        "subtitle": "You Can Call Me Miku",
        "desc": "Opponent: +1 mana per turn",
        "card_pool": ["Skeleton", "IceCube", "BagOfGold", "Bin", "Retriever", "Amogus", "Thorn"],
        "commander_pool": ["Miku"],
        "mana_bonus": 1,
        "ai_hand_size": 7,
        "deck_size": 40,
    },
    {
        "name": "Stage 7",
        "subtitle": "Edward",
        "desc": "Opponent: +2 mana per turn",
        "card_pool": ["BagOfGold", "Net", "B52", "Kamikaze", "IceCube", "Thorn", "Hong", "Pump"],
        "commander_pool": ["Alchemist"],
        "mana_bonus": 2,
        "ai_hand_size": 8,
        "deck_size": 40,
    },
    {
        "name": "Stage 8",
        "subtitle": "The Cake is a Lie",
        "desc": "Opponent: +2 mana per turn",
        "card_pool": ["Amogus", "Skeleton", "Thorn", "IceCube", "Musketeer", "B52", "BagOfGold", "Retriever", "Hong"],
        "commander_pool": ["GLaDOS"],
        "mana_bonus": 2,
        "ai_hand_size": 8,
        "deck_size": 40,
    },
    {
        "name": "Stage 9",
        "subtitle": "Gotta Go Fast",
        "desc": "Opponent: +3 mana per turn",
        "card_pool": ["Amogus", "Hong", "Musketeer", "Sponge", "Snowball", "Kamikaze", "Net", "Thorn"],
        "commander_pool": ["Sonic"],
        "mana_bonus": 3,
        "ai_hand_size": 8,
        "deck_size": 40,
    },
    {
        "name": "Stage 10",
        "subtitle": "Chaos Control",
        "desc": "Opponent: +3 mana per turn",
        "card_pool": ["Hong", "Musketeer", "Sponge", "Thorn", "Pump", "Kamikaze", "Net", "B52", "BagOfGold", "Amogus", "Snowball", "IceCube"],
        "commander_pool": ["Shadow"],
        "mana_bonus": 3,
        "ai_hand_size": 9,
        "deck_size": 40,
    },
]

REWARD_CHOICES = 3


#  card role classification
# every card gets a role so generate_campaign_deck can fill decks
# in sensible ratios rather than pure chaos
CARD_ROLES = {
    "Pump":      "economy",
    "BagOfGold": "economy",
    "Skeleton":  "attack",
    "Amogus":    "attack",
    "Hong":      "attack",
    "Musketeer": "attack",
    "Sponge":    "attack",
    "Snowball":  "attack",
    "IceCube":   "taunt",
    "Thorn":     "taunt",
    "Bin":       "utility",
    "Retriever": "utility",
    "Net":       "utility",
    "Medic":     "utility",
    "Kamikaze":  "finisher",
    "B52":       "aoe",
}

# per-stage deck compositions
# keys are roles from CARD_ROLES
# counts are targets - if a role doesnt have enough cards in the pool
# the rest gets random-filled from whatever is available
# key design principle: every deck needs ENOUGH TAUNT to protect its fragile cards
# and ENOUGH ATTACKERS to not just sit there doing nothing
STAGE_COMPOSITIONS = [
    # skeleton is cheap early pressure, amogus is the reliable body, icecube protects
    {"attack": 20, "taunt": 18},

    # bag of gold enables pump + amogus on the same turn
    # the thorn count is high because miku makes them tankier
    {"taunt": 16, "attack": 12, "economy": 10},

    # need lots of taunt (thorn) to protect pumps while the economy builds
    # retriever draws into more pumps and hongs
    # musketeer is the secret weapon for killing things behind the player's taunt
    {"economy": 14, "taunt": 14, "attack": 8, "utility": 4},

    # sonic needs attackers to use the haste bonus on
    # thorn protects snowball/sponge while they grow
    # net + kamikaze is the combo win condition so we want both
    {"attack": 18, "taunt": 10, "finisher": 5, "utility": 4, "economy": 4},

    # the ratio here is specifically: establish 2-3 pumps behind 2-3 thorns
    # then medic keeps commander alive while the economy snowballs
    # hong and kamikaze are the actual damage
    {"economy": 16, "taunt": 14, "utility": 5, "attack": 4},

    # almost all cards are cost 1 to maximize miku triggers
    # icecube + miku = 4hp taunt wall for 1 mana which is absurd
    # skeleton + miku = 3hp 1/1 that survives thorn retaliation
    # bin and retriever keep the hand full for more miku triggers
    {"taunt": 18, "attack": 12, "utility": 10},

    # bag of gold = draw + mana (best spell in the game with alchemist)
    # lots of spells (bag, b52, kamikaze) to trigger alchemist draws
    # taunt wall (icecube, thorn) to survive long enough for the engine to set up
    # hong as the big finisher once mana is established
    # the economy count reflects bags of gold being key to the alchemist combo
    {"economy": 14, "taunt": 12, "aoe": 6, "finisher": 4, "attack": 4},

    # lots of cheap stuff that will die and trigger glados draws
    # skeleton, amogus, musketeer all die easily = lots of draws
    # b52 clears 1hp cards including our own weak ones = draw triggers
    # thorn retaliation kills both enemy and sometimes our thorn = draw trigger
    # icecube provides the taunt wall to not just immediately collapse
    {"attack": 16, "taunt": 10, "aoe": 6, "utility": 6, "economy": 3},

    # maximum attackers because they all swing the turn they land
    # thorn is still critical - protects sponge/snowball while sonic gives them haste
    # net + hong = the dream turn: play net, free play hong, hong attacks immediately
    # kamikaze is the panic button when we cant get through
    {"attack": 22, "taunt": 8, "finisher": 4, "utility": 4},

    # shadow needs kills to generate mana so we need things that can actually kill stuff
    # hong reliably kills most things in one hit = reliable shadow trigger
    # musketeer kills engine cards through taunt = reliable shadow trigger
    # thorn wall protects sponge/snowball which then become massive threats
    # b52 can wipe 1hp boards = multiple kills = multiple shadow mana triggers
    # net + kamikaze = win condition if the board gets clogged with taunt
    # bag of gold for chain plays when we have lots of mana from shadow triggers
    {"attack": 16, "taunt": 10, "economy": 6, "finisher": 4, "aoe": 4, "utility": 4},
]

# max copies of any single card per deck
MAX_COPIES_PER_CARD = 10


def generate_campaign_deck(stage, deck_size):
    stage_index = next(
        (i for i, s in enumerate(STAGES) if s["name"] == stage["name"]),
        None
    )
    composition = STAGE_COMPOSITIONS[stage_index] if stage_index is not None else {}

    card_classes_map = {
        name: getattr(card_classes, name)
        for name in stage["card_pool"]
        if hasattr(card_classes, name)
    }
    comm_classes_map = {
        name: getattr(commander_classes, name)
        for name in stage["commander_pool"]
        if hasattr(commander_classes, name)
    }

    # 1. pick commander
    comm_class = choice(list(comm_classes_map.values()))
    deck = [comm_class()]

    # 2. group available cards by role
    role_pools = {}
    for name, cls in card_classes_map.items():
        role = CARD_ROLES.get(name, "other")
        role_pools.setdefault(role, [])
        role_pools[role].append(name)

    full_pool = list(card_classes_map.keys())
    target_cards = deck_size - 1
    card_counts = {}

    def add_card(name):
        card_counts[name] = card_counts.get(name, 0) + 1
        deck.append(card_classes_map[name]())

    # 3. fill role slots in composition order
    for role, target in composition.items():
        available = [n for n in role_pools.get(role, [])
                     if card_counts.get(n, 0) < MAX_COPIES_PER_CARD]
        if not available:
            continue
        for _ in range(target):
            if len(deck) - 1 >= target_cards:
                break
            eligible = [n for n in available
                        if card_counts.get(n, 0) < MAX_COPIES_PER_CARD]
            if not eligible:
                break
            add_card(choice(eligible))

    # 4. random fill for remaining slots
    while len(deck) - 1 < target_cards:
        eligible = [n for n in full_pool
                    if card_counts.get(n, 0) < MAX_COPIES_PER_CARD]
        if not eligible:
            eligible = full_pool
        add_card(choice(eligible))

    # 5. setup all objects
    for card in deck:
        card.setup()

    return deck


def run_campaign_menu(screen, res, settings):
    _, _, color_light, color_dark, current_background, color_background, \
        small_font, big_font, color_font, color_invalid = settings

    resolution_sf = (res[0] / 1440, res[1] / 960)

    data = load_deck_data()
    current_stage = data.get("campaign_stage", 0)

    btn_w  = int(300 * resolution_sf[0])
    btn_h  = int(55  * resolution_sf[1])
    btn_gap = int(70 * resolution_sf[1])

    back_btn_w = int(200 * resolution_sf[0])
    back_btn_h = int(50  * resolution_sf[1])
    back_button = Button(res[0] / 2, res[1] - back_btn_h - int(20 * resolution_sf[1]),
                         back_btn_w, back_btn_h, "back",
                         small_font, color_font, color_light, color_dark)

    total_h = len(STAGES) * btn_gap - (btn_gap - btn_h)
    top_y   = (res[1] - total_h) / 2 + int(40 * resolution_sf[1])

    stage_buttons = []
    for i, stage in enumerate(STAGES):
        y = top_y + i * btn_gap
        stage_buttons.append(
            Button(res[0] / 2, y, btn_w, btn_h, stage["name"],
                   small_font, color_font, color_light, color_dark, color_invalid)
        )

    label_x_right  = res[0] / 2 + btn_w / 2 + int(15 * resolution_sf[0])
    label_x_left_base = res[0] / 2 - btn_w / 2 - int(15 * resolution_sf[0])

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

        current_background = draw_background(screen, current_background, color_background)

        tw, _ = big_font.size("Campaign")
        screen.blit(big_font.render("Campaign", True, color_font),
                    ((res[0] - tw) / 2, int(20 * resolution_sf[1])))

        for i, (btn, stage) in enumerate(zip(stage_buttons, STAGES)):
            unlocked  = i <= current_stage
            completed = i < current_stage

            btn.draw(screen, greyed=not unlocked)

            label       = "completed" if completed else ("play" if unlocked else "locked")
            label_color = (150, 255, 150) if completed else color_font
            screen.blit(small_font.render(label, True, label_color),
                        (label_x_right, btn.y + (btn_h - small_font.size(label)[1]) // 2))

            sw, _ = small_font.size(stage["subtitle"])
            screen.blit(small_font.render(stage["subtitle"], True, color_font),
                        (label_x_left_base - sw,
                         btn.y + (btn_h - small_font.size(stage["subtitle"])[1]) // 2))

        back_button.draw(screen)
        pygame.display.update()


def run_reward_screen(screen, res, settings):
    _, _, color_light, color_dark, current_background, color_background, \
        small_font, big_font, color_font, color_invalid = settings

    resolution_sf = (res[0] / 1440, res[1] / 960)

    data = load_deck_data()

    locked_cards = [c for c in data.get("all_cards", [])
                    if c not in data.get("available_cards", [])]
    locked_commanders = [c for c in data.get("all_commanders", [])
                         if c not in data.get("available_commanders", [])]
    locked = locked_cards + locked_commanders

    if not locked:
        continue_button = Button(
            res[0] / 2, res[1] / 2 + int(100 * resolution_sf[1]),
            int(200 * resolution_sf[0]), int(50 * resolution_sf[1]),
            "continue", small_font, color_font, color_light, color_dark)
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    if continue_button.touching():
                        return None
            current_background = draw_background(screen, current_background, color_background)
            tw, _ = big_font.size("No new cards!")
            screen.blit(big_font.render("No new cards!", True, color_font),
                        ((res[0] - tw) / 2, res[1] / 2 - int(80 * resolution_sf[1])))
            continue_button.draw(screen)
            pygame.display.update()

    choices = sample(locked, min(REWARD_CHOICES, len(locked)))
    card_w = int(125 * resolution_sf[0])
    card_h = int(175 * resolution_sf[1])
    card_g = int(20  * resolution_sf[0])

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
            Button(x + card_w / 2, y + card_h + card_g,
                   card_w, int(35 * resolution_sf[1]), "pick",
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

        current_background = draw_background(screen, current_background, color_background)

        tw, _ = big_font.size("Pick a card to unlock")
        screen.blit(big_font.render("Pick a card to unlock", True, color_font),
                    ((res[0] - tw) / 2, int(80 * resolution_sf[1])))

        for (name, obj), btn in zip(card_objects, select_buttons):
            obj.draw(screen)
            btn.draw(screen)

        pygame.display.update()

    if chosen in locked_cards:
        data["available_cards"].append(chosen)
    elif chosen in locked_commanders:
        data["available_commanders"].append(chosen)
    save_deck_data(data)

    return chosen
