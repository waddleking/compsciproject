import os, pygame
from draw_ui import draw_background
from classes import Button, Text
from setup import setup_game

def load(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font):
    path = r'saves' 
    files = []
    buttons = []
    if not os.path.exists(path):
        os.makedirs(path)

    for file in os.listdir(path):
        files.append(os.fsdecode(file))

    for i in range(len(files)):
        buttons.append(Button((res[0])/2, (50*i)+200, 200, 50, files[i], small_font, color_font, color_light, current_background))
        

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: 
                pygame.quit() 

            #button 1
            if ev.type == pygame.MOUSEBUTTONDOWN: 
                for button in buttons:
                    if button.touching():
                        data = []
                        with open(path+"/"+button.text, "r")as f:
                            f = f.readlines()
                            
                            latest = f[-1].split(",")
                            data.append(int(latest[1])) #chips
                            data.append(int(f[0].split(",")[1])*(2**len(f))) #quota
                            data.append(int(latest[0])) #gamestate
                            stats = []
                            for line in [j.split(",") for j in f]:
                                stats.append([int(i) for i in line])
                            data.append(stats) #stats

                        return tuple(data)
                
                if len(buttons) == 0:
                    return setup_game()

        draw_background(screen, current_background, color_background)
        text = "load"
        screen.blit(big_font.render(text, True, color_font), ((res[0]-big_font.size(text)[0])/2, 50))
        for button in buttons:
            button.draw(screen)

        pygame.display.update()
        

def save(screen, res, color_light, color_dark, current_background, color_background, small_font, big_font, color_font, log):
    path = r'saves'
    if not os.path.exists(path):
        os.makedirs(path)
    i = 0
    itaken = []
    for file in os.listdir(path):
        itaken.append(int("".join([str(i) for i in [int(s) for s in os.fsdecode(file) if s.isdigit()]])))
    while i in itaken:
        i += 1
        
    with open(path+"/save"+str(i), "w") as f:
        f.write("\n".join([",".join([str(j) for j in i]) for i in log]))

    text = "saved to path /save"+str(i)
    text_box = Text(res[0]/2, (res[1]/2), 500, 100, text, small_font, color_font, current_background)

    while True:
        text_box.draw(screen)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: 
                pygame.quit() 

            #button 1
            if ev.type == pygame.MOUSEBUTTONDOWN: 
                return 0
            
        pygame.display.update()