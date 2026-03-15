import json
import os
import card_classes
import commander_classes
from random import choice

DATA_FILE = "player_data.json"

def get_deck():
    data = load_deck_data()
    deck = []

    commander_name = data.get("commander")
    if commander_name:
        try:
            comm_class = getattr(commander_classes, commander_name)
            commander_obj = comm_class().setup()
            deck.append(commander_obj)
        except AttributeError:
            print(f"Error: Commander class '{commander_name}' not found.")
    
    card_names = data.get("deck", [])
    for name in card_names:
        try:
            card_class = getattr(card_classes, name)
            card_obj = card_class().setup()
            deck.append(card_obj)
        except AttributeError:
            print(f"Error: Card class '{name}' not found.")

    return deck

def generate_player_deck(max_deck_size):
    data = load_deck_data()
    available_commanders = data.get("available_commanders", [])
    available_cards = data.get("available_cards", [])

    if not available_commanders or len(available_cards) < 1:
        return generate_deck(max_deck_size)

    comm_pool = [getattr(commander_classes, name)
                 for name in available_commanders
                 if hasattr(commander_classes, name)]
    card_pool = [getattr(card_classes, name)
                 for name in available_cards
                 if hasattr(card_classes, name)]

    deck = [choice(comm_pool)()]
    for _ in range(max_deck_size):
        deck.append(choice(card_pool)())
    for card in deck:
        card.setup()
    return deck


def get_default_data():
    return {
        "available_commanders": ["Biden", "Miku"],
        "available_cards": ["Amogus", "IceCube", "Pump", "Thorn", "Medic", "Bin"],
        "commander": "Biden",
        "deck": [ "Amogus" ] * 15 + [ "IceCube" ] * 10 + [ "Pump" ] * 5 + [ "Thorn" ] * 8 + [ "Bin" ] * 2,
        "campaign_stage": 0,
        "all_cards": [
            "Amogus",
            "Pump",
            "Hong",
            "IceCube",
            "Thorn",
            "Medic",
            "Sponge",
            "Bin",
            "Retriever",
            "Musketeer",
            "Net",
            "BagOfGold",
            "Snowball",
            "Kamikaze",
            "B52",
        ],
        "all_commanders": [
            "Biden",
            "Miku",
            "Alchemist",
            "Jesus",
            "GLaDOS",
            "Sonic",
            "Shadow",
        ]
    }

def load_deck_data():
    if not os.path.exists(DATA_FILE):
        data = get_default_data()
        save_deck_data(data)
        return data
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_deck_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generate_deck(max_deck_size):
    commanders = [
        commander_classes.Biden,
        commander_classes.Miku,
        commander_classes.Alchemist,
        commander_classes.Jesus,
        commander_classes.GLaDOS,
        commander_classes.Sonic,
        commander_classes.Shadow,
    ]

    economy_cards = [
        card_classes.Pump,
        card_classes.BagOfGold
    ]   

    taunt_cards = [
        card_classes.Thorn,
        card_classes.IceCube,
    ]

    dps_cards = [
        card_classes.Amogus,
        card_classes.Hong,
        card_classes.Kamikaze,
        card_classes.Musketeer,
        card_classes.Snowball,
        card_classes.Sponge,
    ]

    other_cards = [
        card_classes.Medic,
        card_classes.Net,
        card_classes.Bin,
        card_classes.Retriever,
    ]

    cards_left = max_deck_size
    deck = []
    random_comm_class = choice(commanders) 
    commander_obj = random_comm_class()
    deck.append(commander_obj)

    for i in range(int(max_deck_size/4)):
        random_card_class = choice(economy_cards)
        card_obj = random_card_class()
        deck.append(card_obj)
        cards_left -= 1

    for i in range(int(max_deck_size/4)):
        random_card_class = choice(taunt_cards)
        card_obj = random_card_class()
        deck.append(card_obj)
        cards_left -= 1

    for i in range(int(max_deck_size/3)):
        random_card_class = choice(dps_cards)
        card_obj = random_card_class()
        deck.append(card_obj)
        cards_left -= 1

    while cards_left > 0:
        random_card_class = choice(other_cards)
        card_obj = random_card_class()
        deck.append(card_obj)
        cards_left -= 1

    for card in deck:
        card.setup()

    return deck