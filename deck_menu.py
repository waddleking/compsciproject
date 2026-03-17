import pygame
import card_classes
import commander_classes
from classes import Button, Text
from deck_manager import load_deck_data, save_deck_data, generate_deck, generate_player_deck

def run_deck_menu(screen, res, settings, max_deck_size):
    """
    Description:
    The deck builder UI. Shows two panels: the left panel is the player's
    unlocked card collection as a grid they can click to add cards; the right
    panel is their current deck displayed as grouped stacks with click-to-remove.
    Switches between basic cards and commanders via two tabs at the top.

    Cards in the collection panel are kept as full Card objects the whole time
    so draw() can render them with their real art and stats. They're only
    converted back to class name strings when the player saves.

    The "random" button generates a valid random deck from the unlocked collection.
    The "clear" button empties the current deck.
    Saving converts Card objects back to class name strings and writes to JSON.

    Parameters:
        screen (pygame.Surface): the main display surface
        res (tuple): (width, height) screen resolution
        settings (tuple): unpacked as (screen, res, color_light, color_dark,
            current_background, color_background, small_font, big_font,
            color_font, color_invalid)
        max_deck_size (int): maximum number of non-commander cards allowed

    Returns:
        str: "menu" when the player saves and exits or presses Escape
    """
    # new way to access settings just dropped
    _, _, color_light, color_dark, _, _, small_font, big_font, color_font, color_invalid = settings
    
    # get the saved player data
    data = load_deck_data()

    # sizes
    deck_column_y_offset = 0
    card_w, card_h = 125, 175
    card_g = 10
    gallery_columns = (res[0] - (2 * (card_w + card_g)))//(card_w + card_g)
    deck_columns = 2
    save_button = Button(res[0]//2, res[1]-60, 200, 50, "SAVE & EXIT", small_font, color_font, color_light, color_dark)

    #switch between cards and commanders
    basic_btn = Button(card_g//2+card_g+card_w, 6*card_g, 2*card_w, 30, "basic", small_font, color_font, color_light, color_dark, color_invalid)
    commander_btn = Button(card_g//2+3*(card_g+card_w), 6*card_g, 2*card_w, 30, "commanders", small_font, color_font, color_light, color_dark, color_invalid)
    default_btn = Button(card_g//2+card_g+card_w, res[1]-6*card_g, card_w, 30, "random", small_font, color_font, color_light, color_dark, color_invalid)
    clear_btn = Button(card_g//2+2*(card_g+card_w), res[1]-6*card_g, card_w, 30, "clear", small_font, color_font, color_light, color_dark, color_invalid)
    buttons = [basic_btn,commander_btn]
    
    current_section = "basic"

    # turn the card names from the save file into actual objects
    current_deck = []
    for name in data["deck"]:
        try:
            card_class = getattr(card_classes, name)
            card_obj = card_class().setup() 
            card_obj.w = card_w
            card_obj.h = card_h
            current_deck.append(card_obj)
        except AttributeError:
            print(f"card class {name} not found.")

    # do the same thing for the commander
    card_class = getattr(commander_classes, data["commander"])
    card_obj = card_class().setup()
    card_obj.w = card_w
    card_obj.h = card_h
    current_commander = card_obj

    # load up every card available
    card_collection = []
    for name in data["available_cards"]:
        try:
            card_class = getattr(card_classes, name)
            card_obj = card_class().setup()
            card_obj.w = card_w
            card_obj.h = card_h
            card_collection.append(card_obj)
        except AttributeError:
            print(f"card class {name} not found.")
    
    commander_collection = []
    for name in data["available_commanders"]:
        try:
            card_class = getattr(commander_classes, name)
            card_obj = card_class().setup()
            card_obj.w = card_w
            card_obj.h = card_h
            commander_collection.append(card_obj)
        except AttributeError:
            print(f"card class {name} not found.")

    while True:
        mouse = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.MOUSEWHEEL:
                deck_column_y_offset += event.y * 30

        screen.fill((30, 30, 30))
        
        # title at the top
        Text(res[0]//2, 30, 0, 0, "card collection", small_font, color_font, color_light, False).draw(screen)

        default_btn.draw(screen)
        clear_btn.draw(screen)
        if pygame.mouse.get_pressed()[0] and clear_btn.touching():
            current_deck = []
        if pygame.mouse.get_pressed()[0] and default_btn.touching():
            current_deck = generate_player_deck(max_deck_size)
            current_commander = current_deck[0]
            current_deck = current_deck[1:]
            # current_deck = [
            #     card_classes.Pump().setup(),
            #     card_classes.Pump().setup(),
            #     card_classes.Pump().setup(),
            #     card_classes.Pump().setup(),
            #     card_classes.Pump().setup(),
            #     card_classes.HongXiuQuan().setup(),
            #     card_classes.HongXiuQuan().setup(),
            #     card_classes.IceCube().setup(),
            #     card_classes.IceCube().setup(),
            #     card_classes.IceCube().setup(),
            #     card_classes.Thorn().setup(),
            #     card_classes.Thorn().setup(),
            #     card_classes.Thorn().setup(),
            #     card_classes.Bin().setup(),
            #     card_classes.Bin().setup(),
            #     card_classes.Bin().setup(),
            #     card_classes.Bin().setup(),
            #     card_classes.Bin().setup(),
            #     card_classes.Medic().setup(),
            #     card_classes.Sponge().setup(),
            # ]

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
                # scaled_img = pygame.transform.scale(card.image, (card_w, card_h))
                # screen.blit(scaled_img, (x, y))
                card.x, card.y = x, y
                card.draw(screen)
                
                # how to remove card
                btn = Button(x + card_w//2, y + card_h + card_g, card_w, 30, card.name, small_font, color_font, color_light, color_dark)
                btn.draw(screen)
                
                # add to deck
                if len(current_deck) < max_deck_size and pygame.mouse.get_pressed()[0] and btn.touching():
                    current_deck.append(card)
                    pygame.time.delay(150)

        if current_section == "commander":
            for i, card in enumerate(commander_collection):
                row = i // gallery_columns
                col = i % gallery_columns
                x = card_g + col * (card_w + card_g)
                y = 100 + row * (card_h + 80)

                # scaled_img = pygame.transform.scale(card.image, (card_w, card_h))
                # screen.blit(scaled_img, (x, y))
                card.x, card.y = x, y
                card.draw(screen)
                
                btn = Button(x + card_w//2, y + card_h + card_g, card_w, 30, card.name, small_font, color_font, color_light, color_dark)
                btn.draw(screen)
                
                # choose commander
                if pygame.mouse.get_pressed()[0] and btn.touching():
                    current_commander = card
                    pygame.time.delay(150)

        # deck size count
        x = res[0] - 1.5*(card_w + card_g)
        y = 100 + deck_column_y_offset

        current_deck.sort(key=lambda x: x.name)
        deck_text = f"{len(current_deck)}/{max_deck_size}"
        Text(x + card_w//2, 30, 0, 0, deck_text, small_font, (150, 255, 150), color_light, False).draw(screen)

        # commander image
        scaled_img = pygame.transform.scale(current_commander.image, (card_w, card_h))
        screen.blit(scaled_img, (x, y))

        Text(x + card_w//2, y + card_g + card_h, card_w, 30, current_commander.name, small_font, color_font, color_dark, True).draw(screen)
        
        # yeah so basically i had to make them be grouped together andf this was the best i got
        deck_count = {}
        representative_cards = {} 

        for card in current_deck:
            name = card.__class__.__name__
            deck_count[name] = deck_count.get(name, 0) + 1
            representative_cards[name] = card
        
        # current deck
        for i, (card_name, count) in enumerate(deck_count.items()):
            card_obj = representative_cards[card_name]
            
            row = i // deck_columns + 1
            col = i % deck_columns
            
            x = res[0] - (col * (card_w + card_g)) - (card_w + card_g)
            y = 100 + row * (card_h + 80) + deck_column_y_offset

            scaled_img = pygame.transform.scale(card_obj.image, (card_w, card_h))
            screen.blit(scaled_img, (x, y))
            # card_obj.x, card_obj.y = x, y
            # card_obj.draw(screen)
            
            # click to remove
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