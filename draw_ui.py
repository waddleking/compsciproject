import pygame
from random import randint
from classes import Card
import time

def draw_chips_ui(screen, res, small_font, big_font, color_font, chips, quota, overlay_chips=None):
    if overlay_chips == None: overlay_chips = chips
    # print(chips,overlay_chips)
    ui_color = (169,169,169)
    pygame.draw.rect(screen,ui_color,[20,30,250+big_font.size(str(overlay_chips))[0],160], border_radius=50)
    screen.blit(pygame.transform.scale(pygame.image.load(f"cards/chip.png").convert_alpha(), (200, 200)), ((10, 10)))
    screen.blit(big_font.render(str(overlay_chips), True, color_font), (210, 55))
    screen.blit(small_font.render("quota: "+str(quota), True, color_font), (50, 255))
    return chips
    if overlay_chips == chips:
        return overlay_chips
    else:
        if overlay_chips < chips:
            return overlay_chips + 1
        if overlay_chips > chips:
            return overlay_chips - 1

def draw_card_ui(screen, cards_array, res, card_w=100, card_h=100, gap=0):

    done = True
    
    for player in cards_array:
        pgap = gap
        while len(player)*(pgap+card_w) > res[0]:
            pgap -= 5
        for i in range(len(player)):
            player[i].desired_x = (res[0]-((card_w+pgap)*len(player)))/2+((card_w+pgap)*i)+(pgap/2)
            if player[i].desired_x is not None:
                if player[i].x != player[i].desired_x:
                    done = False
                    distance = player[i].desired_x - player[i].x
                    if distance**2 < 50:
                        player[i].x = player[i].desired_x
                    else:
                        player[i].x += (distance)/5

            if player[i].desired_y is not None:
                if player[i].y != player[i].desired_y:
                    done = False
                    distance = player[i].desired_y - player[i].y
                    if distance**2 < 50:
                        player[i].y = player[i].desired_y
                    else:
                        player[i].y += (distance)/5

            if player[i].hidden == False:       
                # screen.blit(pygame.transform.scale(pygame.image.load(f"cards/{player[i].value}.png").convert_alpha(), (card_w, card_h)), ((player[i].x, player[i].y)))
                screen.blit(pygame.transform.scale(player[i].image, (card_w, card_h)), ((player[i].x, player[i].y)))
            else:
                screen.blit(pygame.transform.scale(pygame.image.load(f"cards/back.png").convert_alpha(), (card_w, card_h)), ((player[i].x, player[i].y)))

    return done

def draw_win_fail_screen(screen, text, y, big_font, res):
    s = pygame.Surface(res)  
    s.set_alpha(128)              
    s.fill((0, 0, 0))          
    screen.blit(s, (0, y))

    text_width, th1 = big_font.size(text)
    screen.blit(big_font.render(text, True, (255, 255, 255)), ((res[0]-text_width)/2, (res[1]/2)+y))

def draw_background(screen, current_background, color_background):
    screen.fill(current_background)
    for i in range(3):
        if current_background[i] < color_background[i]:
            current_background[i] += 0.1
        elif current_background[i] > color_background[i]:
            current_background[i] -= 0.1
    return current_background

if __name__ == "__main__":
    pygame.init() 
    small_font = pygame.font.SysFont('Arial',35) 
    big_font = pygame.font.SysFont('Arial',100) 
    color_font = (255, 255, 255) 
    color_background =(128, 212, 121)
    width, height = pygame.display.Info().current_w, pygame.display.Info().current_h
    res = (width, height)
    screen = pygame.display.set_mode(res)
    chips = 0
    cards = []

    for suit in ["diamonds", "hearts", "clubs", "spades"]:
        for value in ["ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "king", "queen", "jack"]:
            cards.append(Card(f"{value}_of_{suit}", res[0], res[1]/2))
    cards_array = [[]]

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: 
                pygame.quit() 
            if ev.type == pygame.MOUSEBUTTONDOWN: 
                chips += 1
                random = randint(0,len(cards)-1)
                cards_array[0].append(cards[random])
                cards.pop(random)

        current_background = draw_background(screen, current_background, color_background)

        draw_chips_ui(screen, res, chips, small_font, big_font, color_font)
        draw_card_ui(screen, cards_array, res)

        pygame.display.update()