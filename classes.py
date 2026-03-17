import pygame

class Button():
    """
    Description:
    A clickable rectangle with a text label. Draws itself in color_light when
    the mouse is hovering over it and color_dark otherwise, so the player gets
    visual feedback without any extra work. Draws greyed out (using color_invalid)
    when greyed=True, which is how the campaign menu shows locked stages.

    draw() returns self so it can be chained.

    Attributes:
        x (int): horizontal centre of the button
        y (int): top edge of the button
        w (int): button width
        h (int): button height
        text (str): label displayed on the button
    """
    def __init__(self, bx1, by1, sx1, sy1, bt1, font, color_font, color_light, color_dark, color_invalid = None):
        """
        Description:
        Builds a button. x,y is the centre-top point: the rectangle extends
        w/2 to the left and right of x, and h downward from y.

        Parameters:
            bx1 (int): horizontal centre position
            by1 (int): top edge y position
            sx1 (int): width
            sy1 (int): height
            bt1 (str): label text
            font (pygame.font.Font): font for the label
            color_font (tuple): text colour
            color_light (tuple): background colour when hovered
            color_dark (tuple): background colour when not hovered
            color_invalid (tuple or None): background colour when greyed out
        """
        self.x = bx1
        self.y = by1
        self.w = sx1
        self.h = sy1
        self.text = bt1
        self.text_width, self.text_height = font.size(bt1)
        self.font = font
        self.color_font, self.color_light, self.color_dark = color_font, color_light, color_dark
        self.color_invalid = color_invalid

    def draw(self, screen, greyed=False):
        """
        Description:
        Draws the button. If greyed, fills with color_invalid regardless of hover
        state. Otherwise fills with color_light on hover, color_dark off hover.

        Parameters:
            screen (pygame.Surface): the display surface to draw onto
            greyed (bool): if True, draws the locked/disabled version

        Returns:
            self: for chaining
        """
        if greyed:
            pygame.draw.rect(screen,self.color_invalid,[self.x-(self.w/2),self.y,self.w,self.h])
        else:
            if self.touching():
                pygame.draw.rect(screen,self.color_light,[self.x-(self.w/2),self.y,self.w,self.h])
                
            else: 
                pygame.draw.rect(screen,self.color_dark,[self.x-(self.w/2),self.y,self.w,self.h])

        screen.blit(self.font.render(self.text, True, self.color_font), (self.x-(self.text_width/2), (self.y+(self.h/2)-(self.text_height/2))))
        return self

    def touching(self):
        """
        Description:
        Checks whether the mouse cursor is currently over this button.

        Returns:
            bool: True if the mouse is within the button's bounding rectangle
        """
        mouse = pygame.mouse.get_pos()
        return self.x-(self.w/2) <= mouse[0] <= self.x+(self.w/2) and self.y <= mouse[1] <= self.y+self.h
    
class Text():
    """
    Description:
    A drawable text label, optionally with a coloured background rectangle.
    Supports alpha (for the victory/turn-change fade animations) via set_alpha().
    Supports both centred and left-aligned rendering via the centered parameter
    in draw(). This was added purely because I got annoyed at the stage subtitle
    text being off.

    Attributes:
        x (int): horizontal position (centre if centred, left edge otherwise)
        y (int): top edge position
        alpha (int): 0-255 opacity, set via set_alpha(), defaults to 255
    """
    def __init__(self, bx1, by1, sx1, sy1, bt1, font, color_font, color, background=True):
        """
        Description:
        Creates a text object. Width and height are only used for the background
        rectangle and for centering the text vertically within the bounds.

        Parameters:
            bx1 (int): x position (centre if drawing centred, left edge otherwise)
            by1 (int): top edge y position
            sx1 (int): width of the background rectangle (0 for no box)
            sy1 (int): height of the background rectangle
            bt1 (str): text to display
            font (pygame.font.Font): font to render with
            color_font (tuple): text colour
            color (tuple or None): background rectangle colour, None = no background
            background (bool): whether to draw the background rectangle at all
        """
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

    def draw(self, screen, centered=True):
        """
        Description:
        Draws the text onto the screen. If centered=True, x is treated as the
        horizontal centre and the text is horizontally centred on it. The text
        is always vertically centred within the height bounds.

        Parameters:
            screen (pygame.Surface): the display surface to draw onto
            centered (bool): if True, x is the horizontal centre; if False, x is
                the left edge
        """
        if centered:
            if self.background:
                pygame.draw.rect(screen,self.color,[self.x-(self.width/2),self.y,self.width,self.height])
            ts = self.font.render(self.text, True, self.color_font)
            ts.set_alpha(self.alpha)
            screen.blit(ts, (self.x-(self.text_width/2), (self.y+(self.height/2)-(self.text_height/2))))
        else:
            if self.background:
                pygame.draw.rect(screen,self.color,[self.x,self.y,self.width,self.height])
            ts = self.font.render(self.text, True, self.color_font)
            ts.set_alpha(self.alpha)
            screen.blit(ts, (self.x, (self.y+(self.height/2)-(self.text_height/2))))

    def touching(self):
        """
        Description:
        Checks whether the mouse is over this text element's bounding box.
        Not used by any current code.

        Returns:
            bool: True if the mouse is within the text's bounding rectangle
        """
        mouse = pygame.mouse.get_pos()
        return self.x-(self.width/2) <= mouse[0] <= self.x+(self.width/2) and self.y <= mouse[1] <= self.y+self.height
    
    def set_alpha(self, alpha):
        """
        Description:
        Sets the opacity for the next draw() call. Used by big_game for the
        victory overlay and turn-change banner.

        Parameters:
            alpha (int): opacity from 0 (invisible) to 255 (fully opaque)

        Returns:
            self: for chaining
        """
        self.alpha = alpha
        return self
    
class Particle():
    """
    Description:
    A floating number that drifts upward and fades out over time. Used for
    damage numbers, heal numbers, and mana gain notifications during gameplay.
    Positive values (no minus sign) draw in color_positive (green); negative
    values (contain "-") draw in color_negative (red). Non-integer strings like
    "Economics" or "Gotta Go Fast!" also work and display as flavour text.

    alpha starts at 255 and decreases by 2 each draw() call. When alpha < 0
    big_game removes the particle from the list. y drifts upward at a rate
    proportional to alpha so it slows down as it fades.

    Attributes:
        x (float): horizontal position, stays fixed
        y (float): vertical position, drifts upward each frame
        alpha (int): current opacity, counts down to -1 then the particle dies
        value (str): the text being displayed (converted from int if needed)
        color (tuple): resolved from color_positive or color_negative at init
    """
    def __init__(self, x, y, value, font, color_positive, color_negative):
        """
        Description:
        Creates a particle at (x, y). If value is an int it's converted to a
        string. Color is determined by whether the string contains a minus sign.

        Parameters:
            x (float): initial x position (usually centre of the source card)
            y (float): initial y position (usually centre of the source card)
            value (int or str): what to display
            font (pygame.font.Font): font to render with (usually particle_font, 80pt)
            color_positive (tuple): colour for positive/neutral values
            color_negative (tuple): colour for negative values (anything with "-")
        """
        self.x = x
        self.y = y
        self.font = font
        # self.color_positive = color_positive
        # self.color_negative = color_negative
        self.alpha = 255
        if isinstance(value, int):
            self.value = str(value)
        else:
            self.value = value

        if self.value.count("-") != 0:
            self.color = color_negative
        else:
            self.color = color_positive
        self.text_width, self.text_height = font.size(self.value)

    def draw(self, screen):
        """
        Description:
        Renders the particle at its current position, then advances its state:
        alpha decreases by 2, y drifts upward by alpha/250. The drift slows
        as the particle fades since alpha is shrinking.

        Parameters:
            screen (pygame.Surface): the display surface to draw onto
        """
        # if self.value < 0:
        #     ts = self.font.render(str(self.value), True, self.color_negative)
        # else:
        #     ts = self.font.render("+"+str(self.value), True, self.color_positive)
        ts = self.font.render(self.value, True, self.color)
        ts.set_alpha(self.alpha)
        screen.blit(ts, (self.x-(self.text_width/2), (self.y-(self.text_height/2))))
        self.alpha -= 2
        self.y -= self.alpha/250
    
class Card():
    """
    Description:
    The legacy card class from the original card games this project was before.
    Represents a playing card with a value (like "ace_of_spades"), an image loaded from the cards/ folder,
    and a position with lerp animation support (desired_x/desired_y). Not to be confused with
    the Card class in main_classes.py which is a completely different thing that
    the actual game uses. This one is only used in draw_ui.py as a base_card
    placeholder to draw the face-down deck pile (not in the actual game).

    Attributes:
        value (str): card name used to load the image
        x (float): current x position
        y (float): current y position
        desired_x (float or None): animation target x
        desired_y (float or None): animation target y
        hidden (bool): unused in current code
    """
    def __init__(self, value, x, y, hidden=False):
        """
        Description:
        Creates a legacy card and immediately loads its image from cards/{value}.png.
        Note: the main_classes.Card uses card_images/ as its image folder. This one
        uses cards/ which is the old folder from the previous game.

        Parameters:
            value (str): image filename stem, loads cards/{value}.png
            x (float): initial x position
            y (float): initial y position
            hidden (bool): not currently used for anything
        """
        self.value = value
        self.x = x
        self.y = y
        self.desired_x = None
        self.desired_y = None
        self.hidden = hidden
        self.image = pygame.image.load(f"cards/{value}.png").convert_alpha()

    def set_y(self, y):
        """
        Description:
        Sets y and returns self for chaining.

        Parameters:
            y (float): the y coordinate to set
        """
        self.y = y
        return self
    
    def set_x(self, x):
        """
        Description:
        Sets x and returns self for chaining.

        Parameters:
            x (float): the x coordinate to set
        """
        self.x = x
        return self
    
    def set_desired_y(self, y):
        """
        Description:
        Sets the lerp animation target y. The draw_ui lerp loop moves y toward
        desired_y each frame.

        Parameters:
            y (float): target y coordinate to animate toward
        """
        self.desired_y = y
        return self

    def set_desired_x(self, x):
        """
        Description:
        Sets the lerp animation target x. The draw_ui lerp loop moves x toward
        desired_x each frame.

        Parameters:
            x (float): target x coordinate to animate toward
        """
        self.desired_x = x
        return self

    def set_hidden(self, hidden):
        """
        Description:
        Sets the hidden flag and returns self for chaining.

        Parameters:
            hidden (bool): whether to hide the card
        """
        self.hidden = hidden
        return self