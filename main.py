import os
import random
import pygame
import sys
import serial.tools.list_ports
import serial
import threading

pygame.init()
# If the code is frozen, use this path:
if getattr(sys, "frozen", False):
    currentPath = sys._MEIPASS
# If it's not use the path we're on now
else:
    currentPath = os.path.dirname(__file__)

# Game Variables
game_active = False
game_start = True
gravity = 0.25
bird_movement = 0
score = 0
high_score = 10
WIN_SCORE = 5

SPAWNPIPE = pygame.USEREVENT
pygame.time.set_timer(SPAWNPIPE, 4000)
pipe_height = [300, 450, 600]

BIRDFLAP = pygame.USEREVENT + 1
pygame.time.set_timer(BIRDFLAP, 200)


def get_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if str(port.manufacturer).__contains__("Arduino"):
            return port.device


def draw_flor():
    screen.blit(floor_surface, (floor_x_pos, 675))
    screen.blit(floor_surface, (floor_x_pos + 432, 675))


def create_pipe():
    random_pipe_pos = random.choice(pipe_height)
    bottom_pipe = pipe_surface.get_rect(midtop=(500, random_pipe_pos))
    top_pipe = pipe_surface.get_rect(midbottom=(500, random_pipe_pos - 250))
    return bottom_pipe, top_pipe


def move_pipes(pipes):
    for pipe in pipes:
        pipe.centerx -= 5
    return pipes


def draw_pipes(pipes):
    for pipe in pipes:
        if pipe.bottom >= 768:
            screen.blit(pipe_surface, pipe)
        else:
            flip_pipe = pygame.transform.flip(pipe_surface, False, True)
            screen.blit(flip_pipe, pipe)


def check_collision(pipes):
    for pipe in pipes:
        if bird_rect.colliderect(pipe):
            # death_sound.play()
            return False
        if bird_rect.top <= -75 or bird_rect.bottom >= 675:
            death_sound.play()
            return False
    return True


def rotate_bird(bird):
    new_bird = pygame.transform.rotozoom(bird, -bird_movement * 3, 1)
    return new_bird


def bird_animation():
    new_bird = bird_surface
    new_bird_rect = new_bird.get_rect(center=(75, bird_rect.centery))
    return new_bird, new_bird_rect


def score_display(game_state):
    score_surface = game_font.render(f"Score: {int(score)}", True, (255, 255, 255))
    score_rect = score_surface.get_rect(center=(216, 75))
    screen.blit(score_surface, score_rect)

    if not game_state:
        high_score_surface = game_font.render(
            f"High Score: {int(high_score)}", True, (255, 255, 255)
        )
        high_score_rect = high_score_surface.get_rect(center=(216, 735))
        screen.blit(high_score_surface, high_score_rect)


def update_score(score, high_score):
    if score > high_score:
        high_score = score
    return high_score


pygame.mixer.pre_init(frequency=44100, size=16, channels=1)
pygame.init()
screen = pygame.display.set_mode((432, 768))
clock = pygame.time.Clock()
game_font = pygame.font.Font(os.path.join(currentPath, "fonts/04B_19.TTF"), 40)

bg_surface = pygame.transform.scale2x(
    pygame.image.load(
        os.path.join(currentPath, "assets/background-night.png")
    ).convert()
)

floor_surface = pygame.transform.scale2x(
    pygame.image.load(os.path.join(currentPath, "assets/base.png")).convert()
)
floor_x_pos = 0

bird_size = (70, 70)

bird_index = 0
bird_surface = pygame.transform.scale(
    pygame.image.load(
        os.path.join(currentPath, "assets/chich.png")
    ).convert_alpha(),
    bird_size
)
bird_rect = bird_surface.get_rect(center=(75, 384))

pipe_surface = pygame.image.load(os.path.join(currentPath, "assets/pipe-green.png"))
pipe_surface = pygame.transform.scale2x(pipe_surface)
pipe_list = []

game_over_surface = pygame.transform.scale2x(
    pygame.image.load(os.path.join(currentPath, "assets/gameover.png")).convert_alpha()
)

flag = pygame.transform.scale(
    pygame.image.load(os.path.join(currentPath, "assets/win.png")).convert_alpha(),
    (400, 130)
)

game_over_rect = game_over_surface.get_rect(center=(216, 384))
flag_rest = flag.get_rect(center=(216, 384))
game_start_surface = pygame.transform.scale2x(
    pygame.image.load(os.path.join(currentPath, "assets/message.png")).convert_alpha()
)
game_start_rect = game_over_surface.get_rect(center=(216, 192))

flap_sound = pygame.mixer.Sound(os.path.join(currentPath, "sounds/sfx_wing.wav"))
death_sound = pygame.mixer.Sound(os.path.join(currentPath, "sounds/sfx_die.wav"))
score_sound = pygame.mixer.Sound(os.path.join(currentPath, "sounds/sfx_point.wav"))
score_sound_count = 0

serialPort = serial.Serial(get_arduino_port(), 9600)

commands = []

lock = threading.Lock()


def arduino_worker():
    global command, lock
    while True:
        command = serialPort.readline().decode('utf-8').strip()

        if command == "UP":
            lock.acquire()
            commands.append(command)
            lock.release()


thread = threading.Thread(target=arduino_worker)

thread.start()

while True:
    for event in pygame.event.get():
        # Quit
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # if event.type == pygame.KEYDOWN:
        #     print(f"{event.key} Key")
        #     print(f"{keys[random_key]} Value")
        #     pass#print("KEYDOWN")
        #     #print(event.key, event)
        #     #exit()

        command = ""

        if len(commands) > 0:
            command = commands.pop()

        if (
                event.type == pygame.MOUSEBUTTONDOWN
                or event.type == pygame.KEYDOWN
                or command == "UP"
        ):
            game_start = False
            # JUMP
            # print(event.key)
            if game_active:
                if command == "UP":
                    flap_sound.play()
                    bird_movement = 0
                    bird_movement -= 5
                    command = ""
            # Restart game
            else:
                if event.type == pygame.KEYDOWN and event.key == 32:
                    game_active = True
                    pipe_list.clear()
                    bird_rect.center = (75, 384)
                    bird_movement = 0
                    score = 0

        # Create pipes
        if event.type == SPAWNPIPE and game_active:
            pipe_list.extend(create_pipe())
    # BG
    screen.blit(bg_surface, (0, 0))
    # Floor
    floor_x_pos -= 1
    draw_flor()
    if floor_x_pos <= -384:
        floor_x_pos = 0

    if game_start:
        screen.blit(game_start_surface, game_start_rect)

    if game_active and not game_start:
        # Bird
        bird_movement += gravity
        rotated_bird = rotate_bird(bird_surface)

        bird_rect.centery += bird_movement
        screen.blit(rotated_bird, bird_rect)
        game_active = check_collision(pipe_list)
        # Pipe
        pipe_list = move_pipes(pipe_list)
        draw_pipes(pipe_list)

        score += 0.01
        score_sound_count += 1
        if score_sound_count >= 100:
            score_sound.play()
            score_sound_count = 0
        score_display(True)

    elif not game_start and score < WIN_SCORE:
        screen.blit(game_over_surface, game_over_rect)
        # print(random_key)
        high_score = update_score(score, high_score)
        score_display(False)
    if score >= WIN_SCORE:
        game_active = False
        screen.blit(flag, flag_rest)
        score_display(False)
    pygame.display.update()
    clock.tick(60)
