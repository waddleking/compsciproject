from main_classes import Card
from classes import Particle

class Amogus(Card):
    def setup(self):
        self.name = "amogus"
        self.desc = "from the hit game among us"
        self.hp = 2
        self.atk = 1
        self.cost = 1
        self.retreat_cost = 1
        self.set_image("amogus")

class Pump(Card):
    def setup(self):
        self.name = "Pump"
        self.desc = "Generates 1 energy per turn"
        self.hp = 5
        self.atk = 0
        self.cost = 1
        self.retreat_cost = 5
        self.set_image("elixir_pump")

    def on_turn_start(self):
        self.owner.mana += 1

class HongXiuQuan(Card):
    def setup(self):
        self.name = "Hong"
        self.desc = "Taiping Heavenly King"
        self.hp = 5
        self.atk = 5
        self.cost = 2
        self.retreat_cost = 3
        self.set_image("hongxiuquan")

class IceCube(Card):
    def setup(self):
        self.name = "Ice"
        self.desc = "Taunt: 1"
        self.taunt = 1
        self.hp = 3
        self.atk = 0
        self.cost = 1
        self.retreat_cost = 1
        self.max_actions = 0
        self.set_image("ice_cube")

class Thorn(Card):
    """deals damage back when attacked."""
    def setup(self):
        self.name = "Thorn"
        self.desc = "Deals 1 damage back to anyone who attacks it."
        self.hp = 3
        self.atk = 0
        self.cost = 2
        self.set_image("thorn")

    def on_attacked(self, attacker):
        particles = super().on_attacked(attacker)
        
        attacker.hp -= 1
        particles.append(Particle(attacker.x + attacker.w/2, attacker.y + attacker.h/2, -1, self.font, self.hp_color_font, self.atk_color_font))
        
        if attacker.hp <= 0:
            attacker.on_die()
            
        return particles
    
class Medic(Card):
    """heals the commander at the start of every turn."""
    def setup(self):
        self.name = "Medic"
        self.desc = "Heals your commander for 2 HP at the start of your turn."
        self.hp = 3
        self.atk = 1
        self.cost = 2
        self.set_image("medic")

    def on_turn_start(self):
        self.owner.commander.hp += 2

class Sponge(Card):
    """gets stronger when it survives an attack."""
    def setup(self):
        self.name = "Sponge"
        self.desc = "Gains +1 ATK every time it is attacked and survives."
        self.hp = 5
        self.atk = 1
        self.cost = 2
        self.set_image("sponge")

    def on_attacked(self, attacker):
        particles = super().on_attacked(attacker)
        if self.hp > 0:
            self.atk += 1
        return particles
    
class Kamikaze(Card):
    """huge damage, but dies instantly when played."""
    def setup(self):
        self.name = "Kamikaze"
        self.desc = "Deals 10 damage to the enemy commander and dies immediately."
        self.hp = 1
        self.atk = 0 # effect happens on play, not by attacking
        self.cost = 4
        self.set_image("kamikaze")

    def on_play(self):
        super().on_play() # original logic handles mana and moving to active
        
        # find the enemy (the player who isn't the owner)
        for player in self.owner.game.players:
            if player != self.owner:
                player.commander.hp -= 10
                # trigger the red damage particle on the enemy commander
                player.commander.on_attacked(self) 
        
        # kill itself immediately
        self.hp = 0
        self.on_die()

class Bin(Card):
    """draws a card when it leaves the field."""
    def setup(self):
        self.name = "Bin"
        self.desc = "Draw 1 card."
        self.hp = 2
        self.atk = 1
        self.cost = 1
        self.selection_type = ""
        self.set_image("bin")

    def on_action(self):
        self.owner.draw(1, cost=0) # free draw
        self.actions -= 1
        return []