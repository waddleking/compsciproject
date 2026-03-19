# for ngrok: python client.py 0.tcp.ngrok.io 12345
import pygame, socket, pickle, struct, sys, threading
from collections import defaultdict
from classes import Button, Text, Particle
from main_classes import Card
from draw_ui import draw_background
from deck_manager import load_deck_data

SERVER_IP = sys.argv[1] if len(sys.argv) > 1 else input("server ip:")
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else int(input("port:"))

POLL_INTERVAL = 10
STARTING_PLAYER = 0


# binary stuff
def send_msg(sock, data):
    sock.sendall(struct.pack(">I", len(data)) + data)

def recv_msg(sock):
    hdr = b""
    while len(hdr) < 4:
        chunk = sock.recv(4 - len(hdr))
        if not chunk: return None
        hdr += chunk
    n = struct.unpack(">I", hdr)[0]
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(min(65536, n - len(buf)))
        if not chunk: return None
        buf += chunk
    return buf

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((SERVER_IP, PORT))
        # receive player id
        self.p_id = pickle.loads(recv_msg(self.client))
        # send our deck to the server, same format as player_data.json
        data = load_deck_data()
        send_msg(self.client, pickle.dumps({"commander": data["commander"], "deck": data["deck"]}))

    def send(self, data):
        try:
            send_msg(self.client, pickle.dumps(data))
            raw = recv_msg(self.client)
            return pickle.loads(raw) if raw else None
        except Exception as e:
            print(e)
            return None


def apply_state(response, game, pending_events, player_id, opp_id, y_positions, commander_positions, deck_positions, mana_positions, card_w, card_h, resolution_sf):
    # takes a server response and applies it
    # returns the updated game and pending_events
    if response is None: return game, pending_events

    # all this because the cards kept resetting their position
    pos_by_fp = defaultdict(list)
    if game is not None:
        for pi, p in enumerate(game.players):
            for c in p.hand + p.active:
                pos_by_fp[(pi, c.name, c.cost)].append((c.x, c.y))

    game = response["game"]
    pending_events = list(pending_events) + response.get("events", [])

    # server always has player 0 at the bottom and player 1 at the top.
    # remap so our player_id is always index 0
    game.players[player_id].y = y_positions[0]
    game.players[opp_id].y = y_positions[1]
    game.players[player_id].commander_position = commander_positions[0]
    game.players[opp_id].commander_position = commander_positions[1]
    game.players[player_id].commander.set_x(commander_positions[0][0]).set_y(commander_positions[0][1])
    game.players[opp_id].commander.set_x(commander_positions[1][0]).set_y(commander_positions[1][1])
    game.players[player_id].deck_position = deck_positions[0]
    game.players[opp_id].deck_position = deck_positions[1]
    game.players[player_id].mana_position = mana_positions[0]
    game.players[opp_id].mana_position = mana_positions[1]
    game.players[player_id].set_main_character(True)
    game.players[opp_id].set_main_character(False)

    for i, p in enumerate(game.players):
        p.card_w, p.card_h = card_w, card_h
        p.commander.set_w(card_w).set_h(card_h)
        for c in p.hand:
            c.set_w(card_w).set_h(card_h)
            c.set_hidden(i != player_id)
        for c in p.active:
            c.set_w(card_w).set_h(card_h)
            c.set_hidden(False)
        for c in p.deck:
            c.set_w(card_w).set_h(card_h)

    # restore positions
    fp_used = defaultdict(int)
    for pi, p in enumerate(game.players):
        for c in p.hand + p.active:
            fp  = (pi, c.name, c.cost)
            idx = fp_used[fp]
            saved = pos_by_fp[fp]
            if idx < len(saved):
                c.x, c.y = saved[idx]
                fp_used[fp] = idx + 1
            else:
                c.x *= resolution_sf[0]
                c.y *= resolution_sf[1]

    # commander.draw() calls transform.scale(self.image) unconditionally so it crashes on None.
    # card.draw() checks for None so cards are fine
    for p in game.players:
        if p.commander.image is None:
            try:
                p.commander.image = pygame.image.load(p.commander.image_string).convert_alpha()
                p.commander.back_image = pygame.image.load(p.commander.back_image_string).convert_alpha()
            except Exception as e:
                print(f"commander image load failed: {e}")

    return game, pending_events


def run_mp_game():
    pygame.init()
    res = (pygame.display.Info().current_w, pygame.display.Info().current_h)
    screen = pygame.display.set_mode(res, pygame.RESIZABLE)
    pygame.display.set_caption("sus & spells")

    color_font = (255, 255, 255)
    color_light = (170, 170, 170)
    color_dark = (100, 100, 100)
    color_invalid = (130, 70, 70)
    color_background = [100, 140, 100]
    current_background = color_background

    small_font = pygame.font.SysFont('Arial', 25)
    big_font = pygame.font.SysFont('Arial', 100)
    particle_font = pygame.font.SysFont('Arial', 80)

    waiting_font = pygame.font.SysFont('Arial', 50)

    resolution_sf = (res[0]/1440, res[1]/960)



    players = 2
    card_g = int(10 * resolution_sf[0])
    card_w = int(125 * resolution_sf[0])
    card_h = int(175 * resolution_sf[1])
    base_card = Card(w=card_w, h=card_h, hidden=True)

    y_positions = [res[1]-(card_g+card_h), card_g]
    deck_positions = [(card_w, res[1]-2*(card_g+card_h)), (res[0]-2*(card_g+card_w), 2*(card_g+card_h)-card_h)]
    mana_positions = [(card_w/2, res[1]-1.5*card_h), (res[0]-(card_g+card_w/2), 1.5*card_h)]
    commander_positions = [(res[0]-2*(card_g+card_w), res[1]-2*(card_g+card_h)), (card_w, 2*(card_g+card_h)-card_h)]

    end_button = Button(1.5*card_w, res[1]/2, int(100*resolution_sf[0]), int(50*resolution_sf[1]), "end", small_font, color_font, color_light, color_dark, color_invalid)
    print(f"connecting to {SERVER_IP}:{PORT}")
    n = Network()
    player_id = n.p_id
    opp_id = 1 - player_id
    clock = pygame.time.Clock()
    print(f"connected as player {player_id + 1}, deck sent")

    result = None
    game_ended = False
    connected = True
    poll_timer = 0

    selecting = None
    selected_card = None
    selected_source = None
    selected_target = None
    selected_card_idx = None
    selected_source_idx = None

    particles = []
    spell_notifications = []
    pending_events = []

    anim_type = "player_change"
    anim_bool = True
    anim_temp = None
    anim_max = 150
    anim_h = int(150 * resolution_sf[1])
    anim_y = res[1]/2 - anim_h/2
    anim_fade = 0

    game = None

    # for convenience
    layout = (player_id, opp_id, y_positions, commander_positions, deck_positions, mana_positions, card_w, card_h, resolution_sf)

    # server blocks handle() until both decks are in and the game is built, so n.send()
    # will block here too waiting for a reply. fire on a background thread so pygame
    # keeps drawing the waiting screen instead of freezing
    # __setitem__ is just list[i] = x
    # also I just kinda wanted to use more threads because I might as well
    result_box = [None]
    fetch_thread = threading.Thread(target=lambda: result_box.__setitem__(0, n.send({"type": "get"})), daemon=True)
    fetch_thread.start()

    while fetch_thread.is_alive():
        clock.tick(30)
        screen.fill((30, 30, 30))
        Text(res[0]//2, res[1]//2 - 40, 0, 0, f"connected as player {player_id + 1}", waiting_font, color_font, None, False).draw(screen)
        Text(res[0]//2, res[1]//2 + 20, 0, 0, "waiting for opponent...", waiting_font, (180, 180, 180), None, False).draw(screen)
        pygame.display.update()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: 
                pygame.quit()
                return

    game, pending_events = apply_state(result_box[0], game, pending_events, *layout)


    while connected:
        clock.tick(60)
        mouse = pygame.mouse.get_pos()

        # apply_state removes like all of the objects
        if game:
            me = game.players[player_id]
            if selected_card_idx is not None:
                selected_card = me.active[selected_card_idx] if selected_card_idx < len(me.active) else None
                if selected_card is None: selected_card_idx = None
            if selected_source_idx is not None:
                selected_source = me.active[selected_source_idx] if selected_source_idx < len(me.active) else None
                if selected_source is None: selected_source_idx = selecting = None

        # big_game stuff
        for ev in pending_events:
            if ev["type"] == "particle":
                px = ev["x"] * resolution_sf[0]
                py = ev["y"] * resolution_sf[1]
                p = Particle(px, py, ev["value"], particle_font, ev["color"], ev["color"])
                particles.append(p)
            elif ev["type"] == "spell":
                spell_notifications.append({"name": ev["name"], "player": ev["player"], "fade": 255})
            elif ev["type"] == "turn_change":
                anim_type = "player_change"
                anim_bool = True
                anim_fade = 0
                anim_max = 150
                anim_h = int(150 * resolution_sf[1])
                anim_y = res[1]/2 - anim_h/2
        pending_events.clear()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: 
                pygame.quit()
                return

            if ev.type == pygame.KEYDOWN or ev.type == pygame.MOUSEBUTTONDOWN:
                if game_ended:
                    return result

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE: return "menu"
                if ev.key == pygame.K_TAB and game:
                    for player in game.players:
                        for card in player.hand: card.set_hidden(False)

            if ev.type == pygame.MOUSEBUTTONDOWN:
                if result == None:
                    if game.turn_player == player_id:
                        if anim_type == None and end_button.touching():
                            game, pending_events = apply_state(n.send({"type": "end_turn"}), game, pending_events, *layout)
                            selected_card = selected_card_idx = selected_source = selected_source_idx = selecting = None

                        if selecting == None:
                            if selected_card is not None and selected_card.action_button is not None and selected_card.action_button.touching():
                                selected_source = selected_card
                                selected_source_idx = selected_card_idx
                                selecting = selected_card.selection_type
                                selected_card = selected_card_idx = None
                                if selecting == "":
                                    game, pending_events = apply_state(n.send({"type": "action_self", "source": selected_source_idx}), game, pending_events, *layout)
                                    selecting = selected_source = selected_source_idx = None
                            elif selected_card is not None and me.mana >= selected_card.retreat_cost and selected_card.retreat_button is not None and selected_card.retreat_button.touching():
                                game, pending_events = apply_state(n.send({"type": "retreat", "index": selected_card_idx}), game, pending_events, *layout)
                                selected_card = selected_card_idx = selected_source = selected_source_idx = None
                            else:
                                selected_card = selected_card_idx = None
                                for i, card in enumerate(me.active):
                                    if card.touching(mouse) and card.actions > 0:
                                        selected_card = card
                                        selected_card_idx = i

                        elif selecting == "enemy":
                            for player_num in range(players):
                                if player_num != player_id:
                                    highest_taunt = 0
                                    for card in game.players[player_num].active:
                                        if card.taunt > highest_taunt:
                                            highest_taunt = card.taunt
                                    if selected_source and selected_source.ignore_taunt:
                                        highest_taunt = 0

                                    for i, card in enumerate(game.players[player_num].active):
                                        if card.touching(mouse) and card.taunt >= highest_taunt:
                                            game, pending_events = apply_state(n.send({"type": "action", "source": selected_source_idx, "target_player": player_num, "target": i}), game, pending_events, *layout)

                                    if game.players[player_num].commander.touching(mouse) and game.players[player_num].commander.taunt >= highest_taunt:
                                        game, pending_events = apply_state(n.send({"type": "action", "source": selected_source_idx, "target_player": player_num, "target": None}), game, pending_events, *layout)

                            selecting = selected_source = selected_source_idx = selected_card = selected_card_idx = None

                        elif selecting == "hand":
                            for i, card in enumerate(me.hand):
                                if card.touching(mouse):
                                    game, pending_events = apply_state(n.send({"type": "action_hand", "source": selected_source_idx, "target": i}), game, pending_events, *layout)
                            selecting = selected_source = selected_source_idx = selected_card = selected_card_idx = None

                        for card in me.hand:
                            if len(me.active) < me.max_active or card.spell:
                                if card.touching(mouse) and me.mana >= card.cost and card.actions > 0 and (game.turn - STARTING_PLAYER >= game.num_players or not card.spell):
                                    game, pending_events = apply_state(n.send({"type": "play_hand", "index": me.hand.index(card)}), game, pending_events, *layout)

        if game and game.turn_player != player_id and result is None:
            poll_timer -= 1
            if poll_timer <= 0:
                response = n.send({"type": "get"})
                if response is None: connected = False
                else: game, pending_events = apply_state(response, game, pending_events, *layout)
                poll_timer = POLL_INTERVAL

        current_background = draw_background(screen, current_background, color_background)

        if result == None:
            for player in game.players:
                hand = player.hand
                pgap = card_g
                while len(hand)*(pgap+card_w) > res[0]: pgap -= max(1, int(5*resolution_sf[0]))
                for i in range(len(hand)):
                    card = hand[i]
                    card.draw(screen)
                    card.desired_x = (res[0]-((card_w+pgap)*len(hand)))/2+((card_w+pgap)*i)+(pgap/2)
                    if card.desired_x is not None:
                        if card.x != card.desired_x:
                            distance = card.desired_x - card.x
                            if distance**2 < 50 * resolution_sf[0]**2: card.x = card.desired_x
                            else: card.x += distance/5
                    card.desired_y = player.y
                    if card.desired_y is not None:
                        if card.y != card.desired_y:
                            distance = card.desired_y - card.y
                            if distance**2 < 50 * resolution_sf[1]**2: card.y = hand[i].desired_y
                            else: card.y += distance/5
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
                while len(hand)*(pgap+card_w) > res[0]: pgap -= max(1, int(5*resolution_sf[0]))
                for i in range(len(hand)):
                    card = hand[i]
                    card.desired_x = (res[0]-((card_w+pgap)*len(hand)))/2+((card_w+pgap)*i)+(pgap/2)
                    if card.desired_x is not None:
                        if card.x != card.desired_x:
                            distance = card.desired_x - card.x
                            if distance**2 < 50 * resolution_sf[0]**2: card.x = card.desired_x
                            else: card.x += distance/5
                    card.desired_y = player.y
                    if card.desired_y > res[1]/2: card.desired_y -= card_h+card_g
                    else: card.desired_y += card_h+card_g
                    if (card.touching(mouse) and card.actions > 0) or selected_card == card or selected_source == card:
                        if card.desired_y > res[1]/2: card.desired_y -= card_g/2
                    if card.desired_y is not None:
                        if card.y != card.desired_y:
                            distance = card.desired_y - card.y
                            if distance**2 < 50 * resolution_sf[1]**2: card.y = hand[i].desired_y
                            else: card.y += distance/5
                    card.draw(screen)
                    hand[i] = card
                player.active = hand

            if game.turn_player == player_id:
                end_button.draw(screen)

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
                    anim_y = res[1]/2 - anim_h/2

        if anim_type == "player_win":
            if anim_fade < 255: anim_fade += 3
            if anim_fade >= anim_max: anim_temp = anim_max
            else: anim_temp = anim_fade
            overlay = pygame.Surface((res[0], anim_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, anim_temp))
            screen.blit(overlay, (0, anim_y))
            Text(res[0]/2, res[1]/2, 0, 0, f"player {result+1} victory", big_font, color_font, None, False).set_alpha(anim_temp*255/anim_max).draw(screen)
            if anim_fade == 255: game_ended = True
            if anim_fade <= 0: anim_type = None

        if anim_type == "player_change":
            if anim_fade >= 200: anim_bool = False
            if anim_bool: anim_fade += 5
            else: anim_fade -= 5
            if anim_fade >= anim_max: anim_temp = anim_max
            else: anim_temp = anim_fade
            overlay = pygame.Surface((res[0], anim_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, anim_temp))
            screen.blit(overlay, (0, anim_y))
            Text(res[0]/2, res[1]/2, 0, 0, f"player {game.turn_player+1}", big_font, color_font, None, False).set_alpha(anim_temp*255/anim_max).draw(screen)
            if anim_fade <= 0: anim_type = None

        for particle in particles:
            particle.draw(screen)
            if particle.alpha < 0: particles.remove(particle)

        for pending in game.pending_spell_notifications:
            spell_notifications.append({"name": pending["name"], "player": pending["player"], "fade": 255})
        game.pending_spell_notifications.clear()

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
            if notif["fade"] <= 0: spell_notifications.remove(notif)

        pygame.display.update()

    screen.fill((20, 20, 20))
    Text(res[0]//2, res[1]//2, 0, 0, "lost connection to server", big_font, (255, 80, 80), None, False).draw(screen)
    pygame.display.update()
    pygame.time.wait(3000)
    pygame.quit()


if __name__ == "__main__":
    run_mp_game()
