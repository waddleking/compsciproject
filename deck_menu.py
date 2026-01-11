import pygame
import card_classes
import commander_classes
from classes import Button, Text
from deck_manager import load_deck_data, save_deck_data

def run_deck_menu(screen, res, settings, max_deck_size):
    # grab all the colors and fonts from settings
    _, _, color_light, color_dark, _, _, small_font, big_font, color_font, color_invalid = settings
    
    # get the saved player data
    data = load_deck_data()

    # setting up sizes for cards and the grid layout
    card_w, card_h = 125, 175
    card_g = 10
    gallery_columns = (res[0] - (2 * (card_w + card_g)) - (card_w + card_g))//(card_w + card_g)
    deck_columns = 2
    save_button = Button(res[0]//2, res[1]-60, 200, 50, "SAVE & EXIT", small_font, color_font, color_light, color_dark)

    # making the tab buttons to switch between cards and commanders
    basic_btn = Button(card_g//2+card_g+card_w, 6*card_g, 2*card_w, 30, "basic", small_font, color_font, color_light, color_dark, color_invalid)
    commander_btn = Button(card_g//2+3*(card_g+card_w), 6*card_g, 2*card_w, 30, "commanders", small_font, color_font, color_light, color_dark, color_invalid)
    buttons = [basic_btn,commander_btn]
    
    # start off looking at the basic cards
    current_section = "basic"

    # turn the card names from the save file into actual objects
    current_deck = []
    for name in data["deck"]:
        try:
            card_class = getattr(card_classes, name)
            card_obj = card_class()
            card_obj.setup() 
            current_deck.append(card_obj)
        except AttributeError:
            print(f"card class {name} not found.")

    # do the same thing for the commander
    card_class = getattr(commander_classes, data["commander"])
    card_obj = card_class()
    card_obj.setup() 
    current_commander = card_obj

    # load up every card available
    card_collection = []
    for name in data["available_cards"]:
        try:
            card_class = getattr(card_classes, name)
            card_obj = card_class()
            card_obj.setup() 
            card_collection.append(card_obj)
        except AttributeError:
            print(f"card class {name} not found.")
    
    # load up all the commanders unlocked too
    commander_collection = []
    for name in data["available_commanders"]:
        try:
            card_class = getattr(commander_classes, name)
            card_obj = card_class()
            card_obj.setup() 
            commander_collection.append(card_obj)
        except AttributeError:
            print(f"card class {name} not found.")

    while True:
        mouse = pygame.mouse.get_pos()
        screen.fill((30, 30, 30))
        
        # title at the top
        Text(res[0]//2, 30, 0, 0, "card collection", small_font, color_font, color_light, False).draw(screen)

        # logic for switching tabs when you click 'basic' or 'commanders'
        if current_section == "basic":
            basic_btn.draw(screen, True)
            commander_btn.draw(screen)
            if pygame.mouse.get_pressed()[0] and commander_btn.touching():
                current_section = "commander"
        if current_section == "commander":
            commander_btn.draw(screen, True)
            basic_btn.draw(screen)
            if pygame.mouse.get_pressed()[0] and basic_btn.touching():
                current_section = "basic"

        if current_section == "basic":
            # show the grid of cards you can add to your deck
            for i, card in enumerate(card_collection):
                # figure out where each card goes in the grid
                row = i // gallery_columns
                col = i % gallery_columns
                x = card_g + col * (card_w + card_g)
                y = 100 + row * (card_h + 80)

                # draw the card art
                scaled_img = pygame.transform.scale(card.image, (card_w, card_h))
                screen.blit(scaled_img, (x, y))
                
                # put a button under the card to add it
                btn = Button(x + card_w//2, y + card_h + card_g, card_w, 30, card.name, small_font, color_font, color_light, color_dark)
                btn.draw(screen)
                
                # if you click and have space, add it to the deck
                if len(current_deck) < max_deck_size and pygame.mouse.get_pressed()[0] and btn.touching():
                    current_deck.append(card)
                    pygame.time.delay(150)

        if current_section == "commander":
            # show the grid of commanders to pick from
            for i, card in enumerate(commander_collection):
                row = i // gallery_columns
                col = i % gallery_columns
                x = card_g + col * (card_w + card_g)
                y = 100 + row * (card_h + 80)

                scaled_img = pygame.transform.scale(card.image, (card_w, card_h))
                screen.blit(scaled_img, (x, y))
                
                btn = Button(x + card_w//2, y + card_h + card_g, card_w, 30, card.name, small_font, color_font, color_light, color_dark)
                btn.draw(screen)
                
                # clicking a commander button sets them as your active leader
                if pygame.mouse.get_pressed()[0] and btn.touching():
                    current_commander = card
                    pygame.time.delay(150)

        # show the deck size count on the right
        x = res[0] - 1.5*(card_w + card_g)
        y = 100

        deck_text = f"{len(current_deck)}/{max_deck_size}"
        Text(x + card_w//2, 30, 0, 0, deck_text, small_font, (150, 255, 150), color_light, False).draw(screen)

        # draw your currently selected commander on the side
        scaled_img = pygame.transform.scale(current_commander.image, (card_w, card_h))
        screen.blit(scaled_img, (x, y))
        Text(x + card_w//2, y + card_g + card_h, card_w, 30, current_commander.name, small_font, color_font, color_dark, True).draw(screen)
        
        # grouping identical cards so the list doesn't get huge and also annoying problem when loading that each one is different
        deck_count = {}
        representative_cards = {} 

        for card in current_deck:
            name = card.__class__.__name__
            deck_count[name] = deck_count.get(name, 0) + 1
            representative_cards[name] = card
        
        # draw the cards that are currently in your deck
        for i, (card_name, count) in enumerate(deck_count.items()):
            card_obj = representative_cards[card_name]
            
            # math for the deck list grid on the right side
            row = i // deck_columns + 1
            col = i % deck_columns
            
            x = res[0] - (col * (card_w + card_g)) - (card_w + card_g)
            y = 100 + row * (card_h + 80)

            scaled_img = pygame.transform.scale(card_obj.image, (card_w, card_h))
            screen.blit(scaled_img, (x, y))
            
            # button shows how many of that card you have; click to remove one
            btn = Button(x + card_w//2, y + card_h + card_g, card_w, 30, f"{count}", small_font, color_font, color_light, color_dark)
            btn.draw(screen)
            
            if pygame.mouse.get_pressed()[0] and btn.touching():
                for c in current_deck:
                    if c.__class__.__name__ == card_name:
                        current_deck.remove(c)
                        break
                pygame.time.delay(150)

        save_button.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # when saving, convert objects back to strings for the json
                if save_button.touching():
                    data["commander"] = current_commander.__class__.__name__
                    data["deck"] = []
                    for card in current_deck:
                        data["deck"].append(card.__class__.__name__)
                    save_deck_data(data)
                    return "menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"

        pygame.display.update()