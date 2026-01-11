from main_classes import Commander

class Biden(Commander):
    def setup(self):
        self.name = "biden"
        self.desc = "one of the presidents of all time"
        self.hp = 25
        self.set_image("joe_biden")

class HatsuneMiku(Commander):
    def setup(self):
        self.name = "Miku"
        self.desc = "Hatsune Miku"
        self.hp = 21
        self.set_image("hatsune_miku")
        self.color_font = (0, 0, 0) 