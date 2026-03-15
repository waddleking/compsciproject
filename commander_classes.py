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
        return base + (pumps * 15)

class Miku(Commander):
    def setup(self):
        self.name = "Miku"
        self.desc = "When you play a card costing 1 or less, heal it for 2 HP."
        self.hp = 21
        self.set_image("miku")
        # self.color_font = (0, 0, 0) 
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
        small_units = len([c for c in self.owner.active if c.cost <= 1])
        return base + (small_units * 10)
    
class Alchemist(Commander):
    def setup(self):
        self.name = "Alchemist"
        self.desc = "Whenever you play a spell, draw 1 card."
        self.hp = 20
        self.atk = 0
        self.set_image("alchemist")
        return self

    def on_spell_played(self, card):
        print("alchemist triggered")
        self.owner.draw(1, False)
        return [Particle(self.x + self.w//2, self.y, "Alchemy", self.font, self.color_font, self.color_font)]
            
    def ai_value(self):
        return super().ai_value() + 30
    
class Jesus(Commander):
    def setup(self):
        self.name = "Jesus"
        self.desc = "At the start of your turn, give +1 hp to a random active ally."
        self.hp = 33 # High base HP to reflect durability
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

        base_val = 50 + (33 - self.hp) * 2
        
        active_count = len(self.owner.active)
        
        return base_val + (active_count * 10)
    
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
        # More dangerous if the opponent is low on cards
        return base + (20 if hand_size < 3 else 5)
    
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
        active_count = len(self.owner.active)
        return base + 50 - (active_count * 10)
    
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
        base = 50 + (25 - self.hp) * 2
        
        # Count allies with enough ATK to likely kill something
        threats = len([c for c in self.owner.active if c.atk >= 2])
        
        # If the opponent has a lot of mana-generation potential, Shadow is high priority
        return base + (threats * 20)