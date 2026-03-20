# run this first, then both players run client.py
# for internet play without port forwarding i have to use ngrok

import socket, pickle, struct, pygame, threading, time
import card_classes, commander_classes
from main_classes import Game, Player

PORT = 5555
MANA = 3
HAND_SIZE = 5
MAX_ACTIVE = 6
MAX_HAND = 8
STARTING_PLAYER = 0

# idk why but pygame runs the resolution at half of my actual resolution
REF_W, REF_H = 1440, 960
REF_CW, REF_CH, REF_CG = 125, 175, 10

pygame.init()
pygame.display.set_mode((100, 100))  # doesn't actually show anything, just needed for font/image loading


def send_msg(sock, data):
    """
    Description:
    Sends a length-prefixed message over a TCP socket.

    TCP is a stream protocol not a packet one, so a single send() might arrive
    as multiple recv() chunks on the other end. Prefixing with the 4-byte
    payload length lets recv_msg know exactly when it has the full message.
    Discovered this was necessary after seeing the client intermittently
    receive corrupted game states when the payload got large enough to split.

    Parameters:
        sock (socket.socket): the tcp socket to send on
        data (bytes): the already-serialised payload to send
    """
    sock.sendall(struct.pack(">I", len(data)) + data)

def recv_msg(sock):
    """
    Description:
    Reads exactly one length-prefixed message from a TCP socket.
    Waits until the full payload has arrived. Returns None if the
    connection was closed by the other end.

    Parameters:
        sock (socket.socket): the tcp socket to read from

    Returns:
        bytes or None: the complete payload, or None on disconnect
    """
    hdr = b""
    while len(hdr) < 4:
        chunk = sock.recv(4 - len(hdr))
        if not chunk: return None
        hdr += chunk
    n = struct.unpack(">I", hdr)[0] # unsigned int
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(min(65536, n - len(buf))) # 64kb
        if not chunk: return None
        buf += chunk
    return buf


# pygame fonts and surfaces can't be pickled
unpicklable = (
    "font", "font_desc", "particle_font",
    "image", "back_image",
    "cached_image", "cached_back_image", "cached_action_image",
    "action_button", "retreat_button",
)

def strip(obj):
    """
    Description:
    Saves and clears all unpicklable pygame fields on a card or commander.

    Parameters:
        obj: a Card or Commander object

    Returns:
        saved (dict): field name and original value for everything that was stripped
    """
    saved = {}
    for f in unpicklable:
        if hasattr(obj, f):
            saved[f] = getattr(obj, f)
            setattr(obj, f, None)
    return saved

def restore(obj, saved):
    """
    Description:
    Puts stripped pygame fields back onto a card or commander after pickling.

    Parameters:
        obj: the Card or Commander to restore
        saved (dict): the dict returned by strip()
    """
    for f, v in saved.items():
        setattr(obj, f, v)

def make_response(p_id):
    """
    Description:
    Builds the pickled response to send back to a client after any request.
    Drains this player's event queue (particles, spell banners, turn-change
    signals), strips all pygame objects from the game, pickles both together,
    then immediately restores the game so the server can keep running.

    Parameters:
        p_id (int): 0 or 1, which player's event queue to drain

    Returns:
        bytes: pickled
    """
    player_events = list(event_queues[p_id])
    event_queues[p_id].clear()

    all_saved = []
    for p in game.players:
        row = {"cmd": strip(p.commander), "cards": []}
        for zone in (p.hand, p.active, p.deck):
            for c in zone:
                row["cards"].append(strip(c))
        all_saved.append(row)

    data = pickle.dumps({"game": game, "events": player_events})

    for i, p in enumerate(game.players):
        restore(p.commander, all_saved[i]["cmd"])
        j = 0
        for zone in (p.hand, p.active, p.deck):
            for c in zone:
                restore(c, all_saved[i]["cards"][j])
                j += 1
    return data


# client queues for particles, spell banners, and turn change banners
event_queues = {0: [], 1: []}

def emit(event):
    """
    Description:
    Pushes an event into both player queues

    Parameters:
        event (dict): the event dict, e.g. {"type": "turn_change"}
    """
    event_queues[0].append(event)
    event_queues[1].append(event)

def flip_for_p1(x, y):
    """
    Description:
    Converts a reference-layout coordinate into its mirrored equivalent for
    player 1's client. Player 1's board is a flip of player 0's,
    so every mirrored pair of positions sums to (W, H).

    Parameters:
        x (float): reference x coordinate
        y (float): reference y coordinate

    Returns:
        (x, y) (tuple): flipped coordinates for player 1's perspective
    """
    W, H, cw = REF_W, REF_H, REF_CW
    if x < cw * 2 or x > W - cw * 2:
        right = x > W / 2
        bottom = y > H / 2
        if right == bottom:
            return 1420 - x, H - y
        else:
            return W - x, H - y
    else:
        return x, H - y

def capture_particles(particles):
    """
    Description:
    Converts a list of Particle objects into event dicts and pushes
    them into both players' queues.

    Storing p.color directly was necessary because string particles like "Alchemy" and
    "Economics" use white (self.color_font) while damage/heal numbers use red or
    gree.

    Parameters:
        particles (list): Particle objects returned by card/commander on actions
    """
    for p in particles:
        event_queues[0].append({"type": "particle", "x": p.x, "y": p.y, "value": p.value, "color": p.color})
        fx, fy = flip_for_p1(p.x, p.y)
        event_queues[1].append({"type": "particle", "x": fx, "y": fy, "value": p.value, "color": p.color})

def drain_spells():
    """
    Description:
    Moves any spell notifications queued by Card.play() into both event queues,
    then clears the game's list. Just big_game.py logic copied for draining
    game.pending_spell_notifications into the local spell_notifications list
    each frame.
    also clear() does it in place so no returning
    """
    for notif in game.pending_spell_notifications:
        emit({"type": "spell", "name": notif["name"], "player": notif["player"]})
    game.pending_spell_notifications.clear()


def sync_card_positions():
    """
    Description:
    Updates every card's server-side x,y to the correct reference layout position.

    Player.draw() spawns cards at deck_position and nothing moves them after that,
    so server-side card.x/y are permanently stuck at the deck corner. Particles
    are created at target.x/y inside on_action(), so without this call every
    particle would spawn at the deck corner regardless of where the card is on
    screen. Ask me how I know.

    Uses the same position formula as big_game.py.
    """
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
    """
    Description:
    Same logic as get_deck() in deck_manager.py

    Parameters:
        deck_data (dict): {"commander": "Biden", "deck": ["Amogus", "Pump", ...]}

    Returns:
        deck (list): [Commander, Card, ...] fully setup objects
    """
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
    """
    Description:
    Builds and returns a fully initialised Game object from two pre-built deck
    lists. Basically start_big_game() from big_game.py but uses the server's
    fixed reference resolution rather than the client's screen size. Positions
    are overridden by each client in apply_state() after receiving state, so
    the actual values here only need to be consistent with sync_card_positions().

    Parameters:
        decks (list): [[Commander, Card, ...], [Commander, Card, ...]]

    Returns:
        g (Game): fully initialised
    """
    W, H = REF_W, REF_H
    cw, ch, cg = REF_CW, REF_CH, REF_CG

    y_positions = [H-(cg+ch), cg]
    deck_positions = [(cw, H-2*(cg+ch)), (W-2*(cg+cw), 2*(cg+ch)-ch)]
    mana_positions = [(cw/2, H-1.5*ch), (W-(cg+cw/2), 1.5*ch)]
    commander_positions = [(W-2*(cg+cw), H-2*(cg+ch)), (cw, 2*(cg+ch)-ch)]

    g = Game(2, MANA)
    for i in range(2):
        p = Player(
            game=g, max_active=MAX_ACTIVE, max_hand=MAX_HAND, commander=decks[i][0], commander_position=commander_positions[i], deck=decks[i][1:], deck_position=deck_positions[i], mana_position=mana_positions[i], y=y_positions[i],
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
both_ready = threading.Event()  # set once both decks are in and the game is built
received_decks = {0: None, 1: None}


def handle(conn, p_id):
    """
    Description:
    Client handler thread. One of these runs per connected player. Implements a
    three-step handshake before the game loop:
    1. Tell the client their player id (0 or 1).
    2. Receive their deck data (commander name + card name list, same format
    as player_data.json) and store it in received_decks.
    3. Block on both_ready until the main thread has received both decks,
    built the game, and called both_ready.set().

    After the handshake the loop processes action requests from the client,
    applies them to the shared game, and sends back the full
    updated game state plus any queued events.

    The lock is held for the entire duration of each request including the
    make_response() call, because make_response() temporarily mutates the game
    (stripping pygame objects) and two threads doing this simultaneously literally
    mess up everything and ruin everything and it would all go horrible.

    Parameters:
        conn (socket.socket): the accepted client socket
        p_id (int): 0 or 1, this player's slot
    """
    # tell the client which player slot they are
    send_msg(conn, pickle.dumps(p_id))

    # receive their deck before blocking on both_ready so both threads can
    # deposit their decks and the main thread can build the game
    raw = recv_msg(conn)
    if raw is None:
        conn.close()
        return
    received_decks[p_id] = pickle.loads(raw)
    print(f"  player {p_id + 1} sent deck: {received_decks[p_id]['commander']}")

    # block here until both decks are in and start_mp_game() has run
    both_ready.wait()

    while True:
        try:
            raw = recv_msg(conn)
            if raw is None: break
            req = pickle.loads(raw)
            t = req.get("type", "get")

            with lock:
                me = game.players[p_id]
                sync_card_positions()  # keep x/y correct so particles land in the right place

                if t == "play_hand" and game.turn_player == p_id:
                    idx = req.get("index", -1)
                    if 0 <= idx < len(me.hand):
                        card = me.hand[idx]
                        capture_particles(card.play())
                        drain_spells()
                        # first-turn haste restriction – same check as big_game.py
                        if game.turn - STARTING_PLAYER < game.num_players and card.atk != 0:
                            if card in me.active: card.actions = 0

                elif t == "action" and game.turn_player == p_id:
                    si, tp, ti = req.get("source",-1), req.get("target_player",-1), req.get("target")
                    if 0 <= si < len(me.active) and 0 <= tp < len(game.players):
                        src = me.active[si]
                        opp = game.players[tp]
                        # ti=None means hit the commander, ti=int means active[ti]
                        target = opp.commander if ti is None else (opp.active[ti] if 0 <= ti < len(opp.active) else None)
                        if target:
                            capture_particles(src.on_action(target))
                            drain_spells()

                elif t == "action_self" and game.turn_player == p_id:
                    # cards with selection_type "" fire on_action with no target
                    si = req.get("source", -1)
                    if 0 <= si < len(me.active):
                        capture_particles(me.active[si].on_action())
                        drain_spells()

                elif t == "action_hand" and game.turn_player == p_id:
                    # cards like Net that target one of the player's own hand cards
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

                # "get" and anything unrecognised just returns current state with no changes
                send_msg(conn, make_response(p_id))

        except Exception as e:
            print(f"player {p_id} error: {e}")
            break

    print(f"player {p_id} disconnected")
    conn.close()


srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # allows restart without the port timing out
srv.bind(("0.0.0.0", PORT))   # 0.0.0.0 = listen on all interfaces, not just localhost
srv.listen(2)

try: local_ip = socket.gethostbyname(socket.gethostname())
except: local_ip = "unknown"
print(f"server on {local_ip}:{PORT}")
print("waiting for 2 players...\n")

threads = []
for pid in range(2):
    conn, addr = srv.accept()
    print(f"  player {pid+1} connected from {addr[0]}")
    t = threading.Thread(target=handle, args=(conn, pid), daemon=True)
    t.start()
    threads.append(t)

# spin until both handle() threads have deposited their deck data, build the game,
# then unblock both threads simultaneously
while received_decks[0] is None or received_decks[1] is None:
    time.sleep(0.05)

game = start_mp_game([deck_from_data(received_decks[0]), deck_from_data(received_decks[1])])
both_ready.set()
print("both players connected and decks loaded – game running.")
while True: time.sleep(1)