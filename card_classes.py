from main_classes import Card

class Amogus(Card):
    def setup(self):
        self.name = "amogus"
        self.desc = "from the hit game among us"
        self.hp = 2
        self.atk = 1
        self.cost = 1
        self.retreat_cost = 1
        self.set_image("amogus")

class Biden(Card):
    def setup(self):
        self.name = "biden"
        self.desc = "one of the presidents of all time"
        self.hp = 1
        self.atk = 2
        self.cost = 1
        self.retreat_cost = 1
        self.set_image("joe_biden")

class Pump(Card):
    def setup(self):
        self.name = "Pump"
        self.desc = "Generates 1 energy per turn"
        self.hp = 5
        self.atk = 0
        self.cost = 2
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
        self.name = "Ice Cube"
        self.desc = "Taunt: 1"
        self.taunt = 1
        self.hp = 3
        self.atk = 0
        self.cost = 2
        self.retreat_cost = 1
        self.max_actions = 0
        self.set_image("ice_cube")