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
        # player should win comfortably - just learning the board
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
        #   bag of gold (cost 0) -> 2hp (doesnt matter, its a spell that dies anyway)
        # jesus heals a random ally each turn - great with miku-buffed boards
        # note: pump only floors mana at turn_mana now, doesnt stack above it
        # but miku makes the pump itself so durable that it almost always fires
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
        # biden: +1 mana immediately when a pump is played (the main payoff now that
        # pumps dont stack above turn_mana - biden turns each pump into an accelerant)
        # glados: trades aggressively, draws off every death
        # musketeer (ignore taunt, 3/1) is the first real answer to pump-behind-thorn
        # retriever stays on board drawing 1 card per mana spent - good with biden mana
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
        # snowball and sponge are the slow threats - thorn covers them while they grow
        # kamikaze does 8 damage now (was 10) - still a finisher but needs board backup
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
        # pump now only floors mana at turn_mana - it doesnt stack
        # but biden gives +1 mana IMMEDIATELY when a pump is played
        # so the loop is: play pump -> get +1 mana now -> play something else this turn
        # with 2 pumps played early = 2 extra mana spent immediately = tempo lead
        # icecube + thorn walls protect the pumps so they actually fire each turn
        # medic heals 2hp/turn - keeps biden alive long enough to convert tempo into wins
        # kamikaze (8 damage) + board attacks closes games once hong is established
        # bags enable reaching 7 mana for fatman next stage up
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
        # the core problem for the player: pump (cost 1) healed to 7hp by miku
        # pump still only floors mana at turn_mana but a 7hp pump basically never dies
        # it sits behind a thorn wall and quietly ensures the ai hits its mana floor every turn
        # icecube healed to 4hp = better than thorn for 1 less mana
        # skeleton healed to 3hp = survives any thorn retaliation (normally it wouldnt)
        # bin draws a card on the turn its played (haste) - keeps the hand full
        # retriever draws for 1 mana per activation - great with the miku mana base
        # this stage should feel like being swarmed with cheap durable stuff
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
        # IMPORTANT: alchemist only draws on spells costing 1 or less
        # only bagofgold (cost 0) triggers alchemist draws
        # b52 (cost 2), kamikaze (cost 6), fatman (cost 7) do NOT draw with alchemist
        # the engine: bag of gold -> +1 mana + draw 1 card via alchemist
        # if you draw another bag, play it again -> +1 more mana + draw another card
        # chain enough bags and you reach fatman cost (7) + have cards to play after
        # but bags have a 250 cap_penalty when at max mana - dont hoard them
        # net sets up hong: play net this turn, free-play hong next turn
        # (net is not a spell so alchemist doesnt draw from it - its pure hong setup)
        # b52 as cheap board control while the engine assembles
        # pump only useful as a mana floor but +2 mana bonus means ai has plenty anyway
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
        # the intended combo: build a board of cheap fragile stuff, then play fatman
        # fatman kills everything on both boards including your own cards
        # if the ai has 4 cards when fatman plays -> 4 glados draws in one turn
        # then rebuild from a full hand while the player has an empty board
        # skeleton and amogus are the cannon fodder (cheap, die on any hit)
        # musketeer kills valuable targets then dies to retaliation -> draw
        # b52 clears 1hp boards including own cards -> draw triggers for cheap
        # retriever keeps hand full in between glados draw turns
        # with +2 mana bonus fatman (cost 7) is reachable every turn naturally
        # the thorn/icecube wall exists purely to delay the player while the engine sets up
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
        # sonic gives every non-spell card +1 action when played
        # the KEY mechanic: net is not a spell, so sonic gives net +1 action on play
        # this means: play net (3 mana) -> net immediately has 1 action -> use it to free-play hong
        # net + sonic = 3 mana for a 4/4 that attacks on the same turn (with its own sonic action too)
        # that's effectively a 4/4 with haste for 3 mana which is broken
        # sponge with sonic action = swings immediately AND grows on every hit afterward
        # snowball with sonic action = attacks for 0 the first turn but grows to 1/2, 2/3...
        # musketeer with sonic action = kills an engine card (pump, medic) through taunt immediately
        # icecube protects sponge and snowball - sonic deck still needs taunt for growth threats
        # kamikaze at 8 damage closes games when board is stalled
        # +3 mana bonus: ai has up to 9 effective mana per turn. flood and attack every turn
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
        # fatman interaction: fatman calls card.attacked(self) which triggers on_enemy_death
        # this means shadow gets +1 mana for EVERY card fatman kills, including own cards
        # a full 6v6 board + fatman = up to +12 mana for shadow in one turn
        # that mana stacks (capped at turn_mana*2) and fuels an immediate full rebuild
        # normal shadow loop: hong kills something -> +1 mana -> play another card -> kills more
        # musketeer ignores taunt to kill pumps/medics through walls -> +1 mana per engine kill
        # sponge grows with each hit and shadow turns each kill into mana chains
        # net + sonic combo gone here (shadow not sonic) but net still sets up hong next turn
        # b52 for multi-kill turns = multi-shadow mana from one card
        # bag of gold to spend the shadow mana chains on more plays
        # thorn wall protects the sponge/snowball while they grow into reliable shadow triggers
        # +3 mana bonus + shadow mana chains = the ai can theoretically empty its hand in one turn
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
    "FatMan":    "aoe",
}

STAGE_COMPOSITIONS = [
    # stage 1: tutorial
    # just attackers and taunt - learn the board
    {"attack": 20, "taunt": 18},

    # stage 2: miku/jesus
    # high taunt: miku makes icecube 4hp and thorn even tankier
    # high economy: miku makes pump 7hp so it almost never dies
    # bags unlock playing two 1-cost cards in one turn
    {"taunt": 16, "attack": 10, "economy": 12},

    # stage 3: biden/glados
    # economy for biden: each pump play = +1 immediate mana
    # taunt protects the pumps so they actually floor mana every turn
    # attackers apply pressure and die for glados draws
    # utility (retriever) refills hand with spare biden mana
    {"economy": 10, "taunt": 12, "attack": 14, "utility": 4},

    # stage 4: sonic/shadow
    # maximum attackers for sonic action bonus and shadow kill triggers
    # thorn protects snowball and sponge while they grow
    # utility (net): net+sonic = instant free play same turn - key combo
    # finisher (kamikaze): 8 damage + board attacks closes games
    {"attack": 16, "taunt": 10, "finisher": 4, "utility": 6, "economy": 4},

    # stage 5: biden boss
    # economy is the engine: pumps give immediate mana via biden
    # 2 pumps played early = 2 extra mana spent immediately = huge tempo
    # taunt walls protect the pumps so they keep flooring mana
    # utility (medic): keeps commander alive while the pump plan assembles
    # finisher (kamikaze): 8 damage is the win condition with hong support
    # attack (hong): the actual damage dealer once economy is established
    {"economy": 14, "taunt": 10, "utility": 6, "finisher": 5, "attack": 4},

    # stage 6: miku boss
    # maximize cost-1 cards for miku healing triggers
    # pump (1 cost -> 7hp with miku) is nearly unkillable even with musketeer
    # icecube (1 cost -> 4hp with miku) = excellent cheap taunt
    # skeleton (1 cost -> 3hp with miku) = survives thorn retaliation
    # utility (bin, retriever) keeps hand full for continuous miku triggers
    {"taunt": 18, "attack": 10, "economy": 8, "utility": 4},

    # stage 7: alchemist boss
    # heavy economy (bags only): bag = +1 mana + alchemist draw
    # chain bags to reach fatman (cost 7) and refill hand simultaneously
    # taunt wall lets the bag chain assemble without being immediately killed
    # utility (net): sets up hong next turn - delayed free play still strong
    # aoe (b52 + fatman): b52 for cheap board control, fatman as the payoff
    # attack (hong): midgame threat while waiting to chain enough bags
    # note: pump is in pool but +2 mana bonus makes it nearly redundant
    {"economy": 14, "taunt": 12, "aoe": 6, "utility": 4, "attack": 4},

    # stage 8: glados boss
    # attack (cheap fodder): amogus/skeleton die easily = glados draws
    # aoe (b52 + fatman): split between cheap clear and nuclear draw turn
    # fatman is the designed payoff: kill own 4-card board = 4 glados draws at once
    # thorn/icecube wall: brief protection before the inevitable sacrifice
    # utility (retriever): hand refuel between glados draw turns
    # economy (bags): reach fatman cost, enable multi-play turns
    {"attack": 12, "taunt": 8, "aoe": 10, "utility": 6, "economy": 4},

    # stage 9: sonic boss
    # maximum attackers because every card attacks the turn it enters
    # the dream turn: net (played, gets +1 action from sonic) -> free-play hong ->
    #   hong gets +1 action from sonic -> attacks immediately for 4 damage
    #   total: 3 mana for a 4/4 that attacks this turn
    # thorn and icecube protect sponge and snowball while they grow
    # (sonic still gives sponge/snowball +1 action when played - they swing immediately)
    # finisher (kamikaze): 8 damage panic button when board is blocked
    # utility (net): prioritized specifically for the net+sonic instant combo
    {"attack": 20, "taunt": 10, "finisher": 4, "utility": 4},

    # stage 10: shadow final boss
    # attack (hong, musketeer): reliable single-hit killers for shadow mana triggers
    # thorn/icecube: protects sponge/snowball while they grow into big shadow triggers
    # aoe (b52 + fatman): split between the two
    #   b52: multi-kill turn = multi-shadow mana from cheap 2 mana spell
    #   fatman: kills all cards including own -> shadow gets mana for each death
    #   full 6v6 board fatman = up to +12 shadow mana in one turn
    # economy (bags): spends shadow mana chain on more plays in the same turn
    # finisher (kamikaze): 8 damage when the board is stalled
    # utility (net): sets up hong as a guaranteed kill for shadow mana
    {"attack": 14, "taunt": 10, "economy": 6, "finisher": 4, "aoe": 6, "utility": 4},
]

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
            eligible = [n for n in available
                        if card_counts.get(n, 0) < MAX_COPIES_PER_CARD]
            if not eligible:
                break
            add_card(choice(eligible))

    while len(deck) - 1 < target_cards:
        eligible = [n for n in full_pool
                    if card_counts.get(n, 0) < MAX_COPIES_PER_CARD]
        if not eligible:
            eligible = full_pool
        add_card(choice(eligible))

    for card in deck:
        card.setup()

    return deck


def run_campaign_menu(screen, res, settings):
    _, _, color_light, color_dark, current_background, color_background, \
        small_font, big_font, color_font, color_invalid = settings

    resolution_sf = (res[0] / 2880, res[1] / 1920)

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