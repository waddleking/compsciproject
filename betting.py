import pygame
from classes import Button
from draw_ui import draw_chips_ui, draw_background
from menu import run_menu

def run_bets(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, color_invalid, chips, quota, small_bet_size, medium_bet_size, big_bet_size):
    bw = 50
    bh = 50
    add_button = Button(res[0]/2+200, res[1]-100, bw, bh, "+", small_font, color_font, color_light, color_dark, color_invalid)
    add_add_button = Button(res[0]/2+250, res[1]-100, bw, bh, "++", small_font, color_font, color_light, color_dark, color_invalid)
    add_add_add_button = Button(res[0]/2+300, res[1]-100, bw, bh, "+++", small_font, color_font, color_light, color_dark, color_invalid)

    subtract_button = Button(res[0]/2-200, res[1]-100, bw, bh, "-", small_font, color_font, color_light, color_dark, color_invalid)
    subtract_subtract_button = Button(res[0]/2-250, res[1]-100, bw, bh, "--", small_font, color_font, color_light, color_dark, color_invalid)
    subtract_subtract_subtract_button = Button(res[0]/2-300, res[1]-100, bw, bh, "", small_font, color_font, color_light, color_dark, color_invalid)

    max_min_pos = 250

    done_button = Button(res[0]/2, res[1]-250, 200, 50, "done", small_font, color_font, color_light, color_dark, color_invalid)

    add_add_button_valid = medium_bet_size <= chips
    add_add_add_button_valid = big_bet_size <= chips

    subtract_subtract_button_valid = medium_bet_size <= chips
    subtract_subtract_subtract_button_valid = big_bet_size <= chips

    if add_add_button_valid:
        max_min_pos += 50
    if add_add_add_button_valid:
        max_min_pos += 50

    max_button = Button(res[0]/2+max_min_pos, res[1]-100, bw, bh, "max", small_font, color_font, color_light, color_dark, color_invalid)
    min_button = Button(res[0]/2-max_min_pos, res[1]-100, bw, bh, "min", small_font, color_font, color_light, color_dark, color_invalid)
    
    bet = 0

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.MOUSEBUTTONDOWN: 
                if add_button.touching():
                    if bet + small_bet_size <= chips:
                        bet += small_bet_size
                    else:
                        bet = chips
                if subtract_button.touching():
                    if bet >= small_bet_size:
                        bet -= small_bet_size
                    else:
                        bet = 0
                if add_add_button.touching() and add_add_button_valid:
                    if bet + medium_bet_size <= chips:
                        bet += medium_bet_size
                    else:
                        bet = chips
                if subtract_subtract_button.touching() and subtract_subtract_button_valid:
                    if bet >= medium_bet_size:
                        bet -= medium_bet_size
                    else:
                        bet = 0
                if add_add_add_button.touching() and add_add_add_button_valid:
                    if bet + big_bet_size <= chips:
                        bet += big_bet_size
                    else:
                        bet = chips
                if subtract_subtract_subtract_button.touching() and subtract_subtract_subtract_button_valid:
                    if bet >= big_bet_size:
                        bet -= big_bet_size
                    else:
                        bet = 0

                if max_button.touching():
                    bet = chips

                if min_button.touching():
                    bet = 0

                if done_button.touching():
                    if bet != 0:
                        return bet
        current_background = draw_background(screen, current_background, color_background)
        
        add_button.draw(screen)
        subtract_button.draw(screen)
        if add_add_button_valid:
            add_add_button.draw(screen)
        if subtract_subtract_button_valid:
            subtract_subtract_button.draw(screen)
        if add_add_add_button_valid:
            add_add_add_button.draw(screen)
        if subtract_subtract_subtract_button_valid:
            subtract_subtract_subtract_button.draw(screen)

        max_button.draw(screen)
        min_button.draw(screen)
        done_button.draw(screen, bet == 0)
        draw_chips_ui(screen, res, small_font, big_font, color_font, chips, quota)

        screen.blit(big_font.render(str(bet), True, color_font), ((res[0]/2)-(big_font.size(str(bet))[0]/2), res[1]-145))

        pygame.display.update()