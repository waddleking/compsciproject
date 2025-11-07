import pygame

class Button():
    def __init__(self, bx1, by1, sx1, sy1, bt1, font, color_font, color_light, color_dark, color_invalid = None):
        self.x = bx1
        self.y = by1
        self.width = sx1
        self.height = sy1
        self.text = bt1
        self.text_width, self.text_height = font.size(bt1)
        self.font = font
        self.color_font, self.color_light, self.color_dark = color_font, color_light, color_dark
        self.color_invalid = color_invalid

    def draw(self, screen, greyed=False):
        mouse = pygame.mouse.get_pos()

        if greyed:
            pygame.draw.rect(screen,self.color_invalid,[self.x-(self.width/2),self.y,self.width,self.height])
        else:
            if self.x-(self.width/2) <= mouse[0] <= self.x+(self.width/2) and self.y <= mouse[1] <= self.y+self.height:
                pygame.draw.rect(screen,self.color_light,[self.x-(self.width/2),self.y,self.width,self.height])
                
            else: 
                pygame.draw.rect(screen,self.color_dark,[self.x-(self.width/2),self.y,self.width,self.height])

        screen.blit(self.font.render(self.text, True, self.color_font), (self.x-(self.text_width/2), (self.y+(self.height/2)-(self.text_height/2))))

    def touching(self):
        mouse = pygame.mouse.get_pos()
        return self.x-(self.width/2) <= mouse[0] <= self.x+(self.width/2) and self.y <= mouse[1] <= self.y+self.height
    
class Text():
    def __init__(self, bx1, by1, sx1, sy1, bt1, font, color_font, color, background=True):
        self.x = bx1
        self.y = by1
        self.width = sx1
        self.height = sy1
        self.text = bt1
        self.text_width, self.text_height = font.size(bt1)
        self.font = font
        self.color_font, self.color = color_font, color
        self.background = background
        self.alpha = 255

    def draw(self, screen):
        if self.background:
            pygame.draw.rect(screen,self.color,[self.x-(self.width/2),self.y,self.width,self.height])
        ts = self.font.render(self.text, True, self.color_font)
        ts.set_alpha(self.alpha)
        screen.blit(ts, (self.x-(self.text_width/2), (self.y+(self.height/2)-(self.text_height/2))))

    def touching(self):
        mouse = pygame.mouse.get_pos()
        return self.x-(self.width/2) <= mouse[0] <= self.x+(self.width/2) and self.y <= mouse[1] <= self.y+self.height
    
    def set_alpha(self, alpha):
        self.alpha = alpha
        return self
    
class Card():
    def __init__(self, value, x, y, hidden=False):
        self.value = value
        self.x = x
        self.y = y
        self.desired_x = None
        self.desired_y = None
        self.hidden = hidden
        self.image = pygame.image.load(f"cards/{value}.png").convert_alpha()

    def set_y(self, y):
        self.y = y
        return self
    
    def set_x(self, x):
        self.x = x
        return self
    
    def set_desired_y(self, y):
        self.desired_y = y
        return self

    def set_desired_x(self, x):
        self.desired_x = x
        return self

    def set_hidden(self, hidden):
        self.hidden = hidden
        return self
