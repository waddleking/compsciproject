import pygame
from random import randint
from classes import Text, Button, Particle

class Game():
    def __init__(self, players, mana):
        self.turn = 0
        self.turn_player = 0
        self.num_players = players
        self.players = []
        self.turn_mana = mana
        self.pending_spell_notifications = []  # filled by Card.play(), drained each frame by big_game
    
    def next_turn(self):
        particles = []
        self.turn += 1
        self.turn_player = self.turn%self.num_players

        if self.players[self.turn_player].dead == False:
            self.players[self.turn_player].mana = min(self.players[self.turn_player].mana+self.turn_mana, self.turn_mana*2)

            particles.extend(self.players[self.turn_player].commander.on_turn_start())
            for card in self.players[self.turn_player].active:
                particles.extend(card.on_turn_start())
                if self.turn >= self.num_players:
                    card.reset_actions()
            for card in self.players[self.turn_player].hand:
                if self.turn >= self.num_players:
                    card.reset_actions()

            self.players[self.turn_player].draw()

        return particles

        # for card in self.players[self.turn_player].hand:
        #     card.on_turn_start()
        #     card.reset_actions()
    
    def add_player(self, player):
        self.players.append(player)

class Player():
    def __init__(self, game=None, name=None, mana=0, max_active=1, max_hand=7, main_character=False, ai=False, commander=None, commander_position=None, deck=None, deck_position=(0, 0), mana_position=(0, 0), y=100):
        self.game = game
        self.name = name
        self.mana = mana
        self.max_active = max_active
        self.max_hand = max_hand
        self.ai = ai
        self.commander = commander
        self.commander_position = commander_position
        self.hand = []
        self.active = []
        self.deck = deck
        self.deck_position = deck_position
        self.mana_position = mana_position
        self.y = y
        self.main_character = main_character
        self.dead = False
        self.card_w = 1
        self.card_h = 1

    def set_main_character(self, main_character):
        self.main_character = main_character

    def add_card(self, card):
        self.hand.append(card)
    
    def add_active(self, card):
        self.active.append(card)
    
    def remove_card(self, card):
        self.hand.remove(card)

    def remove_active(self, card):
        try:
            self.active.remove(card)
        except Exception as e:
            print(e)

    def set_mana(self, mana):
        self.mana = mana

    def set_dead(self, dead):
        self.dead = dead

    def draw(self, n=1, cost=0):
        self.mana -= cost
        for i in range(n):
            if len(self.deck) > 0 and len(self.hand) < self.max_hand:
                random = randint(0, len(self.deck) - 1)
                self.add_card(self.deck[random].set_coords(self.deck_position))
                self.hand[-1].setup()
                self.hand[-1].set_owner(self)
                self.hand[-1].set_w(self.card_w)
                self.hand[-1].set_h(self.card_h)
                if not self.main_character:
                    self.hand[-1].set_hidden(True)
                self.deck.pop(random)

class Card():
    def __init__(self, owner=None, x=0, y=0, w=0, h=0, hidden=False):
        self.name = "placeholder"
        self.desc = "description and the the"
        self.owner = owner
        self.dead = False
        self.hp = 1
        self.atk = 0
        self.cost = 1
        self.taunt = 0
        self.haste = False
        self.ignore_taunt = False
        self.spell = False
        self.retreat_cost = 1
        self.max_actions = 1
        self.actions = self.max_actions
        self.valid = False
        self.selection_type = "enemy"
        self.x = x
        self.y = y
        self.desired_x = None
        self.desired_y = None
        self.w = w
        self.h = h
        self.hidden = hidden
        self.selected = False
        self.scale_factor = 1
        self.text_factor = 5
        self.text_factor_desc = 8
        self.color_font = (255, 255, 255) 
        self.hp_color_font = (150, 255, 150)
        self.atk_color_font = (255, 150, 150)  
        self.color_light = (170, 170, 170) 
        self.color_dark = (100, 100, 100) 
        self.font = pygame.font.SysFont('Arial',int(self.w/self.text_factor))
        self.font_desc = pygame.font.SysFont('Arial',int(self.w/self.text_factor_desc))
        self.image_string = "card_images/card_back.png"
        self.back_image_string = "card_images/card_back.png"
        self.image = pygame.image.load(self.image_string).convert_alpha()
        self.back_image = pygame.image.load(self.back_image_string).convert_alpha()
        # self.action_button = Button(100, 100, self.w/2, self.h/2, "attack", self.font, self.color_font, self.color_light, self.color_dark)
        # self.retreat_button = Button(100, 100, self.w/2, self.h/2, "retreat", self.font, self.color_font, self.color_light, self.color_dark)
        # self.buttons = [self.action_button, self.retreat_button]

    def __getstate__(self):
    # pickle pickle pickle pickle pickle
        state = self.__dict__.copy()
        keys_to_remove = ['image', 'back_image', 'font', 'font_desc', 'small_font', 'big_font']
        for key in keys_to_remove:
            if key in state:
                state[key] = None
        return state

    def draw(self, screen):
        if not hasattr(self, 'image') or self.image is None:
            self.set_image(self.image_string.split('/')[-1].replace('.png', ''))

        #  font cache: only recreate SysFont when card width changes 
        font_size      = int(self.w / self.text_factor)
        font_desc_size = int(self.w / self.text_factor_desc)
        if (not hasattr(self, 'cached_font_size') or
                self.cached_font_size != font_size):
            self.font = pygame.font.SysFont('Arial', font_size)
            self.cached_font_size = font_size
        if (not hasattr(self, 'cached_font_desc_size') or
                self.cached_font_desc_size != font_desc_size):
            self.font_desc = pygame.font.SysFont('Arial', font_desc_size)
            self.cached_font_desc_size = font_desc_size

        #  image cache: always build so it exists regardless of hidden state 
        if (not hasattr(self, 'cached_scaled_w') or
                self.cached_scaled_w != self.w or
                self.cached_scaled_h != self.h):
            self.cached_image      = pygame.transform.scale(self.image,      (self.w, self.h))
            self.cached_back_image = pygame.transform.scale(self.back_image, (self.w, self.h))
            self.cached_scaled_w = self.w
            self.cached_scaled_h = self.h

        if self.hidden == False:
            image = self.cached_image
            if self.actions == 0:
                # copy so we don't tint the cached surface permanently
                image = image.copy()
                image.fill((255, 255, 255, 128), None, pygame.BLEND_RGBA_MULT)
            screen.blit(image, (self.x, self.y))

            screen.blit(self.font.render(self.name, True, self.color_font),
                        (self.x + (self.w - self.font.size(self.name)[0]) / 2, self.y))

            hp_size   = self.font.size(str(self.hp))
            atk_size  = self.font.size(str(self.atk))
            cost_size = self.font.size(str(self.cost))

            if not self.spell:
                screen.blit(self.font.render(str(self.atk),  True, self.atk_color_font),
                            (self.x + 5,                          self.y + self.h - atk_size[1]))
                screen.blit(self.font.render(str(self.hp),   True, self.hp_color_font),
                            (self.x + self.w - hp_size[0] - 5,   self.y + self.h - hp_size[1]))
            screen.blit(self.font.render(str(self.cost), True, self.color_font),
                        (self.x + (self.w - cost_size[0]) // 2,  self.y + self.h - cost_size[1]))

            # desc word-wrap
            words     = self.desc.split(' ')
            space     = self.font_desc.size(' ')[0]
            max_width = self.w + self.x
            pos       = self.x + 5, self.y + atk_size[1]
            x, y      = pos
            for word in words:
                word_surface = self.font_desc.render(word, 0, self.color_font)
                word_width, word_height = word_surface.get_size()
                if x + word_width >= max_width:
                    x  = pos[0]
                    y += word_height
                screen.blit(word_surface, (x, y))
                x += word_width + space
        else:
            screen.blit(self.cached_back_image, (self.x, self.y))

    def draw_buttons(self, screen):
        # if self.atk == 0:
        #     self.action_button = Button(self.x+self.w/4, self.y-self.w/2, self.w/2, self.w/2, str(self.atk), self.font, self.color_font, self.color_light, self.color_dark)
        # else:
        self.action_button = Button(self.x+self.w/4, self.y-self.w/2, self.w/2, self.w/2, str(self.atk), self.font, self.color_font, self.color_light, self.color_dark).draw(screen)
        self.retreat_button = Button(self.x+self.w/4 + self.w/2, self.y-self.w/2, self.w/2, self.w/2, str(self.retreat_cost), self.font, self.color_font, self.color_light, self.color_dark).draw(screen)
        # self.retreat_button = Button(100, 100, self.w/2, self.h/2, "retreat", self.font, self.color_font, self.color_light, self.color_dark)
        # for button_index in range(len(self.buttons)):
        #     self.buttons[button_index].w = self.w/2
        #     self.buttons[button_index].h = self.w/2
        #     self.buttons[button_index].x = self.x+self.w/4 + self.w/2 * button_index
        #     self.buttons[button_index].y = self.y-self.w/2
        #     self.buttons[button_index].draw(screen)
        #     print(self.buttons[button_index].x,self.buttons[button_index].y)

    def play(self, spend_mana=True):
        particles = []
        if spend_mana:
            self.owner.mana -= self.cost
        self.hidden = False
        self.remove_card()
        self.owner.add_active(self)
        if not self.haste:
            self.actions = 0
        if self.spell:
            player_index = self.owner.game.players.index(self.owner)
            self.owner.game.pending_spell_notifications.append({"name": self.name, "player": player_index})
        particles.extend(self.on_play())
        if not self.spell:
            particles.extend(self.owner.commander.on_card_played(self))
        else:
            particles.extend(self.owner.commander.on_spell_played(self))
        return particles

    def retreat(self, spend_mana=True):
        if spend_mana:
            self.owner.mana -= self.retreat_cost
        if not self.owner.main_character:
            self.hidden = True
        self.owner.remove_active(self)
        self.owner.add_card(self)
        self.actions -= 1
        self.on_retreat()

    def attacked(self, target):
        particles = []
        if self.dead == False:
            particles.extend(self.on_attacked(target))
        if self.hp <= 0:
            self.die()
            particles.extend(target.owner.commander.on_enemy_death(self))
        
        return particles
    
    def die(self):
        self.dead = True
        particles = []
        self.remove_active()
        if not self.spell:
            self.owner.commander.on_card_death(self)
        particles.extend(self.on_die())
        return particles

    def remove_card(self):
        self.owner.remove_card(self)

    def remove_active(self):
        self.owner.remove_active(self)

    def reset_actions(self):
        self.actions = self.max_actions

    def set_owner(self, owner):
        self.owner = owner

    def set_valid(self):
        pass

    def touching(self, mouse):
        return self.x <= mouse[0] <= self.x+(self.w) and self.y <= mouse[1] <= self.y+(self.h)

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
    
    def set_image(self, front=None, back=None):
        if front != None:
            self.image_string = f"card_images/{front}.png"
        if back != None:
            self.back_image_string = f"card_images/{back}.png"
        self.image = pygame.image.load(self.image_string).convert_alpha()
        self.back_image = pygame.image.load(self.back_image_string).convert_alpha()
    
    #actual gameplay
    def on_turn_start(self):
        return []

    def on_play(self):
        return []

    def on_action(self, target):
        particles = [Particle(target.x+target.w/2, target.y+target.h/2, self.atk*-1, self.font, self.hp_color_font, self.atk_color_font)]
        target.hp -= self.atk
        self.actions -= 1
        particles.extend(target.attacked(self))
        return particles
    
    def on_attacked(self, target):
        return []

    def on_die(self):
        return []

    def on_retreat(self):
        pass

    #ai stuff
    def ai_value(self):
        return 1


class Commander():
    def __init__(self, owner=None, x=0, y=0, w=0, h=0, hidden=False):
        self.name = "placeholder"
        self.desc = "description and the the"
        self.owner = owner
        self.hp = 20
        self.taunt = 0
        self.valid = False
        self.x = x
        self.y = y
        self.desired_x = None
        self.desired_y = None
        self.w = w
        self.h = h
        self.selected = False
        self.scale_factor = 1
        self.text_factor = 5
        self.text_factor_desc = 8
        self.color_font = (255, 255, 255) 
        self.hp_color_font = (150, 255, 150)
        self.atk_color_font = (255, 150, 150)  
        self.color_light = (170, 170, 170) 
        self.color_dark = (100, 100, 100) 
        self.font = pygame.font.SysFont('Arial',int(self.w/self.text_factor))
        self.font_desc = pygame.font.SysFont('Arial',int(self.w/self.text_factor_desc))
        self.image_string = "card_images/card_back.png"
        self.back_image_string = "card_images/card_back.png"
        self.image = pygame.image.load(self.image_string).convert_alpha()
        self.back_image = pygame.image.load(self.back_image_string).convert_alpha()
        # self.action_button = Button(100, 100, self.w/2, self.h/2, "attack", self.font, self.color_font, self.color_light, self.color_dark)
        # self.retreat_button = Button(100, 100, self.w/2, self.h/2, "retreat", self.font, self.color_font, self.color_light, self.color_dark)
        # self.buttons = [self.action_button, self.retreat_button]

    def __getstate__(self):
    # This tells Pickle what to save. We remove Surfaces and Fonts.
        state = self.__dict__.copy()
        keys_to_remove = ['image', 'back_image', 'font', 'font_desc', 'small_font', 'big_font']
        for key in keys_to_remove:
            if key in state:
                state[key] = None
        return state

    def draw(self, screen):
        self.font = pygame.font.SysFont('Arial',int(self.w/self.text_factor))
        self.font_desc = pygame.font.SysFont('Arial',int(self.w/self.text_factor_desc))
        
        image = pygame.transform.scale(self.image, (self.w, self.h))    
        if self.hp == 0:
            image.fill((255, 255, 255, 128), None, pygame.BLEND_RGBA_MULT)
        screen.blit(image, ((self.x, self.y)))
        screen.blit(self.font.render(self.name, True, self.color_font), ((self.x+(self.w-self.font.size(self.name)[0])/2, self.y)))
        
        hp_size = self.font.size(str(self.hp))

        #desc
        words = self.desc.split(' ')  # 2D array where each row is a list of words.
        space = self.font_desc.size(' ')[0]  # The width of a space.
        max_width = self.w+self.x
        pos = self.x+5, self.y+hp_size[1]
        x, y = pos
        for word in words:
            word_surface = self.font_desc.render(word, 0, self.color_font)
            word_width, word_height = word_surface.get_size()
            if x + word_width >= max_width:
                x = pos[0]  # Reset the x.
                y += word_height  # Start on new row.
            screen.blit(word_surface, (x, y))
            x += word_width + space
        x = pos[0]  # Reset the x.
        y += word_height  # Start on new row.

    def set_owner(self, owner):
        self.owner = owner

    def touching(self, mouse):
        return self.x <= mouse[0] <= self.x+(self.w) and self.y <= mouse[1] <= self.y+(self.h)

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
    
    def set_image(self, front=None, back=None):
        if front != None:
            self.image_string = f"card_images/{front}.png"
        if back != None:
            self.back_image_string = f"card_images/{back}.png"
        self.image = pygame.image.load(self.image_string).convert_alpha()
        self.back_image = pygame.image.load(self.back_image_string).convert_alpha()

    def attacked(self, target):
        particles = []
        if self.hp <= 0:
            self.die()
        particles.extend(self.on_attacked(target))
        return particles
    
    def die(self):
        particles = []
        return particles

    def ai_value(self):
        # LETHAL CHEC
        # if the commander is at 10 HP or less, it becomes the highest priority target.
        if self.hp <= 10:
            return 2000 - (self.hp * 50)

        value = 30 + (30 - self.hp) * 2
        
        # count high-threat units
        active_threats = len([c for c in self.owner.active if c.atk >= 3 or c.name in ["Pump", "Medic"]])
        
        if active_threats > 0:
            value -= 40

        return max(5, value) # always worth at least a little bit
    
    #actual gameplay
    def on_turn_start(self):
        return []
    
    def on_attacked(self, target):
        particles = []
        if self.hp <= 0:
            self.on_die()
        return particles
    
    def on_card_played(self, card):
        return []
    
    def on_spell_played(self, card):
        return []
    
    def on_card_death(self, card):
        return []
    
    def on_enemy_death(self, enemy_card):
        return []

    def on_die(self):
        pass

    def on_retreat(self):
        pass