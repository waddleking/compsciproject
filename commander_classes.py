from classes import Particle
from main_classes import Commander
from random import choice, randint

class Biden(Commander):
    """
    Description:
    Every time you play a Pump, Biden hands you +1 mana immediately
    on top of whatever the Pump will generate next turn. Since Pump
    now fires at and up to the mana cap (pushing you one above it), Biden turns
    each pump play into instant tempo and a higher ceiling.

    Attributes:
        hp (int): 25
        desc (str): "When you play a Pump, gain +1 Mana."
    """
    def setup(self):
        """
        Description:
        Sets Biden's stats and loads his image.

        Returns:
            self: for chaining
        """
        self.name = "Biden"
        self.desc = "When you play a Pump, gain +1 Mana."
        self.hp = 25
        self.set_image("biden")
        return self

    def on_card_played(self, card):
        """
        Description:
        Fires when any non-spell card is played. Does nothing unless it's a Pump,
        at which point Biden hands you +1 mana immediately.
        Two particles: one at the mana display (the actual mana gain), one at Biden
        himself saying "Economics".

        Parameters:
            card (Card): the card that was just played

        Returns:
            list: [mana particle, "Economics" text particle] if it was a Pump,
                empty list if it was literally anything else
        """
        if card.name == "Pump":
            self.owner.mana += 1
            return [
                Particle(self.owner.mana_position[0], self.owner.mana_position[1], 1, self.particle_font, self.hp_color_font, self.atk_color_font),
                Particle(self.x + self.w//2, self.y, "Economics", self.particle_font, self.color_font, self.color_font)
            ]
        return []

    def ai_value(self):
        """
        Description:
        future_threat is highest when there are no pumps yet.
        economy_running reflects that existing pumps mean Biden is 
        already generating tempo and enabling
        plays the AI can't match without doing something about it.

        Returns:
            int: targeting priority score on top of the base lethal/HP calculation
        """
        base = super().ai_value()
        pumps = len([c for c in self.owner.active if c.name == "Pump"])

        # existing pumps already triggered biden on play so the damage is done
        future_threat = max(0, (3 - pumps)) * 10

        # lots of pumps + high mana = the economy is running and biden is fueling more plays
        economy_running = pumps * 14

        return base + future_threat + economy_running


class Miku(Commander):
    """
    Description:
    The cheap-cards commander. Heals every cost-1-or-less card you play by 2hp
    on entry. This turns IceCube into a 4hp taunt for 1 mana (deeply unfair),
    Pump into a 7hp engine that basically never dies behind a Thorn wall, and
    Skeleton into something that can actually survive Thorn retaliation.
    She rewards going wide with cheap durable stuff instead of a few big threats.

    Attributes:
        hp (int): 21 - the price of a powerful passive
        desc (str): "When you play a card costing 1 or less, heal it for 2 HP."
    """
    def setup(self):
        """
        Description:
        Sets Miku's stats and loads her image.

        Returns:
            self: for chaining
        """
        self.name = "Miku"
        self.desc = "When you play a card costing 1 or less, heal it for 2 HP."
        self.hp = 21
        self.set_image("miku")
        return self

    def on_card_played(self, card):
        """
        Description:
        Fires when any non-spell card is played. If it cost 1 or less, heals it
        by 2hp immediately. The heal happens on entry so the card has the buffed hp
        for its entire time on the board. Spawns two particles: a +2 on the card
        itself and a "Colorful Stage" text at Miku's position.

        Parameters:
            card (Card): the card that was just played

        Returns:
            list: [heal particle on card, flavour text at Miku] if cost <= 1,
                empty list otherwise
        """
        if card.cost <= 1:
            print("miku triggered")
            card.hp += 2
            return [
                Particle(card.x, card.y, 2, self.particle_font, self.hp_color_font, self.atk_color_font),
                Particle(self.x + self.w//2, self.y, "Colorful Stage", self.particle_font, self.color_font, self.color_font)
            ]
        return []

    def ai_value(self):
        """
        Description:
        The value is in future plays getting healed - cards already on the board
        already got their buff and are no longer Miku's doing. A big board of
        cost-1 stuff means more cards of that type are being drawn and played,
        which is the threat. The already_buffed_penalty stops the AI from treating
        Miku as equally dangerous once her swarm is already established.

        Returns:
            int: targeting priority score on top of the base calculation
        """
        base = super().ai_value()

        # cards already on board already got their heal
        small_units_buffed = len([c for c in self.owner.active if c.cost <= 1])
        already_buffed_penalty = small_units_buffed * 5  # miku already did her job for these

        swarm_threat = small_units_buffed * 8

        return base + swarm_threat - already_buffed_penalty


class Alchemist(Commander):
    """
    Description:
    The draw-engine commander. Draws a card whenever you play a spell costing
    1 or less. In practice only BagOfGold (cost 0) qualifies - B52 (2), Kamikaze
    (6), and FatMan (7) are all too expensive. The engine: play BagOfGold → +1
    mana + draw a card → if you drew another BagOfGold, play it again → repeat
    until you've drawn into FatMan or Hong and have the mana to play them.
    Kill him before the first bag fires, not after.

    Attributes:
        hp (int): 20 - low enough to punish a slow start
        desc (str): "Whenever you play a spell costing 1 or less, draw 1 card."
    """
    def setup(self):
        """
        Description:
        Sets Alchemist's stats and loads his image.

        Returns:
            self: for chaining
        """
        self.name = "Alchemist"
        self.desc = "Whenever you play a spell costing 1 or less, draw 1 card."
        self.hp = 20
        self.set_image("alchemist")
        return self

    def on_spell_played(self, card):
        """
        Description:
        Fires when a spell is played. Draws 1 card if the spell cost 1 or less.
        Currently only BagOfGold hits the trigger. Always returns a particle
        regardless of whether a draw happened, so you always see that Alchemist
        noticed the spell even if he didn't do anything about it.

        Parameters:
            card (Card): the spell that was just played

        Returns:
            list: ["Alchemy" text particle at Alchemist] always - draw is a bonus
        """
        if card.cost <= 1:
            print("alchemist triggered")
            self.owner.draw(1, False)
        return [Particle(self.x + self.w//2, self.y, "Alchemy", self.particle_font, self.color_font, self.color_font)]

    def ai_value(self):
        """
        Description:
        The danger window is a small hand. That means the chain is about to start
        and there's nothing in the way. A big hand means the engine already fired
        and he's sitting on the winnings, which is bad but less immediately urgent
        than the moment before he draws into five bags. Empty hand is a panic state
        because one topdeck spell triggers the whole thing.

        Returns:
            int: targeting priority score on top of the base calculation
        """
        base = super().ai_value()
        hand_size = len(self.owner.hand)

        # big hand = alchemist has already drawn a bunch and is winning card advantage anyway
        # small hand = alchemist is about to start drawing and the chain is about to kick off
        # kill him before the bag of gold chain starts not after
        draw_engine_urgency = max(0, (4 - hand_size)) * 15

        # if they have very few cards they might top deck a spell and draw into the win
        # this is the danger window
        empty_hand_panic = 25 if hand_size <= 1 else 0

        return base + draw_engine_urgency + empty_hand_panic


class Jesus(Commander):
    """
    Description:
    The sustain commander. At the start of every turn, heals +1hp to a random
    ally. This sounds like nothing until you realise chip damage literally never
    sticks, Sponge and Snowball become nearly unkillable by attrition, and Medic
    stacks on top of this for a combined 3hp/turn on whatever lucky card Jesus
    keeps choosing. He rewards building a wide board so the heal is always landing
    somewhere valuable.

    Attributes:
        hp (int): 33 - highest HP in the game, appropriate for the divine
        desc (str): "At the start of your turn, give +1 hp to a random active ally."
    """
    def setup(self):
        """
        Description:
        Sets Jesus's stats and loads his image.

        Returns:
            self: for chaining
        """
        self.name = "Jesus"
        self.desc = "At the start of your turn, give +1 hp to a random active ally."
        self.hp = 33
        self.set_image("jesus")
        return self

    def on_turn_start(self):
        """
        Description:
        Fires at the start of the owning player's turn. Picks one card from the
        active zone at random and heals it by 1hp. Does nothing if the board is
        empty, which is the universe's way of saying you should have played more cards.
        The particle is jittered randomly within the card's bounds so it looks
        like the heal is appearing from within rather than dropping from above.

        Returns:
            list: [heal particle on the lucky card, "Miracle" text at Jesus],
                or empty list if the board is empty and he has nobody to heal
        """
        if self.owner.active:
            card = choice(self.owner.active)
            card.hp += 1
            print(f"jesus healed {card.name}")
            return [
                Particle(card.x+card.w//2+randint(-32,32), card.y+card.h//2+randint(-32,32), 1, self.particle_font, self.hp_color_font, self.atk_color_font),
                Particle(self.x + self.w//2, self.y, "Miracle", self.particle_font, self.color_font, self.color_font)
            ]
        return []

    def ai_value(self):
        """
        Description:
        Jesus gets more dangerous the more cards are on the board - each heal
        landing on Sponge or Snowball is worth significantly more than healing
        a random Skeleton. Empty board means Jesus is just a 33hp target doing
        nothing, so the AI correctly deprioritises him until the board fills up.
        At 10hp or below the lethal check overrides all of this and he becomes
        the highest priority target.

        Returns:
            int: targeting priority score (overrides base entirely at low HP,
                otherwise adds board-size and juicy-target bonuses on top)
        """
        if self.hp <= 10:
            return 2000 - (self.hp * 50)

        base = 30 + (33 - self.hp) * 2

        active_count = len(self.owner.active)
        healing_threat = active_count * 14

        # specifically if they have sponge or snowball, jesus tops them up
        juicy_targets = len([c for c in self.owner.active if c.__class__.__name__ in ("Sponge", "Snowball", "Medic")])
        sustain_bonus = juicy_targets * 18

        # but if their board is empty jesus is just a guy doing nothing
        if active_count == 0:
            return max(5, base)

        return max(5, base + healing_threat + sustain_bonus)


class GLaDOS(Commander):
    """
    Description:
    The sacrifice commander. Draws a card whenever one of your allies dies.
    This turns trading into card advantage and deliberate self-sacrifice into
    a draw engine. The ideal play is to flood the board with cheap fragile stuff,
    let it die in combat (or nuke it yourself with FatMan), and draw a full hand
    while the opponent is looking at an empty board wondering what just happened.

    Attributes:
        hp (int): 22 - needs to survive long enough to cash in on the draws
        desc (str): "When an ally dies, draw 1 card."
    """
    def setup(self):
        """
        Description:
        Sets GLaDOS's stats and loads her image.

        Returns:
            self: for chaining
        """
        self.name = "GLaDOS"
        self.desc = "When an ally dies, draw 1 card."
        self.hp = 22
        self.set_image("glados")
        return self

    def on_card_death(self, card):
        """
        Description:
        Fires whenever one of this player's non-spell cards dies. Draws one card
        for free. Spells don't trigger this because they're not really "dying",
        they're just resolving and leaving. GLaDOS only rewards actual death,
        preferably dramatic death, preferably several of them in one turn.

        Parameters:
            card (Card): the ally that just died for science

        Returns:
            list: ["Testing" text particle at GLaDOS's position]
        """
        print("triggered glados")
        self.owner.draw(1, False)
        return [
            Particle(self.x + self.w//2, self.y, "Testing", self.particle_font, self.color_font, self.color_font)
        ]

    def ai_value(self):
        """
        Description:
        The real threat is fragile cards on the board - each one at 2hp or below
        is a pending free draw waiting to happen. A big hand means she already cashed
        in; a small hand with several fragile cards is the most dangerous state and
        triggers the setup_panic bonus. already_drawn_penalty stops the AI from
        panicking about GLaDOS once she's already drawn six cards and the damage is done.

        Returns:
            int: targeting priority score on top of the base calculation
        """
        base = super().ai_value()
        hand_size = len(self.owner.hand)
        enemy_board = self.owner.active

        # lots of 1hp cards on their board = lots of incoming draws from glados = very urgent
        fragile_fodder = len([c for c in enemy_board if c.hp <= 2])
        draw_chain_threat = fragile_fodder * 16

        # their hand being massive is the outcome not the opportunity
        already_drawn_penalty = max(0, hand_size - 4) * 8

        # small hand + fragile board = kill glados NOW before the death draws start
        setup_panic = 20 if (hand_size <= 2 and fragile_fodder >= 2) else 0

        return base + draw_chain_threat - already_drawn_penalty + setup_panic


class Sonic(Commander):
    """
    Description:
    The aggression commander. Every non-spell card played gets +1 action on entry,
    which is effectively haste for everything. This is already very good for normal
    attackers. It becomes completely stupid with Net (Net is not a spell so Sonic
    fires, Net gets +1 action immediately, Net uses it to free-play something this
    turn = Net+Hong is 3 mana for a 4/4 that also attacks this turn). 15hp means
    if you don't win fast, you die.

    Attributes:
        hp (int): 15 - the lowest HP in the game, gotta go fast or go home
        desc (str): "Your cards gain +1 Action when played."
    """
    def setup(self):
        """
        Description:
        Sets Sonic's stats and loads his image.

        Returns:
            self: for chaining
        """
        self.name = "Sonic"
        self.desc = "Your cards gain +1 Action when played."
        self.hp = 15
        self.set_image("sonic")
        return self

    def on_card_played(self, card):
        """
        Description:
        Fires when any non-spell card is played. Gives it +1 action immediately.
        Works on everything - attackers, taunts, Net, Retriever. The +1 action
        stacks with the card's existing actions, so a card that starts with 1 action
        now has 2 and can act twice on the turn it enters if it has max_actions >= 2.

        Parameters:
            card (Card): the newly played card that is about to go fast

        Returns:
            list: ["+ACT" particle on the card, "Gotta Go Fast!" text at Sonic]
        """
        print("triggered sonic")
        card.actions += 1
        return [
            Particle(card.x, card.y, "+ACT", self.particle_font, self.hp_color_font, self.atk_color_font),
            Particle(self.x + self.w//2, self.y, "Gotta Go Fast!", self.particle_font, self.color_font, self.color_font)
            ]

    def ai_value(self):
        """
        Description:
        Cards already on the board have already received their Sonic action bonus -
        that value is spent. The real threat is cards still in hand, each one a
        pending immediate attack the turn it's played. Low HP makes him always at
        least somewhat urgent since even a couple of Amoguses can finish him in
        a few swings. existing_board_penalty stops the AI from panicking about Sonic
        once his haste board is already established and doing its thing.

        Returns:
            int: targeting priority score on top of the base calculation
        """
        base = super().ai_value()

        # sonic at 15hp is already fairly easy to kill
        hand_size = len(self.owner.hand)
        incoming_haste_threat = min(hand_size, 4) * 18

        # existing board already has sonic actions baked in
        existing_board = len(self.owner.active)
        existing_board_penalty = existing_board * 6

        # sonic is always at least somewhat urgent because of low hp
        # even a weak board can kill him in a few turns and he cant heal
        low_hp_urgency = max(0, (20 - self.hp) * 4)

        return base + incoming_haste_threat - existing_board_penalty + low_hp_urgency


class Shadow(Commander):
    """
    Description:
    The momentum commander. Every time one of your allies kills something, +1 mana.
    This turns combat into a resource engine - Hong one-shots most things for
    reliable +1 mana per swing, Musketeer kills engine cards through taunt for +1
    mana per engine kill, and FatMan wiping a full board can net up to +6 mana in
    a single turn (including your own cards - Shadow's on_enemy_death fires for
    every card attacked(self) is called on, which FatMan does to everything).

    Attributes:
        hp (int): 25 - needs to survive long enough for the kills to compound
        desc (str): "When an ally destroys an enemy, gain +1 Mana."
    """
    def setup(self):
        """
        Description:
        Sets Shadow's stats and loads his image.

        Returns:
            self: for chaining
        """
        self.name = "Shadow"
        self.desc = "When an ally destroys an enemy, gain +1 Mana."
        self.hp = 25
        self.set_image("shadow")
        return self

    def on_enemy_death(self, enemy_card):
        """
        Description:
        Fires when an enemy card is destroyed by one of this player's allies.
        Gives +1 mana. Note: FatMan triggers this for every card it kills on
        either side since it calls card.attacked(self) through the damage chain,
        which eventually fires on_enemy_death on the attacker's commander - and
        FatMan's owner is Shadow's player, so Shadow gets mana for everyone.

        Parameters:
            enemy_card (Card): the card that was just destroyed

        Returns:
            list: [mana particle at mana display, "Chaos Control" text at Shadow]
        """
        self.owner.mana += 1
        print("triggered shadow")
        return [
            Particle(self.owner.mana_position[0], self.owner.mana_position[1], 1, self.particle_font, self.hp_color_font, self.atk_color_font),
            Particle(self.x + self.w//2, self.y, "Chaos Control", self.particle_font, self.color_font, self.color_font)
        ]

    def ai_value(self):
        """
        Description:
        Shadow is only dangerous when there are cards that can actually kill things.
        No killers = no mana gains = he's just a 25hp target. Hong and Musketeer
        get a large reliable_bonus because they kill on single hits, generating mana
        reliably rather than chipping and hoping. If there are genuinely no killers,
        returns below base to deprioritise Shadow and focus the actual threats instead.

        Returns:
            int: targeting priority score on top of the base calculation,
                or below base if there's nothing threatening on his board
        """
        base = super().ai_value()

        # only dangerous if they can actually kill things
        killers = [c for c in self.owner.active if c.atk >= 2]
        kill_threat = len(killers) * 22

        # specifically hong (atk 4) and musketeer (atk 3) are reliable shadow triggers
        reliable_triggers = len([c for c in self.owner.active if c.__class__.__name__ in ("Hong", "Musketeer", "Sponge") and c.atk >= 3])
        reliable_bonus = reliable_triggers * 20

        # focus the actual threats instead
        if not killers:
            return max(5, base - 20)

        return base + kill_threat + reliable_bonus