import pygame
import card_classes
import commander_classes
from classes import Button, Text
from draw_ui import draw_background
from deck_manager import load_deck_data, save_deck_data
from random import sample, choice

STAGES = [
    {
        # tutorial: bodies and basic taunt only
        # alchemist has no spells in this pool so hes a vanilla 20hp commander
        # player should win
        "name": "Stage 1",
        "subtitle": "Tutorial Type",
        "desc": "Opponent: just a guy",
        "card_pool": ["Amogus", "IceCube", "Skeleton"],
        "commander_pool": ["Alchemist"],
        "mana_bonus": 0,
        "ai_hand_size": 4,
        "deck_size": 40,
    },
    {
        # introduces economy and punishing taunt
        # miku heals every cost-1 card by +2hp on play:
        #   pump (cost 1) -> 7hp. a 7hp pump behind a thorn is basically immortal
        #   icecube (cost 1) -> 4hp. better taunt than thorn for half the cost
        #   skeleton (cost 1) -> 3hp. survives thorn retaliation which it normally wouldnt
        # jesus heals a random ally each turn
        "name": "Stage 2",
        "subtitle": "Hatsune Messiah",
        "desc": "Opponent: Miku & Jesus",
        "card_pool": ["Amogus", "IceCube", "Thorn", "Pump", "BagOfGold", "Skeleton"],
        "commander_pool": ["Miku", "Jesus"],
        "mana_bonus": 0,
        "ai_hand_size": 5,
        "deck_size": 40,
    },
    {
        # introduces high-atk threats and ignore-taunt
        # biden: +1 mana immediately when a pump is played
        # glados: trades aggressively, draws off every death
        # musketeer (ignore taunt, 3/1) is the first real answer to pump-behind-thorn
        "name": "Stage 3",
        "subtitle": "Malarkey in the Test Chamber",
        "desc": "Opponent: +1 mana per turn",
        "card_pool": ["Amogus", "Thorn", "Pump", "Hong", "Sponge", "Musketeer", "Retriever"],
        "commander_pool": ["Biden", "GLaDOS"],
        "mana_bonus": 1,
        "ai_hand_size": 6,
        "deck_size": 40,
    },
    {
        # introduces growth threats, net, and two momentum commanders
        # sonic: every played card gets +1 action on play
        #   net is NOT a spell, so sonic triggers on it -> net gets +1 action immediately
        #   this means net+sonic = same-turn free play (net acts on the turn its played)
        #   net into hong with sonic = 3 mana for a 4/4 that attacks this turn
        # shadow: every kill = +1 mana. hong kills most things in 1 hit
        # snowball and sponge are the slow threats
        # kamikaze does 6 damage now (was 8) (was 10)
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
        # BOSS FIGHT 1 - biden pump accelerant deck
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
        # BOSS FIGHT 2 - miku cheap swarm with a near-unkillable pump
        "name": "Stage 6",
        "subtitle": "You Can Call Me Miku",
        "desc": "Opponent: +1 mana per turn",
        "card_pool": ["Skeleton", "IceCube", "BagOfGold", "Bin", "Retriever", "Amogus", "Thorn", "Pump"],
        "commander_pool": ["Miku"],
        "mana_bonus": 1,
        "ai_hand_size": 7,
        "deck_size": 40,
    },
    {
        # BOSS FIGHT 3 - alchemist bag-of-gold engine
        "name": "Stage 7",
        "subtitle": "Edward",
        "desc": "Opponent: +2 mana per turn",
        "card_pool": ["BagOfGold", "IceCube", "Thorn", "B52", "FatMan", "Hong", "Net", "Pump"],
        "commander_pool": ["Alchemist"],
        "mana_bonus": 2,
        "ai_hand_size": 8,
        "deck_size": 40,
    },
    {
        # BOSS FIGHT 4 - glados death-draw engine with fatman as the nuclear draw turn
        # glados draws 1 card when any ally dies
        "name": "Stage 8",
        "subtitle": "The Cake is a Lie",
        "desc": "Opponent: +2 mana per turn",
        "card_pool": ["Amogus", "Skeleton", "Thorn", "IceCube", "Musketeer", "B52", "BagOfGold", "Retriever", "Hong", "FatMan"],
        "commander_pool": ["GLaDOS"],
        "mana_bonus": 2,
        "ai_hand_size": 8,
        "deck_size": 40,
    },
    {
        # BOSS FIGHT 5 - sonic instant aggression
        "name": "Stage 9",
        "subtitle": "Gotta Go Fast",
        "desc": "Opponent: +3 mana per turn",
        "card_pool": ["Amogus", "Hong", "Musketeer", "Sponge", "Snowball", "Kamikaze", "Net", "Thorn", "IceCube"],
        "commander_pool": ["Sonic"],
        "mana_bonus": 3,
        "ai_hand_size": 8,
        "deck_size": 40,
    },
    {
        # shadow: every enemy killed by an ally = +1 mana
        "name": "Stage 10",
        "subtitle": "Chaos Control",
        "desc": "Opponent: +3 mana per turn",
        "card_pool": ["Hong", "Musketeer", "Sponge", "Thorn", "Pump", "Kamikaze", "Net", "B52", "BagOfGold", "Amogus", "Snowball", "IceCube", "FatMan"],
        "commander_pool": ["Shadow"],
        "mana_bonus": 3,
        "ai_hand_size": 9,
        "deck_size": 40,
    },
]

REWARD_CHOICES = 3


# card role classification
# fatman is aoe: same category as b52 - both are mass damage spells
# when both are in the pool the generator splits aoe slots between them
CARD_ROLES = {
    "Pump": "economy",
    "BagOfGold": "economy",
    "Skeleton": "attack",
    "Amogus": "attack",
    "Hong": "attack",
    "Musketeer": "attack",
    "Sponge": "attack",
    "Snowball": "attack",
    "IceCube": "taunt",
    "Thorn": "taunt",
    "Bin": "utility",
    "Retriever": "utility",
    "Net": "utility",
    "Medic": "utility",
    "Kamikaze": "finisher",
    "B52": "aoe",
    "FatMan": "aoe",
}

STAGE_COMPOSITIONS = [
    {"attack": 20, "taunt": 18},
    {"taunt": 16, "attack": 10, "economy": 12},
    {"economy": 10, "taunt": 12, "attack": 14, "utility": 4},
    {"attack": 16, "taunt": 10, "finisher": 4, "utility": 6, "economy": 4},
    {"economy": 14, "taunt": 10, "utility": 6, "finisher": 5, "attack": 4},
    {"taunt": 18, "attack": 10, "economy": 8, "utility": 4},
    {"economy": 14, "taunt": 12, "aoe": 6, "utility": 4, "attack": 4},
    {"attack": 12, "taunt": 8, "aoe": 10, "utility": 6, "economy": 4},
    {"attack": 20, "taunt": 10, "finisher": 4, "utility": 4},
    {"attack": 14, "taunt": 10, "economy": 6, "finisher": 4, "aoe": 6, "utility": 4},
]

MAX_COPIES_PER_CARD = 10


def generate_campaign_deck(stage, deck_size):
    """
    Description:
    Procedurally generates the AI's deck for a given campaign stage. Classifies
    all cards in the stage's pool into roles via CARD_ROLES, then fills the deck
    in role-proportioned batches according to STAGE_COMPOSITIONS. Any remaining
    slots after the composition targets are met get random filled (random sampling!!!)
    from the full pool. MAX_COPIES_PER_CARD stops any single card flooding the whole deck.

    Stages with multiple commanders (Stages 2, 3, 4) pick one randomly.

    Parameters:
        stage (dict): the stage dict from STAGES
        deck_size (int): total deck size including the commander

    Returns:
        deck (list): [Commander, Card, ...] fully set up and ready to go
    """
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

    comm_class = choice(list(comm_classes_map.values()))
    deck = [comm_class()]

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

    for role, target in composition.items():
        available = [n for n in role_pools.get(role, [])
                     if card_counts.get(n, 0) < MAX_COPIES_PER_CARD]
        if not available:
            continue
        for _ in range(target):
            if len(deck) - 1 >= target_cards:
                break
            eligible = [n for n in available if card_counts.get(n, 0) < MAX_COPIES_PER_CARD]
            if not eligible:
                break
            add_card(choice(eligible))

    while len(deck) - 1 < target_cards:
        eligible = [n for n in full_pool if card_counts.get(n, 0) < MAX_COPIES_PER_CARD]
        if not eligible:
            eligible = full_pool
        add_card(choice(eligible))

    for card in deck:
        card.setup()

    return deck


def run_campaign_menu(screen, res, settings):
    """
    Description:
    The campaign stage select screen. Shows all 10 stages as a vertical list.
    Completed stages show a green "completed" label to the right. The current
    unlocked stage shows "play".

    Progress is read from player_data.json (campaign_stage field). A stage index
    is unlocked if it's <= campaign_stage. campaign_stage advances when the player
    beats a stage for the first time.
    Replaying completed stages is always allowed.

    Parameters:
        screen (pygame.Surface): the main display surface
        res (tuple): (width, height) screen resolution
        settings (tuple): standard settings tuple unpacked inside

    Returns:
        tuple or str: (stage_index, stage_dict) when a stage is selected,
            or "menu" when the player clicks back
    """
    _, _, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid = settings

    resolution_sf = (res[0] / 2880, res[1] / 1920)

    data = load_deck_data()
    current_stage = data.get("campaign_stage", 0)

    btn_w = int(300 * resolution_sf[0])
    btn_h = int(55  * resolution_sf[1])
    btn_gap = int(70 * resolution_sf[1])

    back_btn_w = int(200 * resolution_sf[0])
    back_btn_h = int(50  * resolution_sf[1])
    back_button = Button(res[0] / 2, res[1] - back_btn_h - int(20 * resolution_sf[1]), back_btn_w, back_btn_h, "back", small_font, color_font, color_light, color_dark)

    total_h = len(STAGES) * btn_gap - (btn_gap - btn_h)
    top_y = (res[1] - total_h) / 2 + int(40 * resolution_sf[1])

    stage_buttons = []
    for i, stage in enumerate(STAGES):
        y = top_y + i * btn_gap
        stage_buttons.append(
            Button(res[0] / 2, y, btn_w, btn_h, stage["name"], small_font, color_font, color_light, color_dark, color_invalid)
        )

    label_x_right = res[0] / 2 + btn_w / 2 + int(15 * resolution_sf[0])
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
        screen.blit(big_font.render("Campaign", True, color_font), ((res[0] - tw) / 2, int(20 * resolution_sf[1])))

        for i, (btn, stage) in enumerate(zip(stage_buttons, STAGES)):
            unlocked = i <= current_stage
            completed = i < current_stage

            btn.draw(screen, greyed=not unlocked)

            label = "completed" if completed else ("play" if unlocked else "locked")
            label_color = (150, 255, 150) if completed else color_font
            screen.blit(small_font.render(label, True, label_color), (label_x_right, btn.y + (btn_h - small_font.size(label)[1]) // 2))

            sw, _ = small_font.size(stage["subtitle"])
            screen.blit(small_font.render(stage["subtitle"], True, color_font), (label_x_left_base - sw, btn.y + (btn_h - small_font.size(stage["subtitle"])[1]) // 2))

        back_button.draw(screen)
        pygame.display.update()


def run_reward_screen(screen, res, settings):
    """
    Description:
    Post-stage reward screen. Shows REWARD_CHOICES (3) randomly sampled (random sampling!!!)
    cards or commanders from the locked pool and lets the player pick one to permanently
    unlock. The chosen card gets added to available_cards or available_commanders
    in player_data.json so it shows up in the deck builder from now on.

    If everything is already unlocked (all_cards and all_commanders are all
    available), shows a "No new cards!" message and a continue button instead.

    Parameters:
        screen (pygame.Surface): the main display surface
        res (tuple): (width, height) screen resolution
        settings (tuple): standard settings tuple unpacked inside

    Returns:
        str or None: the class name string of the chosen card/commander,
            or None if nothing was available to unlock
    """
    _, _, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid = settings

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