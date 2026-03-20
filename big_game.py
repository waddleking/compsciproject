import pygame
from draw_ui import draw_chips_ui, draw_card_ui, draw_win_fail_screen, draw_background
from betting import run_bets
from classes import Button, Text
from main_classes import Game, Player, Card
from random import randint, choice
from menu import run_game_menu
from setup import setup_cards

def run_big_game(settings, decks, hp, mana, hand_size, max_active, max_hand, cost, ai_mana_bonus=0, ai_hand_size=None, stage_desc="", starting_player=0, player_id=0):
    """
    Description:
    The main game loop. Everything that happens during an actual match lives here:
    player input, the AI state machine, card rendering, lerp animation, particles,
    spell notification banners, win detection, and the turn-change overlay.

    The AI runs as a state machine with phases "play", "action", and "end", with
    AI_STEP_DELAY=50 frames between each individual action so the player can see
    what the AI is doing rather than the whole turn resolving invisibly in one frame (thanks rayhan)

    The play threshold is 10-mana rather than a fixed 10. When the AI has lots
    of mana the threshold drops, so it will play cards it would normally consider
    marginal rather than sit on unspent resources. When mana is low it stays picky.
    This is only because I was watching the AI stockpile mana for no reason.

    After the action phase, instead of immediately ending the turn the AI bounces
    back to the play phase up to 3 times (tracked by ai_iteration). This means it
    can play a card, act with it, check if anything new is now worth playing, act
    again, and so on. This was added because Shadow's whole thing doesn't work if 
    the AI doesn't use the mana it gets from swinging.

    The lerp system moves each card toward desired_x/desired_y every frame.
    distance**2 < 50 is the snap threshold that prevents cards getting approaching
    but never reaching it.

    Parameters:
        settings (tuple): (screen, res, color_light, color_dark, current_background,
            color_background, small_font, big_font, color_font, color_invalid)
        decks (list): [player_deck, ai_deck], each is [Commander, Card, Card, ...]
        hp (int): unused as I moved to a commander system
        mana (int): base mana gained per turn
        hand_size (int): opening hand size for the human player
        max_active (int): board size limit per player
        max_hand (int): hand size cap before draws are skipped
        cost (int): legacy parameter, unused
        ai_mana_bonus (int): extra mana added to the AI's total at phase initialisation
        ai_hand_size (int or None): AI opening hand size, defaults to hand_size
        stage_desc (str): small text shown centre-screen describing stage difficulty
            modifiers, hidden if empty string
        starting_player (int): who takes turn 0 and gets the opening mana draw
        player_id (int or None): index of the human player; None = AI vs AI watch mode

    Returns:
        str or int: "menu" if the player left via escape, or the winning player
            index (0 or 1) when a commander hits 0hp
    """
    screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid = settings
    button_available = False

    resolution_sf = (res[0]/1440, res[1]/960)

    players = randint(2, 2)
    # player_id = 0
    result = None
    overlay_y = -res[1]
    card_g = int(10 * resolution_sf[0])
    card_w = int(125 * resolution_sf[0])
    card_h = int(175 * resolution_sf[1])
    base_card = Card(w=card_w, h=card_h, hidden=True)
    end_button = Button(1.5*card_w, res[1]/2, int(100 * resolution_sf[0]), int(50 * resolution_sf[1]), "end", small_font, color_font, color_light, color_dark, color_invalid)

    y_positions = [res[1]-(card_g+card_h), card_g]
    deck_positions = [(card_w, res[1]-2*(card_g+card_h)), (res[0]-2*(card_g+card_w), 2*(card_g+card_h)-card_h)]
    mana_positions = [(card_w/2, res[1]-1.5*card_h), (res[0]-(card_g+card_w/2), 1.5*card_h)]
    commander_positions = [(res[0]-2*(card_g+card_w), res[1]-2*(card_g+card_h)), (card_w, 2*(card_g+card_h)-card_h)]

    selecting = None
    selected_card = None
    selected_source = None
    selected_target = None

    particles = []
    spell_notifications = []  # [{name, player, fade}]

    AI_STEP_DELAY = 50       # frames between each individual AI action
    ai_phase = None     # None, "play", "action", "end"
    ai_step_timer = 0        # countdown to next AI step

    game_ended = False

    anim_type = None
    anim_bool = None
    anim_temp = None
    anim_max = None
    anim_x = None
    anim_y = None
    anim_w = None
    anim_h = None
    anim_fade = None

    game = start_big_game(res, decks, players, player_id, card_w, card_h, card_g, mana, hand_size, max_active, max_hand, y_positions, deck_positions, mana_positions, commander_positions, starting_player, ai_hand_size=ai_hand_size)
    result = None

    print("game start")
    anim_type = "player_change"
    anim_bool = True
    anim_fade = 0
    anim_max = 150
    anim_h = int(150 * resolution_sf[1])
    anim_y = res[1]/2-anim_h/2

    while True:

        mouse = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: 
                pygame.quit() 

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    option = run_game_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid)
                    if option == "menu":
                        return option
                if ev.key == pygame.K_TAB:
                    for player in game.players:
                        for card in player.hand:
                            card.set_hidden(False)
                    
            if ev.type == pygame.KEYDOWN or ev.type == pygame.MOUSEBUTTONDOWN: 
                if game_ended:
                    return result
                
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if result == None:
                    if game.turn_player == player_id:
                        if anim_type == None and end_button.touching():
                            print("player turn over")
                            particles.extend(game.next_turn())
                            anim_type = "player_change"
                            anim_bool = True
                            anim_fade = 0
                            anim_max = 150
                            anim_h = int(150 * resolution_sf[1])
                            anim_y = res[1]/2-anim_h/2

                        if selecting == None:
                            if selected_card is not None and selected_card.action_button is not None and selected_card.action_button.touching():
                                selected_source = selected_card
                                selecting = selected_card.selection_type
                                selected_card = None
                                if selecting == "":
                                    particles.extend(selected_source.on_action())
                                    selecting = None
                                    selected_source = None
                                    selected_target = None
                                    selected_card = None
                            elif selected_card is not None and game.players[player_id].mana >= selected_card.retreat_cost and selected_card.retreat_button.touching():
                                selected_card.retreat()
                                selected_card = None
                                selected_source = None
                            else:
                                selected_card = None
                                for card in game.players[player_id].active:
                                    if card.touching(mouse) and card.actions > 0:
                                        selected_card = card
                        
                        elif selecting == "enemy":
                            for player_num in range(players):
                                if player_num != player_id:
                                    highest_taunt = 0
                                    for card in game.players[player_num].active:
                                        if card.taunt > highest_taunt:
                                            highest_taunt = card.taunt
                                    
                                    if selected_source.ignore_taunt:
                                        highest_taunt = 0

                                    for card in game.players[player_num].active:
                                        if card.touching(mouse) and card.taunt >= highest_taunt:
                                            selected_target = card
                                            particles.extend(selected_source.on_action(selected_target))

                                    if game.players[player_num].commander.touching(mouse) and game.players[player_num].commander.taunt >= highest_taunt:
                                        selected_target = game.players[player_num].commander
                                        particles.extend(selected_source.on_action(selected_target))

                            selecting = None
                            selected_source = None
                            selected_target = None
                            selected_card = None

                        elif selecting == "hand":
                            for card in game.players[player_id].hand:
                                if card.touching(mouse):
                                    selected_target = card
                                    particles.extend(selected_source.on_action(selected_target))

                            selecting = None
                            selected_source = None
                            selected_target = None
                            selected_card = None

                        for card in game.players[player_id].hand:
                            if len(game.players[player_id].active) < game.players[player_id].max_active or card.spell == True:
                                if card.touching(mouse) and game.players[player_id].mana >= card.cost and card.actions > 0 and (game.turn - starting_player >= game.num_players or not card.spell):
                                    particles.extend(card.play())
                                    if game.turn - starting_player < game.num_players and card.atk != 0:
                                        card.actions = 0
                
        current_background = draw_background(screen, current_background, color_background)

        if result == None:
            if game.turn_player != player_id:

                #  initialise AI turn once the player_change banner has finished 
                if ai_phase is None and anim_type is None:
                    game.players[game.turn_player].mana += ai_mana_bonus
                    ai_phase = "play"
                    ai_iteration = 0
                    ai_step_timer = AI_STEP_DELAY
                    print(f"ai {game.turn_player} turn begin")

                #  count down between steps 
                if ai_step_timer > 0:
                    ai_step_timer -= 1

                #  PLAY PHASE: play one card per step 
                elif ai_phase == "play":
                    hand = game.players[game.turn_player].hand
                    mana = game.players[game.turn_player].mana
                    played = False

                    for card in sorted(hand, key=lambda x: x.ai_value(), reverse=True):
                        if card.cost <= mana and card.ai_value() >= 10-mana and (game.turn - starting_player >= game.num_players or not card.spell):
                            if len(game.players[game.turn_player].active) < max_active:
                                particles.extend(card.play())
                                if game.turn < game.num_players and card.atk != 0:
                                    card.actions = 0
                                print(f"ai {game.turn_player} played {card.name}")
                                played = True
                                ai_step_timer = AI_STEP_DELAY
                                break
                            else:
                                swappable_card = None
                                for active_card in sorted(game.players[game.turn_player].active, key=lambda x: x.ai_value()):
                                    if (active_card.ai_value() < card.ai_value()
                                            and card.ai_value() >= 10-mana
                                            and active_card.retreat_cost + card.cost <= mana):
                                        swappable_card = active_card
                                if swappable_card is not None:
                                    swappable_card.retreat()
                                    print(f"ai {game.turn_player} retreated {swappable_card.name}")
                                    particles.extend(card.play())
                                    if game.turn - starting_player < game.num_players and card.atk != 0:
                                        card.actions = 0
                                    print(f"ai {game.turn_player} played {card.name}")
                                    played = True
                                    ai_step_timer = AI_STEP_DELAY
                                    break

                    if not played:
                        ai_phase = "action"
                        ai_step_timer = AI_STEP_DELAY

                #  ACTION PHASE: use one active card per step 
                elif ai_phase == "action":
                    acted = False

                    for selected_source in game.players[game.turn_player].active:
                        if selected_source.actions > 0:
                            selecting = selected_source.selection_type

                            if selecting == "":
                                particles.extend(selected_source.on_action())
                                print(f"ai {game.turn_player} used {selected_source.name}")
                                acted = True

                            elif selecting == "enemy" and selected_source.atk != 0:
                                available_targets = []
                                for player_num in range(players):
                                    if player_num != game.turn_player:
                                        highest_taunt = 0
                                        highest_actual_taunt = 0
                                        for card in game.players[player_num].active:
                                            if card.taunt > highest_taunt:
                                                highest_taunt = card.taunt
                                                highest_actual_taunt = card.taunt
                                        if selected_source.ignore_taunt:
                                            highest_taunt = 0
                                        for card in game.players[player_num].active:
                                            if card.taunt >= highest_taunt:
                                                available_targets.append(card)
                                        if game.players[player_num].commander.taunt >= highest_taunt:
                                            available_targets.append(game.players[player_num].commander)

                                if available_targets:
                                    selected_target = sorted(available_targets, key=lambda x: x.ai_value()*(1+highest_actual_taunt-x.taunt), reverse=True)[0]
                                    particles.extend(selected_source.on_action(selected_target))
                                    print(f"ai {game.turn_player} used {selected_source.name} to attack {selected_target.name}")
                                    acted = True

                            elif selecting == "hand":
                                ai_hand = game.players[game.turn_player].hand
                                if ai_hand:
                                    selected_target = sorted(ai_hand, key=lambda x: x.ai_value(), reverse=True)[0]
                                    particles.extend(selected_source.on_action(selected_target))
                                    print(f"ai {game.turn_player} used {selected_source.name} to use {selected_target.name}")
                                    acted = True

                            selecting = None
                            selected_source = None
                            selected_target = None
                            selected_card = None

                            if acted:
                                ai_step_timer = AI_STEP_DELAY
                                break   # one action per step; render then come back

                    if not acted and ai_iteration == 3:
                        ai_phase = "end"
                    elif not acted:
                        ai_phase = "play"
                        ai_iteration += 1

                #  END PHASE: hand off to next player 
                elif ai_phase == "end":
                    particles.extend(game.next_turn())
                    anim_type = "player_change"
                    anim_bool = True
                    anim_fade = 0
                    anim_max = 150
                    anim_h = int(150 * resolution_sf[1])
                    anim_y = res[1]/2 - anim_h/2
                    ai_phase = None
                    ai_step_timer = 0
            
        for player in game.players:
            hand = player.hand
            pgap = card_g
            while len(hand)*(pgap+card_w) > res[0]:
                pgap -= max(1, int(5 * resolution_sf[0]))
            for i in range(len(hand)):
                card = hand[i]
                card.draw(screen)
                card.desired_x = (res[0]-((card_w+pgap)*len(hand)))/2+((card_w+pgap)*i)+(pgap/2)
                if card.desired_x is not None:
                    if card.x != card.desired_x:
                        distance = card.desired_x - card.x
                        if distance**2 < 50 * resolution_sf[0]**2:
                            card.x = card.desired_x
                        else:
                            card.x += (distance)/5

                card.desired_y = player.y

                if card.desired_y is not None:
                    if card.y != card.desired_y:
                        distance = card.desired_y - card.y
                        if distance**2 < 50 * resolution_sf[1]**2:
                            card.y = hand[i].desired_y
                        else:
                            card.y += (distance)/5
                
                hand[i] = card
                
            if selected_card is not None:
                selected_card.draw_buttons(screen)
            
            if player.commander is not None:
                player.commander.draw(screen)
                if player.deck_position[1] > res[1]//2:
                    Text(player.commander_position[0]+card_w/2, player.commander_position[1]-card_g*2, 0, 0, str(player.commander.hp), small_font, color_font, None, False).draw(screen)
                else:
                    Text(player.commander_position[0]+card_w/2, player.commander_position[1]+player.commander.h+card_g*2, 0, 0, str(player.commander.hp), small_font, color_font, None, False).draw(screen)

            if len(player.deck) > 0:
                base_card.x, base_card.y = player.deck_position
                base_card.draw(screen)
                if player.deck_position[1] > res[1]//2:
                    Text(player.deck_position[0]+card_w/2, player.deck_position[1]-card_g*2, 0, 0, str(len(player.deck)), small_font, color_font, None, False).draw(screen)
                else:
                    Text(player.deck_position[0]+card_w/2, player.deck_position[1]+base_card.h+card_g*2, 0, 0, str(len(player.deck)), small_font, color_font, None, False).draw(screen)

            Text(player.mana_position[0], player.mana_position[1], 0, 0, str(player.mana), big_font, color_font, None, False).draw(screen)

            player.hand = hand

            hand = player.active
            pgap = card_g
            while len(hand)*(pgap+card_w) > res[0]:
                pgap -= max(1, int(5 * resolution_sf[0]))
            for i in range(len(hand)):
                card = hand[i]
                card.desired_x = (res[0]-((card_w+pgap)*len(hand)))/2+((card_w+pgap)*i)+(pgap/2)
                if card.desired_x is not None:
                    if card.x != card.desired_x:
                        distance = card.desired_x - card.x
                        if distance**2 < 50 * resolution_sf[0]**2:
                            card.x = card.desired_x
                        else:
                            card.x += (distance)/5

                card.desired_y = player.y

                if card.desired_y > res[1]/2:
                    card.desired_y -= card_h+card_g
                else:
                    card.desired_y += card_h+card_g

                if (card.touching(mouse) and card.actions > 0) or selected_card == card or selected_source == card:
                    if card.desired_y > res[1]/2:
                        card.desired_y -= card_g/2

                if card.desired_y is not None:
                    if card.y != card.desired_y:
                        distance = card.desired_y - card.y
                        if distance**2 < 50 * resolution_sf[1]**2:
                            card.y = hand[i].desired_y
                        else:
                            card.y += (distance)/5
                
                card.draw(screen)
                hand[i] = card
            player.active = hand

        if game.turn_player == player_id:
            end_button.draw(screen)

        # stage description
        # what difficulty modifiers are active
        if stage_desc:
            Text(res[0]/2, res[1]/2 - int(20 * resolution_sf[1]), 0, 0, stage_desc,
                 small_font, (255, 255, 255), None, False).draw(screen)

        # winning
        player_count = 0
        for player in game.players:
            if player.commander.hp <= 0:
                player.set_dead(True)
            elif player.commander.hp > 0:
                player.set_dead(False)
                player_count += 1

        if player_count == 1:
            for player_num in range(players):
                if game.players[player_num].dead == False and anim_type != "player_win":
                    result = player_num
                    anim_type = "player_win"
                    anim_fade = 0
                    anim_max = 150
                    anim_h = int(150 * resolution_sf[1])
                    anim_y = res[1]/2-anim_h/2

        if anim_type == "player_win":
            if anim_fade < 255:
                anim_fade += 3

            if anim_fade >= anim_max:
                anim_temp = anim_max
            else:
                anim_temp = anim_fade

            overlay = pygame.Surface((res[0], anim_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, anim_temp))

            screen.blit(overlay, (0, anim_y))
            Text(res[0]/2, res[1]/2, 0, 0, f"player {result+1} victory", big_font, color_font, None, False).set_alpha(anim_temp*255/anim_max).draw(screen)

            if anim_fade == 255:
                game_ended = True
            if anim_fade <= 0:
                anim_type = None

        if anim_type == "player_change":
            if anim_fade >= 200:
                anim_bool = False
            if anim_bool:
                anim_fade += 5
            else:
                anim_fade -= 5

            if anim_fade >= anim_max:
                anim_temp = anim_max
            else:
                anim_temp = anim_fade

            overlay = pygame.Surface((res[0], anim_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, anim_temp))

            screen.blit(overlay, (0, anim_y))
            Text(res[0]/2, res[1]/2, 0, 0, f"player {game.turn_player+1}", big_font, color_font, None, False).set_alpha(anim_temp*255/anim_max).draw(screen)

            if anim_fade <= 0:
                anim_type = None

        for particle in particles:
            particle.draw(screen)
            if particle.alpha < 0:
                particles.remove(particle)
                
        # drain any spell notifications queued by Card.play() this frame
        for pending in game.pending_spell_notifications:
            spell_notifications.append({"name": pending["name"], "player": pending["player"], "fade": 255})
        game.pending_spell_notifications.clear()

        #  spell notifications 
        for notif in spell_notifications[:]:
            alpha = notif["fade"]
            label = f"{notif['name']}  (player {notif['player'] + 1})"
            notif_w = int(res[0])
            notif_h = int(150 * resolution_sf[1])
            notif_x = (res[0] - notif_w) // 2
            notif_y = int(res[1] * 0.42)
            overlay = pygame.Surface((notif_w, notif_h), pygame.SRCALPHA)
            overlay.fill((20, 20, 60, min(180, alpha)))
            screen.blit(overlay, (notif_x, notif_y))
            surf = big_font.render(label, True, (180, 180, 255))
            surf.set_alpha(alpha)
            tw, th = big_font.size(label)
            screen.blit(surf, ((res[0] - tw) // 2, notif_y + (notif_h - th) // 2))
            notif["fade"] -= 3
            if notif["fade"] <= 0:
                spell_notifications.remove(notif)

        pygame.display.update()

def start_big_game(res, decks, players, player_id, card_w, card_h, card_g, mana, hand_size, max_active, max_hand, y_positions, deck_positions, mana_positions, commander_positions, starting_player=0, ai_hand_size=None):
    """
    Description:
    Constructs and returns a fully initialised Game object ready for run_big_game
    to loop over. Builds all the Player objects, attaches commanders, deals opening
    hands, sets card sizes, and positions everything on screen.

    Parameters:
        res (tuple): (width, height) screen resolution
        decks (list): [player_deck, ai_deck]
        players (int): always 2 (for now...)
        player_id (int or None): human player index, None for AI vs AI
        card_w (int): card pixel width
        card_h (int): card pixel height
        card_g (int): gap between cards in pixels
        mana (int): base mana per turn
        hand_size (int): human player opening hand size
        max_active (int): board size limit
        max_hand (int): hand size cap
        y_positions (list): [human_y, ai_y] vertical row positions
        deck_positions (list): [(x,y), (x,y)] deck pile screen positions
        mana_positions (list): [(x,y), (x,y)] mana display positions
        commander_positions (list): [(x,y), (x,y)] commander card positions
        starting_player (int): who takes turn 0 and gets the opening mana
        ai_hand_size (int or None): AI opening hand size, defaults to hand_size

    Returns:
        game (Game): fully initialised and ready to go
    """
    game = Game(players, mana)

    for i in range(players):
        game.add_player(Player(game=game, max_active=max_active, max_hand=max_hand, commander=decks[i][0], commander_position=commander_positions[i], deck=decks[i][1:], deck_position=deck_positions[i], mana_position=mana_positions[i], y=y_positions[i]))
    if player_id is not None:
        game.players[player_id].set_main_character(True)
    else:
        for i in range(players):
            game.players[i].set_main_character(True)

    for i, player in enumerate(game.players):
        this_hand_size = hand_size if i == player_id else (ai_hand_size if ai_hand_size is not None else hand_size)
        player.commander.setup()
        player.commander.set_owner(player)
        player.card_w = card_w
        player.card_h = card_h
        player.draw(this_hand_size)
        for card in player.hand:
            card.set_w(card_w)
            card.set_h(card_h)
        player.set_mana(0)

        player.commander.set_w(card_w)
        player.commander.set_h(card_h)

        player.commander.set_x(player.commander_position[0])
        player.commander.set_y(player.commander_position[1])

    # whoever goes first gets the opening mana
    game.turn = starting_player
    game.turn_player = starting_player
    game.players[starting_player].set_mana(mana)
    game.players[starting_player].draw()

    return game

def do_ai(hand):
    """
    Description:
    The original AI from before the state machine existed. Randomly plays roughly
    half the hand. Completely replaced by the ai_phase loop in run_big_game.
    card.valid is never set to True by anything, so this always returns an empty
    list regardless of the hand.

    Parameters:
        hand (list): the AI's hand of Card objects, which it will largely ignore

    Returns:
        list: a list containing one empty list
    """
    ai_instructions = []
    pre_round = []
    for card in hand:
        if randint(0, 1) == 1 and card.valid:
            pre_round.append(card)
    ai_instructions.append(pre_round)

    return ai_instructions