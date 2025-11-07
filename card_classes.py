import pygame
from random import randint
from classes import Text

class Game():
    def __init__(self, players):
        self.turn = 0
        self.turn_player = 0
        self.num_players = players
        self.players = []
    
    def next_turn(self):
        self.turn += 1
        self.turn_player = self.turn%self.num_players
    
    def add_player(self, player):
        self.players.append(player)

class Player():
    def __init__(self, name=None, hp=1, mana=0, max_active=1, main_character=False, ai=False, deck=None, deck_position=(0, 0), mana_position=(0, 0), y=100):
        self.name = name
        self.hp = hp
        self.mana = mana
        self.max_active = max_active
        self.ai = ai
        self.hand = []
        self.active = []
        self.deck = deck
        self.deck_position = deck_position
        self.mana_position = mana_position
        self.y = y
        self.main_character = main_character

    def add_card(self, card):
        self.hand.append(card)
    
    def add_active(self, card):
        self.active.append(card)
    
    def remove_card(self, card):
        self.hand.remove(card)

    def set_mana(self, mana):
        self.mana = mana

    def draw(self, n=1, cost=1):
        self.mana -= cost
        for i in range(n):
            if len(self.deck) > 0:
                random = randint(0, len(self.deck) - 1)
                self.add_card(self.deck[random].set_coords(self.deck_position))
                self.deck.pop(random)

class Card():
    def __init__(self, owner=None, x=0, y=0, w=0, h=0, hidden=False):
        self.name = "placeholder"
        self.owner = owner
        self.hp = 1
        self.atk = 1
        self.cost = 1
        self.valid = False
        self.x = x
        self.y = y
        self.desired_x = None
        self.desired_y = None
        self.w = w
        self.h = h
        self.hidden = hidden
        self.text_factor = 3
        self.color_font = (255, 255, 255) 
        self.hp_color_font = (150, 255, 150)
        self.atk_color_font = (255, 150, 150)  
        self.font = pygame.font.SysFont('Arial',int(self.w/self.text_factor))
        self.image = pygame.image.load(f"cards/card_background.png").convert_alpha()
        self.back_image = pygame.image.load(f"cards/card_background_back.png").convert_alpha()

    def draw(self, screen):
        self.font = pygame.font.SysFont('Arial',int(self.w/self.text_factor))
        
        if self.hidden == False:       
            screen.blit(pygame.transform.scale(self.image, (self.w, self.h)), ((self.x, self.y)))
            screen.blit(self.font.render(self.name, True, self.color_font), ((self.x+(self.w-self.font.size(self.name)[0])/2, self.y)))
            hp_size = self.font.size(str(self.hp))
            screen.blit(self.font.render(str(self.hp), True, self.hp_color_font), ((self.x+5, self.y+self.h-hp_size[1])))
            atk_size = self.font.size(str(self.atk))
            screen.blit(self.font.render(str(self.atk), True, self.atk_color_font), ((self.x+(self.w-atk_size[0]), self.y+self.h-hp_size[1])))
        else:
            screen.blit(pygame.transform.scale(self.back_image, (self.w, self.h)), ((self.x, self.y)))

    def play(self):
        self.hidden = False
        self.owner.remove_card(self)
        self.owner.add_active(self)
        self.on_play()

    def remove_card(self):
        self.owner.remove_card(self)

    def set_owner(self, owner):
        self.owner = owner

    def set_valid(self):
        pass

    def touching(self, mouse):
        return self.x <= mouse[0] <= self.x+(self.w) and self.y <= mouse[1] <= self.y+(self.h)

    def on_play(self):
        pass

    def on_action(self):
        pass

    def on_die(self):
        pass

    def set_y(self, y):
        self.y = y
        return self
    
    def set_x(self, x):
        self.x = x
        return self
    
    def set_coords(self, coords):
        self.x, self.y = coords
        return self
    
    def set_desired_y(self, y):
        self.desired_y = y
        return self

    def set_desired_x(self, x):
        self.desired_x = x
        return self
    
    def set_w(self, w):
        self.w = w
        return self
    
    def set_h(self, h):
        self.h = h
        return self

    def set_hidden(self, hidden):
        self.hidden = hidden
        return self

class Amogus(Card):
    def setup(self):
        self.name = "amogus"
        self.hp = 2
        self.atk = 1
        self.cost = 1

    def on_play(self):
        pass

    def on_action(self):
        pass

    def on_die(self):
        pass

class Biden(Card):
    def setup(self):
        self.name = "biden"
        self.hp = 1
        self.atk = 2
        self.cost = 1

    def on_play(self):
        pass

    def on_action(self):
        pass

    def on_die(self):
        pass

    