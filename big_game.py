import pygame
from draw_ui import draw_chips_ui, draw_card_ui, draw_win_fail_screen, draw_background
from betting import run_bets
from classes import Button, Text
from main_classes import Game, Player, Card
from random import randint
from menu import run_game_menu
from setup import setup_cards

def run_big_game(settings, decks, hp, mana, hand_size, max_active, cost):
    screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid = settings
    button_available = False #0 for cards

    
    players = randint(2, 2)
    player_id = 0
    result = None
    overlay_y = -res[1]
    card_g = 10
    card_w = 125
    card_h = 175
    base_card = Card(w=card_w, h=card_h, hidden=True)
    end_button = Button(1.5*card_w, res[1]/2+50, 100, 50, "end", small_font, color_font, color_light, color_dark, color_invalid)

    y_positions = [res[1]-(card_g+card_h), card_g]
    deck_positions = [(card_w, res[1]-2*card_h), (res[0]-2*(card_g+card_w), 1*card_h)]
    mana_positions = [(card_w/2, res[1]-1.5*card_h), (res[0]-(card_g+card_w/2), 1.5*card_h)]
    commander_positions = [(res[0]-2*(card_g+card_w), res[1]-2*card_h), (card_w, 1*card_h)]

    selecting = None
    selected_card = None
    selected_source = None
    selected_target = None

    particles = []

    anim_type = None
    anim_bool = None
    anim_temp = None
    anim_max = None
    anim_x = None
    anim_y = None
    anim_w = None
    anim_h = None
    anim_fade = None

    game = start_big_game(res, decks, players, player_id, card_w, card_h, card_g, mana, hand_size, max_active, y_positions, deck_positions, mana_positions, commander_positions)
    result = None

    print("game start")
    anim_type = "player_change"
    anim_bool = True
    anim_fade = 0
    anim_max = 150
    anim_h = 150
    anim_y = res[1]/2-anim_h/2

    while True:

        mouse = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: 
                pygame.quit() 

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    option = run_game_menu(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid)
                    # if option == "give up":
                    #     result == "epic fail"
                    #     chips = 0
                    #     overlay_y = 0
                    # elif option == "load":
                    #     return option
                    if option == "menu":
                        return option
                    
            if ev.type == pygame.KEYDOWN or ev.type == pygame.MOUSEBUTTONDOWN: 
                    #restart
                if overlay_y == 0:
                    return result
                
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if result == None:
                    #player actions
                    if anim_type == None and game.turn_player == player_id:
                        if anim_type == None and end_button.touching():
                            print("player turn over")
                            game.next_turn()
                            anim_type = "player_change"
                            anim_bool = True
                            anim_fade = 0
                            anim_max = 150
                            anim_h = 150
                            anim_y = res[1]/2-anim_h/2

                        #selection stuff
                        if selecting == None:
                            if selected_card != None and selected_card.action_button.touching():
                                selected_source = selected_card
                                selecting = selected_card.selection_type
                                selected_card = None
                                if selecting == "":
                                    particles.extend(selected_source.on_action())
                                    selecting = None
                                    selected_source = None
                                    selected_target = None
                                    selected_card = None
                            elif selected_card != None and selected_card.retreat_button.touching():
                                selected_card.retreat()
                                selected_card = None
                                selected_source = None
                            else:
                                selected_card = None
                                for card in game.players[player_id].active:
                                    if card.touching(mouse) and card.actions > 0:
                                        selected_card = card
                        
                        elif selecting == "enemy":
                            #
                            for player_num in range(players):
                                #find the highest taunt level
                                highest_taunt = 0
                                for card in game.players[player_num].active:
                                    if card.taunt > highest_taunt:
                                        highest_taunt = card.taunt

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


                        #play card into active
                        if len(game.players[player_id].active) < game.players[player_id].max_active:
                            for card in game.players[player_id].hand:
                                if card.touching(mouse) and game.players[player_id].mana >= card.cost and card.actions > 0:
                                    card.play()

                        #drawing
                        if len(game.players[player_id].deck) > 0 and game.players[player_id].mana > 0:
                            base_card.x, base_card.y = game.players[player_id].deck_position
                            if base_card.touching(mouse) and card.actions > 0:
                                game.players[player_id].draw(cost=cost)
                
        current_background = draw_background(screen, current_background, color_background)

        if result == None:
            #AI STUTFF AI STIA AIA AI IA AA IA IA IA IA IA IA IAI AIA  IA IAIA AI IAA IA IA IAIAIAIA IA IA IA IA IAAI
            if anim_type == None and game.turn_player != player_id:
                for i in range(game.players[game.turn_player].mana):
                    if len(game.players[game.turn_player].hand) < randint(0,hand_size*2) and game.players[game.turn_player].mana >= cost and len(game.players[game.turn_player].deck) > 0:
                        game.players[game.turn_player].draw(cost=cost)
                    elif len(game.players[game.turn_player].active) < max_active and len(game.players[game.turn_player].hand) > 0:
                        r = randint(0,len(game.players[game.turn_player].hand)-1)
                        if game.players[game.turn_player].hand[r].cost <= game.players[game.turn_player].mana:
                            game.players[game.turn_player].hand[r].play()
                            
                print(f"ai {game.turn_player} turn over")
                game.next_turn()
                anim_type = "player_change"
                anim_bool = True
                anim_fade = 0
                anim_max = 150
                anim_h = 150
                anim_y = res[1]/2-anim_h/2
            
        for player in game.players:
            #actual hand
            hand = player.hand
            pgap = card_g
            while len(hand)*(pgap+card_w) > res[0]:
                pgap -= 5
            for i in range(len(hand)):
                card = hand[i]
                card.draw(screen)
                card.desired_x = (res[0]-((card_w+pgap)*len(hand)))/2+((card_w+pgap)*i)+(pgap/2)
                if card.desired_x != None:
                    if card.x != card.desired_x:
                        distance = card.desired_x - card.x
                        if distance**2 < 50:
                            card.x = card.desired_x
                        else:
                            card.x += (distance)/5

                card.desired_y = player.y
                if card.touching(mouse) and card.actions > 0:
                    if card.desired_y > res[1]/2:
                        card.desired_y -= card_g/2
                        Text(mouse[0], mouse[1]-50, 100, 100, str(card.cost), big_font, color_font, color_light, False).draw(screen)

                if card.desired_y != None:
                    if card.y != card.desired_y:
                        distance = card.desired_y - card.y
                        if distance**2 < 50:
                            card.y = hand[i].desired_y
                        else:
                            card.y += (distance)/5
                
                
                hand[i] = card
                
            #little ui stuff, deck and commander
            if selected_card != None:
                selected_card.draw_buttons(screen)
            
            if player.commander != None:
                player.commander.draw(screen)
                Text(player.commander_position[0]+card_w/2, player.commander_position[1]-card_g*2, 0, 0, str(player.commander.hp), small_font, color_font, None, False).draw(screen)

            if len(player.deck) > 0:
                base_card.x, base_card.y = player.deck_position
                base_card.draw(screen)
                Text(player.deck_position[0]+card_w/2, player.deck_position[1]-card_g*2, 0, 0, str(len(player.deck)), small_font, color_font, None, False).draw(screen)

            Text(player.mana_position[0], player.mana_position[1], 0, 0, str(player.mana), big_font, color_font, None, False).draw(screen)

            player.hand = hand

            #active hand
            hand = player.active
            pgap = card_g
            while len(hand)*(pgap+card_w) > res[0]:
                pgap -= 5
            for i in range(len(hand)):
                card = hand[i]
                card.desired_x = (res[0]-((card_w+pgap)*len(hand)))/2+((card_w+pgap)*i)+(pgap/2)
                if card.desired_x != None:
                    if card.x != card.desired_x:
                        distance = card.desired_x - card.x
                        if distance**2 < 50:
                            card.x = card.desired_x
                        else:
                            card.x += (distance)/5

                card.desired_y = player.y

                if card.desired_y > res[1]/2:
                    card.desired_y -= card_h+card_g
                else:
                    card.desired_y += card_h+card_g

                if card.touching(mouse) and card.actions > 0:
                    if card.desired_y > res[1]/2:
                        card.desired_y -= card_g/2

                if card.desired_y != None:
                    if card.y != card.desired_y:
                        distance = card.desired_y - card.y
                        if distance**2 < 50:
                            card.y = hand[i].desired_y
                        else:
                            card.y += (distance)/5
                
                card.draw(screen)
                hand[i] = card
            player.active = hand

        if game.turn_player == player_id:
            end_button.draw(screen)

        #winning
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
                    anim_h = 150
                    anim_y = res[1]/2-anim_h/2

        #animation stuff
        for particle in particles:
            particle.draw(screen)
            if particle.alpha < 0:
                particles.remove(particle)

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

        pygame.display.update()

def start_big_game(res, decks, players, player_id, card_w, card_h, card_g, mana, hand_size, max_active, y_positions, deck_positions, mana_positions, commander_positions):
    game = Game(players, mana)

    for i in range(players):
        game.add_player(Player(max_active=max_active, commander=decks[i][0], commander_position=commander_positions[i], deck=decks[i][1:], deck_position=deck_positions[i], mana_position=mana_positions[i], y=y_positions[i]))
    game.players[player_id].set_main_character(True)

    for player in game.players:
        player.commander.setup()
        player.card_w = card_w
        player.card_h = card_h
        player.draw(hand_size)
        for card in player.hand:
            card.set_w(card_w)
            card.set_h(card_h)
        player.set_mana(0)

        player.commander.set_w(card_w)
        player.commander.set_h(card_h)

        player.commander.set_x(player.commander_position[0])
        player.commander.set_y(player.commander_position[1])

    game.players[0].set_mana(mana)

    return game

def do_ai(hand):
    ai_instructions = []
    #pre round
    pre_round = []
    for card in hand:
        if randint(0, 1) == 1 and card.valid:
            pre_round.append(card)
    ai_instructions.append(pre_round)
    #round

    return ai_instructions