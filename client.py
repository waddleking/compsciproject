import pygame
import socket
import pickle
from main_classes import Card
from classes import Text

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(("localhost", 5555))
        self.p_id = pickle.loads(self.client.recv(2048))

    def send(self, data):
        try:
            self.client.send(pickle.dumps(data))
            # Increase buffer to 2MB to handle many cards + metadata
            return pickle.loads(self.client.recv(2048 * 1024)) 
        except: return None

def hydrate(obj, big_f, small_f):
    """Restores assets to a Card or Commander object after network transfer."""
    if obj is None: return
    
    # Restore fonts required by the object's internal .draw()
    obj.font = big_f
    obj.font_desc = small_f
    
    # Load images based on the strings stored in the object
    if obj.image is None:
        try:
            # Check for standard image_string first
            if hasattr(obj, 'image_string'):
                obj.image = pygame.image.load(obj.image_string).convert_alpha()
            # If it's a card with a back (like in deck/opponent hand)
            if hasattr(obj, 'back_image_string') and obj.back_image_string:
                obj.back_image = pygame.image.load(obj.back_image_string).convert_alpha()
        except:
            # Fallback to naming convention if string is missing
            obj.set_image(obj.name.lower())

def draw_big_game_repro(screen, game, res, small_f, big_f):
    screen.fill((50, 100, 50)) 
    if not game: return

    # --- CONSTANTS FROM BIG_GAME.PY ---
    card_g, card_w, card_h = 10, 125, 175
    y_positions = [res[1]-(card_g+card_h), card_g]
    commander_positions = [(res[0]-2*(card_g+card_w), res[1]-2*(card_g+card_h)), (card_w, 2*(card_g+card_h)-card_h)]
    deck_positions = [(card_w, res[1]-2*(card_g+card_h)), (res[0]-2*(card_g+card_w), 2*(card_g+card_h)-card_h)]
    mana_positions = [(card_w/2, res[1]-1.5*card_h), (res[0]-(card_g+card_w/2), 1.5*card_h)]

    base_card = Card(w=card_w, h=card_h, hidden=True)

    for p_id, player in enumerate(game.players):
        # 1. COMMANDER & HP OVERLAY
        hydrate(player.commander, big_f, small_f)
        player.commander.x, player.commander.y = commander_positions[p_id]
        player.commander.set_w(card_w).set_h(card_h)
        player.commander.draw(screen)
        
        # DRAW HP TEXT (Same logic as big_game.py)
        hp_y = player.commander.y - 30 if player.commander.y > res[1]/2 else player.commander.y + card_h + 10
        Text(player.commander.x + card_w/2, hp_y, 0, 0, 
             f"HP: {player.commander.hp}", big_f, (255, 255, 255), None, False).draw(screen)

        # 2. HAND CARDS (CENTERED)
        hand = player.hand
        pgap = card_g
        while len(hand)*(pgap+card_w) > res[0]: pgap -= 5
        start_x = (res[0]-((card_w+pgap)*len(hand)))/2
        
        for i, card in enumerate(hand):
            hydrate(card, big_f, small_f)
            card.desired_x = start_x + ((card_w+pgap)*i) + (pgap/2)
            card.desired_y = y_positions[p_id]
            
            # Smooth movement
            for attr in ['x', 'y']:
                dist = getattr(card, f'desired_{attr}') - getattr(card, attr)
                if dist**2 < 50: setattr(card, attr, getattr(card, f'desired_{attr}'))
                else: setattr(card, attr, getattr(card, attr) + dist/5)
            card.draw(screen)

        # 3. ACTIVE CARDS (CENTERED)
        active = player.active
        agap = card_g
        while len(active)*(agap+card_w) > res[0]: agap -= 5
        active_start_x = (res[0]-((card_w+agap)*len(active)))/2
            
        for i, card in enumerate(active):
            hydrate(card, big_f, small_f)
            card.desired_x = active_start_x + ((card_w+agap)*i) + (agap/2)
            # Vertical offset logic
            card.desired_y = y_positions[p_id] - (card_h + card_g) if y_positions[p_id] > res[1]/2 else y_positions[p_id] + (card_h + card_g)

            for attr in ['x', 'y']:
                dist = getattr(card, f'desired_{attr}') - getattr(card, attr)
                if dist**2 < 50: setattr(card, attr, getattr(card, f'desired_{attr}'))
                else: setattr(card, attr, getattr(card, attr) + dist/5)
            card.draw(screen)

        # 4. DECK & MANA
        if len(player.deck) > 0:
            base_card.x, base_card.y = deck_positions[p_id]
            base_card.draw(screen)
        
        Text(mana_positions[p_id][0], mana_positions[p_id][1], 0, 0, 
             str(player.mana), big_f, (255, 255, 255), None, False).draw(screen)

    pygame.display.update()

def main():
    pygame.init()
    info = pygame.display.Info()
    res = (info.current_w, info.current_h)
    screen = pygame.display.set_mode(res, pygame.RESIZABLE)
    
    small_f = pygame.font.SysFont("Arial", 18)
    big_f = pygame.font.SysFont("Arial", 28, bold=True) # Slightly smaller font for HP
    
    n = Network()
    clock = pygame.time.Clock()

    while True:
        clock.tick(60)
        game_state = n.send({"type": "get"})
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
            if event.type == pygame.MOUSEBUTTONDOWN and game_state:
                if game_state.turn_player == n.p_id:
                    pos = pygame.mouse.get_pos()
                    # Only allow clicking on local hand
                    for i, card in enumerate(game_state.players[n.p_id].hand):
                        if pygame.Rect(card.x, card.y, 125, 175).collidepoint(pos):
                            n.send({"type": "play", "index": i})
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                n.send({"type": "end_turn"})

        draw_big_game_repro(screen, game_state, res, small_f, big_f)

if __name__ == "__main__":
    main()