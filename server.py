# ngrok tcp 5555 or something i have no clue
import socket, pickle, struct, pygame, threading, time
import card_classes, commander_classes
from main_classes import Game, Player

PORT = 5555
MANA = 3
HAND_SIZE = 5
MAX_ACTIVE = 6
MAX_HAND = 8
STARTING_PLAYER = 0

REF_W, REF_H = 1440, 960
REF_CW, REF_CH, REF_CG  = 125, 175, 10

pygame.init()
pygame.display.set_mode((100, 100))


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


unpicklable = (
    "font", "font_desc", "particle_font",
    "image", "back_image",
    "cached_image", "cached_back_image", "cached_action_image",
    "action_button", "retreat_button",
)

def strip(obj):
    saved = {}
    for f in unpicklable:
        if hasattr(obj, f):
            saved[f] = getattr(obj, f)
            setattr(obj, f, None)
    return saved

def restore(obj, saved):
    for f, v in saved.items():
        setattr(obj, f, v)

def make_response(p_id):
    my_events = list(event_queues[p_id])
    event_queues[p_id].clear()

    all_saved = []
    for p in game.players:
        row = {"cmd": strip(p.commander), "cards": []}
        for zone in (p.hand, p.active, p.deck):
            for c in zone:
                row["cards"].append(strip(c))
        all_saved.append(row)

    data = pickle.dumps({"game": game, "events": my_events})

    for i, p in enumerate(game.players):
        restore(p.commander, all_saved[i]["cmd"])
        j = 0
        for zone in (p.hand, p.active, p.deck):
            for c in zone:
                restore(c, all_saved[i]["cards"][j])
                j += 1
    return data


event_queues = {0: [], 1: []}

def emit(event):
    event_queues[0].append(event)
    event_queues[1].append(event)

def flip_for_p1(x, y):
    W, H, cw = REF_W, REF_H, REF_CW
    if x < cw * 2 or x > W - cw * 2:
        right  = x > W / 2
        bottom = y > H / 2
        if right == bottom:
            return 1420 - x, H - y
        else:
            return W - x, H - y
    else:
        return x, H - y

def capture_particles(particles):
    for p in particles:
        event_queues[0].append({"type": "particle", "x": p.x, "y": p.y, "value": p.value, "color": p.color})
        fx, fy = flip_for_p1(p.x, p.y)
        event_queues[1].append({"type": "particle", "x": fx, "y": fy, "value": p.value, "color": p.color})

def drain_spells():
    for notif in game.pending_spell_notifications:
        emit({"type": "spell", "name": notif["name"], "player": notif["player"]})
    game.pending_spell_notifications.clear()


def sync_card_positions():
    W, H = REF_W, REF_H
    cw, ch, cg = REF_CW, REF_CH, REF_CG
    y_positions = [H-(cg+ch), cg]

    for pi, p in enumerate(game.players):
        n = len(p.hand)
        sx = (W - (cw+cg)*n) / 2
        for ci, c in enumerate(p.hand):
            c.x = sx + (cw+cg)*ci + cg/2
            c.y = y_positions[pi]

        n = len(p.active)
        sx = (W - (cw+cg)*n) / 2
        ay = y_positions[pi] - (ch+cg) if y_positions[pi] > H/2 else y_positions[pi] + (ch+cg)
        for ci, c in enumerate(p.active):
            c.x = sx + (cw+cg)*ci + cg/2
            c.y = ay


def deck_from_data(deck_data):
    # reconstructs a [Commander, Card, ...] list from the name strings the client sent.
    # same logic as get_deck() in deck_manager.py
    deck = []
    comm_class = getattr(commander_classes, deck_data["commander"])
    deck.append(comm_class().setup())
    for name in deck_data["deck"]:
        try:
            card_class = getattr(card_classes, name)
            deck.append(card_class().setup())
        except AttributeError:
            print(f"card class '{name}' not found, skipping")
    return deck

def start_mp_game(decks):
    W, H = REF_W, REF_H
    cw, ch, cg = REF_CW, REF_CH, REF_CG

    y_positions = [H-(cg+ch), cg]
    deck_positions = [(cw, H-2*(cg+ch)), (W-2*(cg+cw), 2*(cg+ch)-ch)]
    mana_positions = [(cw/2, H-1.5*ch), (W-(cg+cw/2), 1.5*ch)]
    commander_positions = [(W-2*(cg+cw), H-2*(cg+ch)), (cw, 2*(cg+ch)-ch)]

    g = Game(2, MANA)
    for i in range(2):
        p = Player(
            game=g, max_active=MAX_ACTIVE, max_hand=MAX_HAND,
            commander=decks[i][0], commander_position=commander_positions[i],
            deck=decks[i][1:], deck_position=deck_positions[i],
            mana_position=mana_positions[i], y=y_positions[i],
        )
        p.commander.setup()
        p.commander.set_owner(p)
        p.commander.set_w(cw).set_h(ch)
        p.commander.set_x(commander_positions[i][0]).set_y(commander_positions[i][1])
        p.card_w, p.card_h = cw, ch
        p.draw(HAND_SIZE)
        for card in p.hand: card.set_w(cw).set_h(ch)
        p.set_mana(0)
        g.add_player(p)

    g.turn = STARTING_PLAYER
    g.turn_player = STARTING_PLAYER
    g.players[STARTING_PLAYER].set_mana(MANA)
    g.players[STARTING_PLAYER].draw()
    return g


game = None
lock = threading.Lock()
both_ready = threading.Event()
received_decks = {0: None, 1: None}  # filled during handshake before game is built


def handle(conn, p_id):
    # step 1: tell the client their player id
    send_msg(conn, pickle.dumps(p_id))

    # step 2: receive their deck data (commander name + card name list)
    # this arrives before both_ready is set so both threads can hand in their
    # decks before the game is built
    raw = recv_msg(conn)
    if raw is None:
        conn.close(); return
    received_decks[p_id] = pickle.loads(raw)
    print(f"  player {p_id + 1} sent deck: {received_decks[p_id]['commander']}")

    # step 3: wait until both decks have arrived and the game has been built
    both_ready.wait()

    while True:
        try:
            raw = recv_msg(conn)
            if raw is None: break
            req = pickle.loads(raw)
            t   = req.get("type", "get")

            with lock:
                me = game.players[p_id]
                sync_card_positions()

                if t == "play_hand" and game.turn_player == p_id:
                    idx = req.get("index", -1)
                    if 0 <= idx < len(me.hand):
                        card = me.hand[idx]
                        capture_particles(card.play())
                        drain_spells()
                        if game.turn - STARTING_PLAYER < game.num_players and card.atk != 0:
                            if card in me.active: card.actions = 0

                elif t == "action" and game.turn_player == p_id:
                    si, tp, ti = req.get("source",-1), req.get("target_player",-1), req.get("target")
                    if 0 <= si < len(me.active) and 0 <= tp < len(game.players):
                        src = me.active[si]
                        opp = game.players[tp]
                        tgt = opp.commander if ti is None else (opp.active[ti] if 0 <= ti < len(opp.active) else None)
                        if tgt:
                            capture_particles(src.on_action(tgt))
                            drain_spells()

                elif t == "action_self" and game.turn_player == p_id:
                    si = req.get("source", -1)
                    if 0 <= si < len(me.active):
                        capture_particles(me.active[si].on_action())
                        drain_spells()

                elif t == "action_hand" and game.turn_player == p_id:
                    si, ti = req.get("source",-1), req.get("target",-1)
                    if 0 <= si < len(me.active) and 0 <= ti < len(me.hand):
                        capture_particles(me.active[si].on_action(me.hand[ti]))
                        drain_spells()

                elif t == "retreat" and game.turn_player == p_id:
                    idx = req.get("index", -1)
                    if 0 <= idx < len(me.active): me.active[idx].retreat()

                elif t == "end_turn" and game.turn_player == p_id:
                    capture_particles(game.next_turn())
                    drain_spells()
                    emit({"type": "turn_change"})

                send_msg(conn, make_response(p_id))

        except Exception as e:
            print(f"player {p_id} error: {e}")
            import traceback; traceback.print_exc()
            break

    print(f"player {p_id} disconnected")
    conn.close()


srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("0.0.0.0", PORT))
srv.listen(2)

try:    local_ip = socket.gethostbyname(socket.gethostname())
except: local_ip = "unknown"
print(f"server on {local_ip}:{PORT}")
print("for ngrok: run 'ngrok tcp 5555', share the printed address with the other player")
print("waiting for 2 players...\n")

threads = []
for pid in range(2):
    conn, addr = srv.accept()
    print(f"  player {pid+1} connected from {addr[0]}")
    t = threading.Thread(target=handle, args=(conn, pid), daemon=True)
    t.start()
    threads.append(t)

# wait until both handle() threads have deposited their deck data
# (they block on recv_msg before reaching both_ready.wait(), so by the time
# we get here both threads are either still receiving or have already stored their deck)
while received_decks[0] is None or received_decks[1] is None:
    time.sleep(0.05)

# build the game from both players' actual decks, then unblock both threads
game = start_mp_game([deck_from_data(received_decks[0]), deck_from_data(received_decks[1])])
both_ready.set()
print("both players connected and decks loaded – game running.")
while True: time.sleep(1)