from classes import Particle
from main_classes import Commander
from random import choice, randint

class Biden(Commander):
    def setup(self):
        self.name = "Biden"
        self.desc = "When you play a Pump, gain +1 Mana."
        self.hp = 25
        self.set_image("biden")
        return self

    def on_card_played(self, card):
        if card.name == "Pump":
            self.owner.mana += 1
            return [Particle(self.owner.mana_position[0], self.owner.mana_position[1], 1, self.font, self.hp_color_font, self.atk_color_font),
                    Particle(self.x + self.w//2, self.y, "Economics", self.font, self.color_font, self.color_font)
                    ]
        return []

    def ai_value(self):
        base = super().ai_value()
        pumps = len([c for c in self.owner.active if c.name == "Pump"])

        # existing pumps already triggered biden on play so the damage is done
        future_threat = max(0, (3 - pumps)) * 10

        # lots of pumps + high mana = the economy is running and biden is fueling more plays
        economy_running = pumps * 14

        return base + future_threat + economy_running


class Miku(Commander):
    def setup(self):
        self.name = "Miku"
        self.desc = "When you play a card costing 1 or less, heal it for 2 HP."
        self.hp = 21
        self.set_image("miku")
        return self

    def on_card_played(self, card):
        if card.cost <= 1:
            print("miku triggered")
            card.hp += 2
            return [
                Particle(card.x, card.y, 2, self.font, self.hp_color_font, self.atk_color_font),
                Particle(self.x + self.w//2, self.y, "Colorful Stage", self.font, self.color_font, self.color_font)
            ]
        return []

    def ai_value(self):
        base = super().ai_value()

        # cards already on board already got their heal
        small_units_buffed = len([c for c in self.owner.active if c.cost <= 1])
        already_buffed_penalty = small_units_buffed * 5  # miku already did her job for these

        swarm_threat = small_units_buffed * 8

        return base + swarm_threat - already_buffed_penalty


class Alchemist(Commander):
    def setup(self):
        self.name = "Alchemist"
        self.desc = "Whenever you play a spell, draw 1 card."
        self.hp = 20
        self.set_image("alchemist")
        return self

    def on_spell_played(self, card):
        print("alchemist triggered")
        self.owner.draw(1, False)
        return [Particle(self.x + self.w//2, self.y, "Alchemy", self.font, self.color_font, self.color_font)]

    def ai_value(self):
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
    def setup(self):
        self.name = "Jesus"
        self.desc = "At the start of your turn, give +1 hp to a random active ally."
        self.hp = 33
        self.set_image("jesus")
        return self

    def on_turn_start(self):
        if self.owner.active:
            card = choice(self.owner.active)
            card.hp += 1
            print(f"jesus healed {card.name}")
            return [
                Particle(card.x+card.w//2+randint(-32,32), card.y+card.h//2+randint(-32,32), 1, self.font, self.hp_color_font, self.atk_color_font),
                Particle(self.x + self.w//2, self.y, "Miracle", self.font, self.color_font, self.color_font)
            ]
        return []

    def ai_value(self):
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
    def setup(self):
        self.name = "GLaDOS"
        self.desc = "When an ally dies, draw 1 card."
        self.hp = 22
        self.set_image("glados")
        return self

    def on_card_death(self, card):
        print("triggered glados")
        self.owner.draw(1, False)
        return [
            Particle(self.x + self.w//2, self.y, "Testing", self.font, self.color_font, self.color_font)
        ]

    def ai_value(self):
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
    def setup(self):
        self.name = "Sonic"
        self.desc = "Your cards gain +1 Action when played."
        self.hp = 15
        self.set_image("sonic")
        return self

    def on_card_played(self, card):
        print("triggered sonic")
        card.actions += 1
        return [
            Particle(card.x, card.y, "+ACT", self.font, self.hp_color_font, self.atk_color_font),
            Particle(self.x + self.w//2, self.y, "Gotta Go Fast!", self.font, self.color_font, self.color_font)
            ]

    def ai_value(self):
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
    def setup(self):
        self.name = "Shadow"
        self.desc = "When an ally destroys an enemy, gain +1 Mana."
        self.hp = 25
        self.set_image("shadow")
        return self

    def on_enemy_death(self, enemy_card):
        self.owner.mana += 1
        print("triggered shadow")
        return [
            Particle(self.owner.mana_position[0], self.owner.mana_position[1], 1, self.font, self.hp_color_font, self.atk_color_font),
            Particle(self.x + self.w//2, self.y, "Chaos Control", self.font, self.color_font, self.color_font)
        ]

    def ai_value(self):
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