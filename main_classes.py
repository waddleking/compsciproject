import pygame
from random import randint
from classes import Text, Button, Particle

class Game():
    """
    Description:
    The central state container for a game session. Has the players list,
    tracks whose turn it is, and holds the mana-per-turn setting.
    Everything else reads from or writes to this object.

    Attributes:
        turn (int): total turns elapsed since game start
        turn_player (int): index into players of whoever is active right now
        num_players (int): how many players are in this game (always 2 for now but maybe that'll change later?????)
        players (list): Player objects, added via add_player()
        turn_mana (int): base mana each player gains per turn
        pending_spell_notifications (list): spell names queued by Card.play(),
            drained each frame by big_game to show the spell overlay banner
    """
    def __init__(self, players, mana):
        """
        Description:
        Sets up a fresh game with no players yet. Players are added separately
        via add_player() after construction.

        Parameters:
            players (int): number of players (always 2 in practice)
            mana (int): base mana each player gains at the start of their turn
        """
        self.turn = 0
        self.turn_player = 0
        self.num_players = players
        self.players = []
        self.turn_mana = mana
        self.pending_spell_notifications = []  # filled by Card.play(), drained each frame by big_game
    
    def next_turn(self):
        """
        Description:
        Advances the game by one turn. Increments the counter, works out whose
        turn it is, tops up their mana (capped at turn_mana * 2 so nobody hoards
        infinite mana), fires all on_turn_start on actions, resets actions on all cards,
        and draws one card for the active player.

        The self.turn >= self.num_players check means cards played on turn 0
        don't get their actions reset immediately so you don't get jumped immediately.

        Returns:
            particles (list): all particle effects from turn-start on actions
                (pump mana sparks, jesus heals, medic heals etc)
        """
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
        """
        Description:
        Appends a Player to the game's players list.
        Should be called before the game starts.

        Parameters:
            player (Player): the fully constructed Player object to add
        """
        self.players.append(player)

class Player():
    """
    Description:
    Represents one player in a game. Owns the hand, active zone, deck, mana,
    and commander, plus all position info needed to render them on screen.
    Also tracks whether this is the human player (main_character) which affects
    whether their hand cards are shown face-up or hidden.

    Attributes:
        game (Game): reference back to the parent Game object
        mana (int): current mana this player has to spend
        max_active (int): maximum cards in the active zone (usually 6)
        max_hand (int): maximum hand size before draws stop
        hand (list): cards currently in hand
        active (list): cards currently on the board
        deck (list): remaining cards to draw from
        commander (Commander): this player's commander object
        dead (bool): true when the commander's hp hits 0
        card_w (int): pixel width for cards drawn by this player
        card_h (int): pixel height for cards drawn by this player
        main_character (bool): true for the human player
    """
    def __init__(self, game=None, name=None, mana=0, max_active=1, max_hand=7, main_character=False, ai=False, commander=None, commander_position=None, deck=None, deck_position=(0, 0), mana_position=(0, 0), y=100):
        """
        Description:
        Constructs a player with everything needed to participate in a game.

        Parameters:
            game (Game): the game this player belongs to
            name (str): player name (mostly for debug prints)
            mana (int): starting mana, usually 0 then topped up on first turn
            max_active (int): board size cap
            max_hand (int): hand size cap
            main_character (bool): true for the human player
            ai (bool): legacy flag, not actively used by the ai logic
            commander (Commander): this player's commander object
            commander_position (tuple): (x, y) screen position for the commander
            deck (list): list of Card objects making up the player's deck
            deck_position (tuple): (x, y) where the face-down deck pile is drawn
            mana_position (tuple): (x, y) where the mana number is displayed
            y (int): vertical row for this player's hand and active zone
        """
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
        """
        Description:
        Marks this player as the human-controlled one. Human player cards are
        shown face-up; ai cards start hidden.

        Parameters:
            main_character (bool): true if this is the human player
        """
        self.main_character = main_character

    def add_card(self, card):
        """
        Description:
        Puts a card into this player's hand. Used by draw() and retreat().

        Parameters:
            card (Card): the card to add to hand
        """
        self.hand.append(card)
    
    def add_active(self, card):
        """
        Description:
        Puts a card onto the board (active zone). Called by Card.play().

        Parameters:
            card (Card): the card entering the active zone
        """
        self.active.append(card)
    
    def remove_card(self, card):
        """
        Description:
        Removes a card from hand. Called by Card.remove_card() during Card.play().

        Parameters:
            card (Card): the card to remove from hand
        """
        self.hand.remove(card)

    def remove_active(self, card):
        """
        Description:
        Removes a card from the active zone. Called during die() and retreat().
        Wrapped in try/except because both can fire in the same damage chain
        and a double-remove would crash without it.

        Parameters:
            card (Card): the card to remove from the board
        """
        try:
            self.active.remove(card)
        except Exception as e:
            print(e)

    def set_mana(self, mana):
        """
        Description:
        Sets mana to a specific value. Used at game start to give the
        first player their opening mana.

        Parameters:
            mana (int): the mana value to set directly
        """
        self.mana = mana

    def set_dead(self, dead):
        """
        Description:
        Sets whether this player is considered dead (commander hp <= 0).
        big_game checks this every frame to detect the win condition.

        Parameters:
            dead (bool): true if the player's commander is out of hp
        """
        self.dead = dead

    def draw(self, n=1, cost=0):
        """
        Description:
        Draws n cards from the deck into hand. Deducts cost from mana first
        (Retriever charges 1 mana per draw this way). Picks a random index
        from the deck each time meaning the deck is effectively shuffled at draw time
        rather than up front, which is equivalent. Skips the draw if the deck
        is empty or the hand is already full. Sets up each drawn card with the
        correct owner, size, and visibility.

        Parameters:
            n (int): number of cards to draw (default 1)
            cost (int): mana cost per draw, deducted before drawing begins
        """
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
    """
    Description:
    Base class for all 16 card types. Handles rendering, positioning, combat,
    and the event on action system. Individual cards in card_classes.py inherit from
    this and override setup() plus whichever on actions they need.

    The draw() method caches fonts and scaled images to avoid calling SysFont()
    and transform.scale() on every frame for every card as with 12+ cards at 60fps
    that was hundreds of redundant allocations per second.

    __getstate__ strips pygame Surfaces and Fonts before pickle so the object
    can be sent over the network without crashing.

    Attributes:
        name (str): displayed card name
        desc (str): ability description shown on the card
        hp (int): current hit points. card dies when this hits 0
        atk (int): damage dealt to targets when attacking
        cost (int): mana cost to play from hand
        retreat_cost (int): mana cost to return to hand from the board
        taunt (int): cards can only attack the highest taunt cards
        haste (bool): if true, card can act on the turn it is played
        ignore_taunt (bool): if true, bypasses enemy taunt (musketeer)
        spell (bool): if true, resolves instantly and leaves the board
        max_actions (int): actions per turn (usually 1)
        actions (int): remaining actions this turn
        selection_type (str): "enemy" to attack, "" for no-target actions,
            "hand" to target own hand cards (net)
    """
    def __init__(self, owner=None, x=0, y=0, w=0, h=0, hidden=False):
        """
        Description:
        Constructs a card with default placeholder stats and loads the
        card back image. Actual stats are set by each subclass's setup().

        Parameters:
            owner (Player): the player who owns this card (set later via set_owner)
            x (int): initial screen x position
            y (int): initial screen y position
            w (int): card width in pixels
            h (int): card height in pixels
            hidden (bool): if true, shows the card back instead of the front
        """
        self.name = "placeholder"
        self.desc = "description and the the"
        self.action_image = "card_images/axe.png"
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
        self.particle_font = pygame.font.SysFont('Arial',int(80))
        self.font_desc = pygame.font.SysFont('Arial',int(self.w/self.text_factor_desc))
        self.image_string = "card_images/card_back.png"
        self.back_image_string = "card_images/card_back.png"
        self.image = pygame.image.load(self.image_string).convert_alpha()
        self.back_image = pygame.image.load(self.back_image_string).convert_alpha()
        self.action_button = None
        self.retreat_button = None
        # self.action_button = Button(100, 100, self.w/2, self.h/2, "attack", self.font, self.color_font, self.color_light, self.color_dark)
        # self.retreat_button = Button(100, 100, self.w/2, self.h/2, "retreat", self.font, self.color_font, self.color_light, self.color_dark)
        # self.buttons = [self.action_button, self.retreat_button]

    def __getstate__(self):
        """
        Description:
        Custom pickle stuff. Strips pygame Surfaces and Fonts before the
        object is serialised for networking. Surfaces cannot be pickled at all. 
        The client restores them via hydrate() after receiving the state.

        Returns:
            state (dict): instance dict with all unpickleable assets set to None
        """
    # pickle pickle pickle pickle pickle
        state = self.__dict__.copy()
        keys_to_remove = ['image', 'back_image', 'font', 'font_desc', 'small_font', 'big_font']
        for key in keys_to_remove:
            if key in state:
                state[key] = None
        return state

    def draw(self, screen):
        """
        Description:
        Renders the card at its current (x, y) position. Uses a font cache and
        image cache to avoid SysFont() and transform.scale() every frame.
        If the card has no remaining actions, tints it with a semi-transparent
        white overlay (copies the cached surface first so the cache stays clean).
        For hidden cards (AI hand) draws the card back.
        Handles description word-wrap by splitting on spaces and reflowing onto
        new lines when the current line would overflow the card width.

        Parameters:
            screen (pygame.Surface): the pygame display surface to draw onto
        """
        if not hasattr(self, 'image') or self.image is None:
            self.set_image(self.image_string.split('/')[-1].replace('.png', ''))

        #  font cache
        font_size = int(self.w / self.text_factor)
        font_desc_size = int(self.w / self.text_factor_desc)
        if (not hasattr(self, 'cached_font_size') or self.cached_font_size != font_size):
            self.font = pygame.font.SysFont('Arial', font_size)
            self.cached_font_size = font_size
        if (not hasattr(self, 'cached_font_desc_size') or self.cached_font_desc_size != font_desc_size):
            self.font_desc = pygame.font.SysFont('Arial', font_desc_size)
            self.cached_font_desc_size = font_desc_size

        #  image cache
        if (not hasattr(self, 'cached_scaled_w') or self.cached_scaled_w != self.w or self.cached_scaled_h != self.h):
            self.cached_image = pygame.transform.scale(self.image, (self.w, self.h))
            self.cached_back_image = pygame.transform.scale(self.back_image, (self.w, self.h))
            self.cached_scaled_w = self.w
            self.cached_scaled_h = self.h

        if self.hidden == False:
            image = self.cached_image
            if self.actions == 0:
                # copy so it doesnt tint the cached surface permanently
                image = image.copy()
                image.fill((255, 255, 255, 128), None, pygame.BLEND_RGBA_MULT)
            screen.blit(image, (self.x, self.y))

            screen.blit(self.font.render(self.name, True, self.color_font), (self.x + (self.w - self.font.size(self.name)[0]) / 2, self.y))

            hp_size = self.font.size(str(self.hp))
            atk_size = self.font.size(str(self.atk))
            cost_size = self.font.size(str(self.cost))

            if not self.spell:
                screen.blit(self.font.render(str(self.atk),  True, self.atk_color_font), (self.x + 5, self.y + self.h - atk_size[1]))
                screen.blit(self.font.render(str(self.hp),   True, self.hp_color_font), (self.x + self.w - hp_size[0] - 5,   self.y + self.h - hp_size[1]))
            screen.blit(self.font.render(str(self.cost), True, self.color_font), (self.x + (self.w - cost_size[0]) // 2,  self.y + self.h - cost_size[1]))

            # desc word-wrap
            words = self.desc.split(' ')
            space = self.font_desc.size(' ')[0]
            max_width = self.w + self.x
            pos = self.x + 5, self.y + atk_size[1]
            x, y = pos
            for word in words:
                word_surface = self.font_desc.render(word, 0, self.color_font)
                word_width, word_height = word_surface.get_size()
                if x + word_width >= max_width:
                    x = pos[0]
                    y += word_height
                screen.blit(word_surface, (x, y))
                x += word_width + space
        else:
            screen.blit(self.cached_back_image, (self.x, self.y))

    def draw_buttons(self, screen):
        """
        Description:
        Draws the action and retreat buttons above the selected card.
        The action button shows the card's ATK value; the retreat button shows
        the retreat cost. big_game calls this when the player has selected
        an active card and needs to choose what to do with it.

        Parameters:
            screen (pygame.Surface): the pygame display surface to draw onto
        """
        # if self.atk == 0:
        #     self.action_button = Button(self.x+self.w/4, self.y-self.w/2, self.w/2, self.w/2, str(self.atk), self.font, self.color_font, self.color_light, self.color_dark)
        # else:
        if self.action_image is not None:
            if not hasattr(self, 'cached_action_image') or self.cached_scaled_w != self.w:
                action_img = pygame.image.load(self.action_image).convert_alpha()
                action_size = int(self.w / 2)
                self.cached_action_image = pygame.transform.scale(action_img, (action_size, action_size))
            self.action_button = Button(self.x+self.w/4, self.y-self.w/2, self.w/2, self.w/2, "", self.font, self.color_font, self.color_light, self.color_dark).draw(screen)
            screen.blit(self.cached_action_image, (self.x, self.y - self.w/2))
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
        """
        Description:
        Moves the card from hand to the active zone. Deducts mana (unless
        spend_mana=False, which is how Net plays a card for free). Sets actions
        to 0 if the card has no haste. For spell cards, queues a spell notification
        for the overlay banner and fires on_spell_played on the commander instead
        of on_card_played.

        Parameters:
            spend_mana (bool): if False, skip the mana deduction (used by Net)

        Returns:
            particles (list): particles from on_play() and commander on actions
        """
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
        """
        Description:
        Returns the card from the active zone back to hand. Costs retreat_cost
        mana. Hides the card again if this is the AI's side (so the player
        can't see the AI's retreated cards). Costs one action.

        Parameters:
            spend_mana (bool): if False, skip the mana deduction
        """
        if spend_mana:
            self.owner.mana -= self.retreat_cost
        if not self.owner.main_character:
            self.hidden = True
        self.owner.remove_active(self)
        self.owner.add_card(self)
        self.actions -= 1
        self.on_retreat()

    def attacked(self, target):
        """
        Description:
        Called when this card receives an incoming attack. Fires on_attacked()
        (e.g. Sponge gains ATK) then checks if hp dropped to 0 and calls die().
        Also fires on_enemy_death on the attacker's commander (e.g. Shadow gains mana).
        The dead check prevents on_attacked from firing twice if the card was
        already killed earlier in the same damage chain.

        Parameters:
            target (Card): the card or commander that attacked this card

        Returns:
            particles (list): particles from on_attacked and die on actions
        """
        particles = []
        if self.dead == False:
            particles.extend(self.on_attacked(target))
        if self.hp <= 0:
            self.die()
            particles.extend(target.owner.commander.on_enemy_death(self))
        
        return particles
    
    def die(self):
        """
        Description:
        Removes the card from the active zone and fires death on actions.
        Sets dead=True first to prevent double-triggering. Fires on_card_death
        on this player's commander (e.g. GLaDOS draws a card). Spells don't
        trigger on_card_death.

        Returns:
            particles (list): particles from on_die on action
        """
        self.dead = True
        particles = []
        self.remove_active()
        if not self.spell:
            self.owner.commander.on_card_death(self)
        particles.extend(self.on_die())
        return particles

    def remove_card(self):
        """
        Description:
        Delegates to the owner player's remove_card(). Convenience wrapper.
        """
        self.owner.remove_card(self)

    def remove_active(self):
        """
        Description:
        Delegates to the owner player's remove_active(). Convenience wrapper
        used by die() and retreat().
        """
        self.owner.remove_active(self)

    def reset_actions(self):
        """
        Description:
        Restores this card's actions to its max. Called at the start of the
        owning player's turn by Game.next_turn().
        """
        self.actions = self.max_actions

    def set_owner(self, owner):
        """
        Description:
        Sets the player who owns this card. Called when a card is drawn from
        the deck so it knows which player's board and mana to affect.

        Parameters:
            owner (Player): the player who now owns this card
        """
        self.owner = owner

    def set_valid(self):
        """Description: not currently in use."""
        pass

    def touching(self, mouse):
        """
        Description:
        Checks if the mouse cursor is over this card's bounding box.
        Used by big_game for click detection on hand and active cards.

        Parameters:
            mouse (tuple): (x, y) mouse position from pygame.mouse.get_pos()

        Returns:
            bool: true if the mouse is within the card's rectangular bounds
        """
        return self.x <= mouse[0] <= self.x+(self.w) and self.y <= mouse[1] <= self.y+(self.h)

    def set_y(self, y):
        """
        Description:
        Sets the card's y position and returns self for chaining.

        Parameters:
            y (int): the y coordinate to move to
        """
        self.y = y
        return self
    
    def set_x(self, x):
        """
        Description:
        Sets the card's x position and returns self for chaining.

        Parameters:
            x (int): the x coordinate to move to
        """
        self.x = x
        return self
    
    def set_coords(self, coords):
        """
        Description:
        Sets both x and y from a tuple. Used when drawing a card from the deck
        to spawn it at the deck pile position before it lerps into hand.

        Parameters:
            coords (tuple): (x, y) position to place the card
        """
        self.x, self.y = coords
        return self
    
    def set_desired_y(self, y):
        """
        Description:
        Sets the target y position for the lerp animation system.
        The card moves toward desired_y each frame in big_game.

        Parameters:
            y (int): the y coordinate to animate toward
        """
        self.desired_y = y
        return self

    def set_desired_x(self, x):
        """
        Description:
        Sets the target x position for the lerp animation system.
        The card moves toward desired_x each frame in big_game.

        Parameters:
            x (int): the x coordinate to animate toward
        """
        self.desired_x = x
        return self
    
    def set_w(self, w):
        """
        Description:
        Sets the card width in pixels. Invalidates the image cache so draw()
        rescales the image on the next frame.

        Parameters:
            w (int): card width in pixels
        """
        self.w = w
        return self
    
    def set_h(self, h):
        """
        Description:
        Sets the card height in pixels. Invalidates the image cache so draw()
        rescales the image on the next frame.

        Parameters:
            h (int): card height in pixels
        """
        self.h = h
        return self

    def set_hidden(self, hidden):
        """
        Description:
        Sets whether this card shows its back (hidden=True) or front (False).
        AI hand cards are hidden; human hand cards are shown face-up.

        Parameters:
            hidden (bool): true to show the card back
        """
        self.hidden = hidden
        return self
    
    def set_image(self, front=None, back=None):
        """
        Description:
        Loads card art from the card_images/ folder. Called by each subclass's
        setup() with the card's image name. The back image defaults to card_back.png
        unless explicitly overridden.

        Parameters:
            front (str): filename stem for the front face (e.g. "pump")
            back (str): filename stem for the back face, usually left as None
        """
        if front is not None:
            self.image_string = f"card_images/{front}.png"
        if back is not None:
            self.back_image_string = f"card_images/{back}.png"
        self.image = pygame.image.load(self.image_string).convert_alpha()
        self.back_image = pygame.image.load(self.back_image_string).convert_alpha()
    
    #actual gameplay
    def on_turn_start(self):
        """
        Description:
        on action called at the start of the owning player's turn. Base does nothing.
        Override in subclasses that have per-turn effects (Pump, Medic, Snowball).

        Returns:
            list: particles to display (empty by default)
        """
        return []

    def on_play(self):
        """
        Description:
        on action called immediately when this card is played. Base does nothing.
        Override in subclasses with play effects (Kamikaze, B52, FatMan, BagOfGold).

        Returns:
            list: particles to display (empty by default)
        """
        return []

    def on_action(self, target):
        """
        Description:
        Default attack action. Deals self.atk damage to the target, consumes
        one action, and calls target.attacked(self) to trigger any defensive
        on actions on the target (Thorn retaliation, Sponge ATK gain etc).

        Parameters:
            target (Card or Commander): the thing being attacked

        Returns:
            particles (list): damage particle at target position plus any
                particles from target.attacked()
        """
        particles = [Particle(target.x+target.w/2, target.y+target.h/2, self.atk*-1, self.particle_font, self.hp_color_font, self.atk_color_font)]
        target.hp -= self.atk
        self.actions -= 1
        particles.extend(target.attacked(self))
        return particles
    
    def on_attacked(self, target):
        """
        Description:
        on action called when this card is hit. Base does nothing.
        Override in subclasses with defensive effects (Sponge, Thorn).

        Parameters:
            target (Card): the card that attacked this one

        Returns:
            list: particles to display (empty by default)
        """
        return []

    def on_die(self):
        """
        Description:
        on action called when this card dies. Base does nothing.
        Override in subclasses with death effects if needed.

        Returns:
            list: particles to display (empty by default)
        """
        return []

    def on_retreat(self):
        """
        Description:
        on action called when this card retreats to hand. Base does nothing.
        Override in subclasses that need cleanup on retreat.
        """
        pass

    #ai stuff
    def ai_value(self):
        """
        Description:
        Base ai_value for a generic card. Returns 1. Every subclass in
        card_classes.py overrides this with a context-sensitive score based
        on the current board state. The AI uses this to decide which cards
        to play and which targets to attack.

        Returns:
            int: scoring value for AI decision-making (higher = more desirable)
        """
        return 1


class Commander():
    """
    Description:
    Base class for all 7 commander types. Commanders are persistent game pieces
    with HP that sit on the board throughout the game and when their HP hits 0
    the game ends. They have passive ability on actions that fire on game events.

    Like Card, Commander uses __getstate__ to strip pygame assets before pickle.
    Unlike Card, Commander.draw() doesn't use the image cache (commanders are
    drawn once per frame at a fixed size, not worth the complexity).

    Attributes:
        name (str): commander name shown on their card
        desc (str): ability description
        hp (int): current hit points
        taunt (int): always 0 for commanders (for now...)
        owner (Player): the player who owns this commander
    """
    def __init__(self, owner=None, x=0, y=0, w=0, h=0, hidden=False):
        """
        Description:
        Constructs a commander with default placeholder stats and loads the
        card back image. Actual stats are set by each subclass's setup().

        Parameters:
            owner (Player): the player who owns this commander
            x (int): initial screen x position
            y (int): initial screen y position
            w (int): card width in pixels
            h (int): card height in pixels
            hidden (bool): unused for commanders
        """
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
        self.particle_font = pygame.font.SysFont('Arial',int(80))
        self.font_desc = pygame.font.SysFont('Arial',int(self.w/self.text_factor_desc))
        self.image_string = "card_images/card_back.png"
        self.back_image_string = "card_images/card_back.png"
        self.image = pygame.image.load(self.image_string).convert_alpha()
        self.back_image = pygame.image.load(self.back_image_string).convert_alpha()
        # self.action_button = Button(100, 100, self.w/2, self.h/2, "attack", self.font, self.color_font, self.color_light, self.color_dark)
        # self.retreat_button = Button(100, 100, self.w/2, self.h/2, "retreat", self.font, self.color_font, self.color_light, self.color_dark)
        # self.buttons = [self.action_button, self.retreat_button]

    def __getstate__(self):
        """
        Description:
        Custom pickle stuuff matching Card.__getstate__. Strips pygame
        Surfaces and Fonts so the commander can be sent over the network.
        The client restores them via hydrate() after receiving the state.

        Returns:
            state (dict): instance dict with unpickleable assets set to None
        """
    # This tells Pickle what to save. We remove Surfaces and Fonts.
        state = self.__dict__.copy()
        keys_to_remove = ['image', 'back_image', 'font', 'font_desc', 'small_font', 'big_font']
        for key in keys_to_remove:
            if key in state:
                state[key] = None
        return state

    def draw(self, screen):
        """
        Description:
        Renders the commander card at its current position. Unlike Card.draw(),
        this does not use a font or image cache as commanders are drawn once per
        frame at a fixed size so its whatever. Makes the image slightly transparent
        when hp reaches 0. Draws name and description with the same word-wrap
        logic as Card.draw().

        Parameters:
            screen (pygame.Surface): the pygame display surface to draw onto
        """
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
        """
        Description:
        Sets the player who owns this commander.

        Parameters:
            owner (Player): the player who owns this commander
        """
        self.owner = owner

    def touching(self, mouse):
        """
        Description:
        Checks if the mouse cursor is over this commander's bounding box.
        Used by big_game for click detection when selecting attack targets.

        Parameters:
            mouse (tuple): (x, y) mouse position from pygame.mouse.get_pos()

        Returns:
            bool: true if the mouse is within the commander's rectangular bounds
        """
        return self.x <= mouse[0] <= self.x+(self.w) and self.y <= mouse[1] <= self.y+(self.h)

    def set_y(self, y):
        """
        Description:
        Sets the commander's y position and returns self for chaining.

        Parameters:
            y (int): the y coordinate to move to
        """
        self.y = y
        return self
    
    def set_x(self, x):
        """
        Description:
        Sets the commander's x position and returns self for chaining.

        Parameters:
            x (int): the x coordinate to move to
        """
        self.x = x
        return self
    
    def set_coords(self, coords):
        """
        Description:
        Sets both x and y from a position tuple.

        Parameters:
            coords (tuple): (x, y) position to place the commander
        """
        self.x, self.y = coords
        return self
    
    def set_desired_y(self, y):
        """
        Description:
        Sets the target y for the lerp animation system.

        Parameters:
            y (int): the y coordinate to animate toward
        """
        self.desired_y = y
        return self

    def set_desired_x(self, x):
        """
        Description:
        Sets the target x for the lerp animation system.

        Parameters:
            x (int): the x coordinate to animate toward
        """
        self.desired_x = x
        return self
    
    def set_w(self, w):
        """
        Description:
        Sets the commander width in pixels.

        Parameters:
            w (int): commander card width in pixels
        """
        self.w = w
        return self
    
    def set_h(self, h):
        """
        Description:
        Sets the commander height in pixels.

        Parameters:
            h (int): commander card height in pixels
        """
        self.h = h
        return self

    def set_hidden(self, hidden):
        """
        Description:
        Sets hidden state. This came from Card, commanders
        are never actually hidden in normal gameplay.

        Parameters:
            hidden (bool): true to mark as hidden
        """
        self.hidden = hidden
        return self
    
    def set_image(self, front=None, back=None):
        """
        Description:
        Loads commander art from card_images/. Works the same as Card.set_image().

        Parameters:
            front (str): filename stem for the commander image (e.g. "biden")
            back (str): filename stem for the back, usually left as None
        """
        if front is not None:
            self.image_string = f"card_images/{front}.png"
        if back is not None:
            self.back_image_string = f"card_images/{back}.png"
        self.image = pygame.image.load(self.image_string).convert_alpha()
        self.back_image = pygame.image.load(self.back_image_string).convert_alpha()

    def attacked(self, target):
        """
        Description:
        Called when this commander takes a hit. Checks hp and calls die()
        if it has dropped to 0. Fires on_attacked() which subclasses can
        override if needed (none currently do).

        Parameters:
            target (Card): the card that attacked this commander

        Returns:
            particles (list): particles from on_attacked on action
        """
        particles = []
        if self.hp <= 0:
            self.die()
        particles.extend(self.on_attacked(target))
        return particles
    
    def die(self):
        """
        Description:
        Commander death. The actual game-ending logic lives in big_game's
        win detection loop which checks player.dead each frame. This is just
        here so die() doesn't crash if called.

        Returns:
            list: empty particles list
        """
        particles = []
        return particles

    def ai_value(self):
        """
        Description:
        Base targeting priority score for the AI. Subclasses in commander_classes.py
        override this to add commander-specific urgency on top of this base calculation.

        Lethal check: if hp <= 10, return a very high score so the AI always
        prioritises finishing off a near-dead commander. The closer to 0, the higher
        the score.

        Base value scales up as the commander takes damage (damaged = more urgent to
        kill). If the owner has active threats (high-ATK cards or engine cards like
        Pump/Medic), reduce value slightly to prioritise killing threats instead.

        Returns:
            int: targeting priority score (higher = more urgent to attack)
        """
        # LETHAL CHEC
        # if the commander is at 10 HP or less, it becomes the highest priority target.
        if self.hp <= 10:
            return 2000 - (self.hp * 50)

        value = (15 - self.hp) * 2
        
        # count high-threat units
        active_threats = len([c for c in self.owner.active if c.atk >= 3 or c.name in ["Pump", "Medic"]])
        
        if active_threats > 0:
            value -= 40

        return value
    
    #actual gameplay
    def on_turn_start(self):
        """
        Description:
        on action called at the start of the owning player's turn. Base does nothing.
        Override for per-turn passive effects (Jesus heals a random ally).

        Returns:
            list: particles to display (empty by default)
        """
        return []
    
    def on_attacked(self, target):
        """
        Description:
        on action called after this commander takes damage. Base does nothing useful
        beyond checking if we're dead (which attacked() already does).
        Override if a commander needs to react to being hit.

        Parameters:
            target (Card): the card that attacked this commander

        Returns:
            list: particles to display (empty by default)
        """
        particles = []
        if self.hp <= 0:
            self.on_die()
        return particles
    
    def on_card_played(self, card):
        """
        Description:
        on action called when a non-spell card is played to the active zone.
        Base does nothing. Override for on-play passives (Biden, Miku, Sonic).

        Parameters:
            card (Card): the card that was just played

        Returns:
            list: particles to display (empty by default)
        """
        return []
    
    def on_spell_played(self, card):
        """
        Description:
        on action called when a spell card is played. Separate from on_card_played so
        commanders can respond differently to spells vs regular cards.
        Base does nothing. Override for spell passives (Alchemist).

        Parameters:
            card (Card): the spell card that was just played

        Returns:
            list: particles to display (empty by default)
        """
        return []
    
    def on_card_death(self, card):
        """
        Description:
        on action called when one of this commander's allies dies. Base does nothing.
        Override for death-trigger passives (GLaDOS draws a card).

        Parameters:
            card (Card): the ally that just died

        Returns:
            list: particles to display (empty by default)
        """
        return []
    
    def on_enemy_death(self, enemy_card):
        """
        Description:
        on action called when an enemy card is destroyed by one of this commander's allies.
        Base does nothing. Override for kill-reward passives (Shadow gains mana).

        Parameters:
            enemy_card (Card): the enemy card that was just destroyed

        Returns:
            list: particles to display (empty by default)
        """
        return []

    def on_die(self):
        """
        Description:
        on action called when this commander's hp hits 0. Base does nothing.
        The actual game end is detected by big_game's win loop each frame.
        """
        pass

    def on_retreat(self):
        """
        Description:
        on action called when this commander retreats. Commanders can't actually
        retreat in normal gameplay.
        """
        pass
