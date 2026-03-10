import socket
import pickle
import pygame
from _thread import start_new_thread
from main_classes import Game, Player
from deck_manager import get_deck

pygame.init()
pygame.display.set_mode((100, 100)) 

SERVER = "0.0.0.0"
PORT = 5555
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((SERVER, PORT))
s.listen(2)

game = Game(players=2, mana=1)

def setup_network_player(p_id):
    full_deck = get_deck() 
    p = Player(
        game=game, 
        max_active=5, 
        commander=full_deck[0], 
        deck=full_deck[1:],
    )
    p.commander.setup()
    p.draw(4)
    return p

game.add_player(setup_network_player(0))
game.add_player(setup_network_player(1))

def get_safe_game(game_obj):
    """Deep-cleans surfaces and fonts for pickling"""
    for p in game_obj.players:
        p.commander.image = None
        p.commander.font = p.commander.font_desc = None
        for lst in [p.hand, p.active, p.deck]:
            for card in lst:
                card.image = None
                card.font = card.font_desc = None
    return game_obj

def threaded_client(conn, p_id):
    conn.send(pickle.dumps(p_id))
    while True:
        try:
            data = conn.recv(1024 * 512)
            if not data: break
            req = pickle.loads(data)
            if req["type"] == "play" and game.turn_player == p_id:
                game.players[p_id].hand[req["index"]].play()
            elif req["type"] == "end_turn" and game.turn_player == p_id:
                game.next_turn()
            conn.sendall(pickle.dumps(get_safe_game(game)))
        except: break
    conn.close()

print("Server is waiting for 2 players...")
curr_p = 0
while curr_p < 2:
    conn, addr = s.accept()
    start_new_thread(threaded_client, (conn, curr_p))
    curr_p += 1