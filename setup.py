from classes import Card

def setup_cards(res):
    cards = []
    for suit in ["diamonds", "hearts", "clubs", "spades"]:
        for value in ["ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "king", "queen", "jack"]:
            cards.append(Card(f"{value}_of_{suit}", res[0], res[1]/2))
    return cards

def setup_game(chips=None, quota=None, game_state=None, stats=None):
    if chips == None: chips = 100
    if quota == None: quota = 200
    if game_state == None: game_state = 0
    if stats == None: stats = [[0, 100, 0]]
    print(chips, quota, game_state, stats)
    return chips, quota, game_state, stats