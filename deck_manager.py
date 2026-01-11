import json
import os
import card_classes
import commander_classes

DATA_FILE = "player_data.json"

def get_deck():
    data = load_deck_data()
    deck = []

    commander_name = data.get("commander")
    if commander_name:
        try:
            comm_class = getattr(commander_classes, commander_name)
            commander_obj = comm_class()
            commander_obj.setup() 
            deck.append(commander_obj)
        except AttributeError:
            print(f"Error: Commander class '{commander_name}' not found.")
    
    card_names = data.get("deck", [])
    for name in card_names:
        try:
            card_class = getattr(card_classes, name)
            card_obj = card_class()
            card_obj.setup()
            deck.append(card_obj)
        except AttributeError:
            print(f"Error: Card class '{name}' not found.")

    return deck

def get_default_data():
    return {
        "available_commanders": ["HatsuneMiku", "Biden"],
        "available_cards": ["Amogus", "Pump", "HongXiuQuan", "IceCube"],
        "commander": "Biden",
        "deck": ["Amogus", "Amogus", "HongXiuQuan", "IceCube", "Pump"]
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