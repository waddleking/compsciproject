from main_classes import Card
from classes import Particle
from random import randint

AI_CONFIG = {
    "fragile_classes": ("Pump", "Medic", "Musketeer", "Sponge", "Snowball"),
    "attacker_targets": {
        "early": (0, 1),
        "mid": (6, 2),
        "late": (11, 3)
    },
    "limits": {
        "Pump": {"soft": 3, "hard": 4},
        "Taunt": {"soft": 2, "hard": 3},
        "Medic": {"soft": 1, "hard": 2}
    }
}

def is_protected(player):
    return any(c.taunt > 0 for c in player.active)

def get_attacker_target(turn):
    target = AI_CONFIG["attacker_targets"]["early"][1]
    if turn >= AI_CONFIG["attacker_targets"]["late"][0]:
        target = AI_CONFIG["attacker_targets"]["late"][1]
    elif turn >= AI_CONFIG["attacker_targets"]["mid"][0]:
        target = AI_CONFIG["attacker_targets"]["mid"][1]
    return target

def count_active_by_name(player, class_name):
    return len([c for c in player.active if c.__class__.__name__ == class_name])

# cards

class Amogus(Card):
    def setup(self):
        self.name = "amogus"
        self.desc = "from the hit game among us"
        self.hp = 2
        self.atk = 2
        self.cost = 1
        self.retreat_cost = 0
        self.set_image("amogus")
        return self
    
    def ai_value(self):
        # High priority early to fill board
        attackers = len([c for c in self.owner.active if c.atk > 0])
        target = get_attacker_target(self.owner.game.turn)
        return 25 if attackers < target else 10

class Pump(Card):
    def setup(self):
        self.name = "Pump"
        self.desc = "Generates 1 energy per turn"
        self.hp = 5
        self.atk = 0
        self.cost = 1
        self.retreat_cost = 5
        self.set_image("pump")
        return self
    
    def ai_value(self):
        pumps_active = count_active_by_name(self.owner, "Pump")
        if pumps_active >= AI_CONFIG["limits"]["Pump"]["hard"]: return 0
        
        # PROTECTION CHECK: Reduce value by 70% if no taunt is active
        base_val = 40 if pumps_active < AI_CONFIG["limits"]["Pump"]["soft"] else 20
        if not is_protected(self.owner):
            base_val *= 0.3 
            
        return base_val

    def on_turn_start(self):
        self.owner.mana += 1
        return [Particle(self.owner.mana_position[0]+randint(-32,32), self.owner.mana_position[1]+randint(-32,32), 1, self.font, self.hp_color_font, self.atk_color_font)]

class Hong(Card):
    def setup(self):
        self.name = "Hong"
        self.desc = "Taiping Heavenly King"
        self.hp = 4
        self.atk = 5
        self.cost = 4
        self.retreat_cost = 2
        self.set_image("hong")
        return self
    
    def ai_value(self):
        # High priority early to fill board
        attackers = len([c for c in self.owner.active if c.atk > 0])
        target = get_attacker_target(self.owner.game.turn)
        return 50 if attackers < target else 30

class IceCube(Card):
    def setup(self):
        self.name = "Ice Cube"
        self.desc = "Taunt: 1"
        self.taunt = 1
        self.hp = 2
        self.atk = 0
        self.cost = 1
        self.retreat_cost = 1
        self.set_image("icecube")
        return self
    
    def ai_value(self):
        taunts_active = len([c for c in self.owner.active if c.taunt > 0])
        if taunts_active >= AI_CONFIG["limits"]["Taunt"]["hard"]: return 5
        
        # High value if we HAVE fragile units on board that need protection
        fragile_on_board = any(c.__class__.__name__ in AI_CONFIG["fragile_classes"] for c in self.owner.active)
        return 50 if fragile_on_board and taunts_active == 0 else 25

class Thorn(Card):
    def setup(self):
        self.name = "Thorn"
        self.desc = "Taunt: 1. Deals 2 damage back to anyone who attacks it."
        self.taunt = 1
        self.hp = 3
        self.atk = 1
        self.cost = 2
        self.set_image("thorn")
        return self
    
    def ai_value(self):
        taunts_active = len([c for c in self.owner.active if c.taunt > 0])
        limits = AI_CONFIG["limits"]["Taunt"]
        if taunts_active >= limits["hard"]: return 2
        
        val = 18 if taunts_active < limits["soft"] else 6
        fragile_units = len([c for c in self.owner.active if c.__class__.__name__ in AI_CONFIG["fragile_classes"]])
        return val + (fragile_units * 5)

    def on_attacked(self, attacker):
        particles = []
        attacker.hp -= 2
        particles.append(Particle(attacker.x + attacker.w/2, attacker.y + attacker.h/2, -2, self.font, self.hp_color_font, self.atk_color_font))
        attacker.attacked(self)
        return particles
    
class Medic(Card):
    def setup(self):
        self.name = "Medic"
        self.desc = "Heals your commander for 2 HP at the start of your turn."
        self.hp = 3
        self.atk = 0
        self.cost = 2
        self.set_image("medic")
        return self
    
    def ai_value(self):
        missing_hp = 25 - self.owner.commander.hp
        medics_active = count_active_by_name(self.owner, "Medic")
        if medics_active >= AI_CONFIG["limits"]["Medic"]["hard"]: return 0
        
        # PROTECTION CHECK: Medics are high priority targets; don't play without cover
        val = (missing_hp * 3)
        if not is_protected(self.owner):
            val -= 20
        return max(5, val)

    def on_turn_start(self):
        self.owner.commander.hp += 2
        return [Particle(self.owner.commander_position[0]+self.owner.commander.w//2+randint(-32,32), self.owner.commander_position[1]+self.owner.commander.h//2+randint(-32,32), 2, self.font, self.hp_color_font, self.atk_color_font)]

class Sponge(Card):
    def setup(self):
        self.name = "Sponge"
        self.desc = "Gains +1 ATK every time it is attacked and survives."
        self.hp = 5
        self.atk = 2
        self.cost = 2
        self.set_image("sponge")
        return self
    
    def ai_value(self):
        attackers = len([c for c in self.owner.active if c.atk > 0])
        target = get_attacker_target(self.owner.game.turn)
        bonus = 25 if attackers < target else 0
        if not is_protected(self.owner):
            bonus *= 0.3
        return 7 + len([c for c in self.owner.active if c.taunt > 0]) * 3 + bonus

    def on_attacked(self, attacker):
        particles = []
        if self.hp > 0:
            self.atk += 1
        return particles
    
class Kamikaze(Card):
    def setup(self):
        self.name = "Kamikaze"
        self.desc = "Deals 10 damage to the enemy commander and dies immediately."
        self.hp = 0
        self.atk = 10
        self.cost = 6
        self.set_image("kamikaze")
        return self
    
    def ai_value(self):
        enemy = next(p for p in self.owner.game.players if p != self.owner)
        if enemy.commander.hp <= 10: return 1000
        return 20

    def on_play(self):
        particles = []
        for player in self.owner.game.players:
            if player != self.owner:
                player.commander.hp -= 10
                particles.extend(player.commander.attacked(self))
                particles.append(Particle(player.commander.x+player.commander.w/2, player.commander.y+player.commander.h/2, -10, self.font, self.hp_color_font, self.atk_color_font))
        self.hp = 0
        self.die()
        return particles

class Bin(Card):
    def setup(self):
        self.name = "Bin"
        self.desc = "Draw 1 card."
        self.hp = 2
        self.atk = 0
        self.cost = 3
        self.selection_type = ""
        self.set_image("bin")
        return self
    
    def ai_value(self):
        return 20 - len(self.owner.hand)

    def on_action(self):
        self.owner.draw(1, cost=0)
        self.actions -= 1
        return []
    
class Retriever(Card):
    def setup(self):
        self.name = "Retriever"
        self.desc = "Draw 1 card for 1 mana."
        self.hp = 2
        self.atk = 0
        self.cost = 2
        self.selection_type = ""
        self.set_image("retriever")
        return self
    
    def ai_value(self):
        return 20 - len(self.owner.hand)
    
    def on_play(self):
        self.actions -= 1
        return []

    def on_action(self):
        if self.owner.mana > 0:
            self.actions -= 1
            self.owner.draw(1, cost=1)
        return []
    
class Musketeer(Card):
    def setup(self):
        self.name = "Musketeer"
        self.desc = "Ignores Taunt."
        self.ignore_taunt = True
        self.hp = 1
        self.atk = 3
        self.cost = 3
        self.set_image("musketeer")
        return self
    
    def ai_value(self):
        enemy = next(p for p in self.owner.game.players if p != self.owner)
        enemy_has_taunt = any(c.taunt > 0 for c in enemy.active)
        
        # If enemy has a taunt, Musketeer is vital. 
        # But if WE don't have a taunt, he will die after one shot.
        val = 45 if enemy_has_taunt else 15
        if not is_protected(self.owner):
            val -= 20
        return max(5, val)
    
class Net(Card):
    def setup(self):
        self.name = "Net"
        self.desc = "Play one card for free. One time use."
        self.selection_type = "hand"
        self.hp = 1
        self.atk = 0
        self.cost = 3
        self.set_image("net")
        return self
    
    def ai_value(self):
        hand_values = [c.ai_value() for c in self.owner.hand if c.name != "Net"]
        return max(hand_values) if hand_values else 0
    
    def on_play(self):
        self.actions -= 1
        return []
    
    def on_action(self, target):
        target.play(False)
        self.actions -= 1
        self.hp = 0
        self.die()
        return []
    
class BagOfGold(Card):
    def setup(self):
        self.name = "Bag of Gold"
        self.desc = "Gives 1 mana."
        self.spell = True
        self.hp = 0
        self.atk = 0 
        self.cost = 0
        self.set_image("bagofgold")
        return self
    
    def ai_value(self):
        current_mana = self.owner.mana
        best_enablable_value = 0
        for card in self.owner.hand:
            if card != self and card.cost == current_mana + 1:
                potential_val = card.ai_value()
                if potential_val > best_enablable_value:
                    best_enablable_value = potential_val
        
        return best_enablable_value + 2 if best_enablable_value > 0 else 1

    def on_play(self):
        self.owner.mana += 1
        self.hp = 0
        self.die()
        return [Particle(self.owner.mana_position[0], self.owner.mana_position[1], 1, self.font, self.hp_color_font, self.atk_color_font)]

class Snowball(Card):
    def setup(self):
        self.name = "Snowball"
        self.desc = "Gets +1/+1 per turn"
        self.hp = 1
        self.atk = 0
        self.cost = 4
        self.retreat_cost = 10
        self.set_image("snowball")
        return self
    
    def ai_value(self):
        # Snowball needs time to grow. Value is near zero without protection.
        if not is_protected(self.owner):
            return 2
        return 15 + (self.owner.game.turn * 2)

    def on_turn_start(self):
        self.atk += 1
        self.hp += 1
        return []
    
class B52(Card):
    def setup(self):
        self.name = "B52"
        self.desc = "Deals 1 damage to every enemy card."
        self.spell = True
        self.hp = float("inf")
        self.atk = 0 
        self.cost = 2
        self.set_image("b52")
        return self
    
    def ai_value(self):
        base = 0
        for player in self.owner.game.players:
            if player != self.owner:
                for card in player.active:
                    if card.hp <= 1:
                        base += 1
        return base * 20

    def on_play(self):
        particles = []
        
        for player in self.owner.game.players:
            if player != self.owner:
                for card in player.active:
                    card.hp -= 1
                    card.attacked(self)
                    particles.append(Particle(card.x+card.w//2, card.y+card.h//2, -1, self.font, self.hp_color_font, self.atk_color_font))
        self.hp = 0
        self.die()
        return particles