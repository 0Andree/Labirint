import pygame
from pygame import *

import os.path
import sys

with open("maze.config", "r") as f:
    SETTINGS = f.readlines()


DISPLAY_SCALE = (800, 700)

def texture(name):
    return "texture/" + name

BG = transform.scale(image.load(texture("bg.png")), DISPLAY_SCALE)
WIN_SCREEN = transform.scale(image.load(texture("win_screen.png")), DISPLAY_SCALE)
LOSE_SCREEN = transform.scale(image.load(texture("lose_screen.png")), DISPLAY_SCALE)

WALL_TEXTURE = "wall.png"
PLAYER_TEXTURE = "player.png"
BULLET_TEXTURE = "bullet.png"
ENEMY_TEXTURE = "enemy.png"
ENEMY_DAMAGED_TEXTURE = "enemy_damaged.png"
FINAL_SPRITE_TEXTURE = "final_sprite.png"
BOSS_TEXTURE = "boss.png"

GAME_TITLE = SETTINGS[0].replace("\n", "")
PLAYER_SPEED = int(SETTINGS[1])
PLAYER_START_X = int(SETTINGS[2])
PLAYER_START_Y = int(SETTINGS[3])
COLLISION = bool(int(SETTINGS[4]))
ENEMY_COLLISION = bool(int(SETTINGS[5]))
BULLETS_AMOUNT = int(SETTINGS[6])
BULLETS_COOLDOWN = int(SETTINGS[7])
DEBUG = bool(int(SETTINGS[8]))

abs_path = os.path.dirname(os.path.realpath(__file__))

window = display.set_mode(DISPLAY_SCALE)
display.set_caption(GAME_TITLE)

def debug_message(message, channel="Main"):
    global DEBUG
    if DEBUG:
        print("[" + GAME_TITLE + "/Debug/" + channel + "] " + message)

def move_enemies(enemies):
    for enemy in enemies:
        enemy.move()

def move_bullets(bullets):
    for bullet in bullets:
        bullet.move()

def move_sprites(player, enemies, boss, bullets):
    player.move()
    move_enemies(enemies)
    boss.move()
    move_bullets(bullets)

def render(phonos, barriers, player, final, enemies, boss, bullets):
    window.blit(phonos, (0, 0))
    barriers.draw(window)
    bullets.draw(window)
    enemies.draw(window)
    player.draw()
    final.draw()
    boss.draw()

def win_screen(window):
    global WIN_SCREEN
    window.blit(WIN_SCREEN, (0, 0))

def lose_screen(window):
    global LOSE_SCREEN
    window.blit(LOSE_SCREEN, (0, 0))

class GameSprite(sprite.Sprite):
    def __init__(self, x, y, w, h, image, rotation=0):
        super().__init__()
        self.image = transform.rotate(pygame.image.load(os.path.join(abs_path, texture(image))), rotation)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.w = w
        self.h = h

    def draw(self):
        window.blit(self.image, (self.rect.x, self.rect.y))

class Bullet(GameSprite):
    def __init__(self, x, y):
        super().__init__(x, y, 10, 5, BULLET_TEXTURE)
        self.speed = 30

    def move(self):
        self.rect.x += self.speed
        for barrier in barriers:
            if sprite.collide_rect(self, barrier):
                bullets.remove(self)
                self.kill()
        for enemy in enemies:
            if sprite.collide_rect(self, enemy):
                enemy.damage()
                bullets.remove(self)
                self.kill()

class Player(GameSprite):
    def __init__(self, x, y, w, h, image, rotation=0):
        super().__init__(x, y, w, h, image)
        self.x_speed = 0
        self.y_speed = 0
        self.bullets = BULLETS_AMOUNT
        self.can_strike = True
    
    def strike(self):
        global bullets_cooldown
        if self.bullets >= 1 and self.can_strike:
            bullets.add(Bullet(self.rect.centerx, self.rect.centery))
            self.bullets -= 1
            bullets_cooldown += BULLETS_COOLDOWN
    
    def move(self):
        global finish
        self.rect.x += self.x_speed

        if COLLISION:
            if self.rect.left < 0: self.rect.left = 0
            if self.rect.right > DISPLAY_SCALE[0]: self.rect.right = DISPLAY_SCALE[0]

            sprites_touched = sprite.spritecollide(self, barriers, False)
            if self.x_speed > 0:  # RIGHT
                for spr in sprites_touched:
                    self.rect.right = min(self.rect.right, spr.rect.left)
            elif self.x_speed < 0:  # LEFT
                for spr in sprites_touched:
                    self.rect.left = max(self.rect.left, spr.rect.right)
        self.rect.y += self.y_speed

        if COLLISION:
            if self.rect.top < 0: self.rect.top = 0
            if self.rect.bottom > DISPLAY_SCALE[1]: self.rect.bottom = DISPLAY_SCALE[1]

            sprites_touched = sprite.spritecollide(self, barriers, False)
            if self.y_speed > 0:  # DOWN
                for spr in sprites_touched:
                    self.rect.bottom = min(self.rect.bottom, spr.rect.top)
            elif self.y_speed < 0:  # VP
                for spr in sprites_touched:
                    self.rect.top = max(self.rect.top, spr.rect.bottom)

    def add_x_speed(self, x_speed):
        self.x_speed += x_speed
    
    def add_y_speed(self, y_speed):
        self.y_speed += y_speed

    def stop_x(self):
        self.x_speed = 0

    def stop_y(self):
        self.y_speed = 0

class Enemy(GameSprite):
    def __init__(self, start_x, start_y, x1, x2, y1, y2, w, h, speed, protection=1):
        super().__init__(start_x, start_y, w, h, ENEMY_TEXTURE)
        self.protection = protection
        self.x_speed = speed
        self.y_speed = speed
        if y1 == y2:
            self.y_speed = 0
        if x1 == x2:
            self.x_speed = 0
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
    
    def move(self):
        if self.rect.x >= self.x2 and self.rect.y >= self.y2:
            self.x_speed = -self.x_speed
            self.y_speed = -self.y_speed
        elif self.rect.x <= self.x1 and self.rect.y <= self.y1:
            self.x_speed = -self.x_speed
            self.y_speed = -self.y_speed
        self.rect.x += self.x_speed
        self.rect.y += self.y_speed
    
    def damage(self):
        if self.protection >= 2:
            self.protection -= 1
            self.image = transform.scale(image.load(texture(ENEMY_DAMAGED_TEXTURE)), (self.w, self.h))
        else:
            self.kill()
            enemies.remove(self)
    
class Boss(GameSprite):
    def __init__(self):
        super().__init__(600, 620, 80, 74, BOSS_TEXTURE)
        self.x_speed = -10
        self.y_speed = -10

    def move(self):
        if self.rect.x <= 600 and self.rect.y >= 620:
            self.y_speed = -10
        if self.rect.x <= 480 and self.rect.y <= 500:
            self.x_speed = 10
        if self.rect.x >= 600 and self.rect.y <= 380:
            self.y_speed = 10
        if self.rect.x >= 720 and self.rect.y >= 500:
            self.x_speed = -10
        
        self.rect.x += self.x_speed
        self.rect.y += self.y_speed

barriers = sprite.Group()

barriers.add(GameSprite(350, 350, 100, 350, WALL_TEXTURE))
barriers.add(GameSprite(100, 250, 350, 100, WALL_TEXTURE, 90))
barriers.add(GameSprite(550, 250, 350, 100, WALL_TEXTURE, 90))
barriers.add(GameSprite(350, -200, 100, 350, WALL_TEXTURE))

finish = False
final_sprite = GameSprite(700, 600, 100, 100, FINAL_SPRITE_TEXTURE)

player = Player(PLAYER_START_X, PLAYER_START_Y, 80, 74, PLAYER_TEXTURE)

enemies = sprite.Group()
enemies.add(Enemy(0 + 1, 350, 0, 270, 350, 350, 80, 74, 5))
enemies.add(Enemy(270, 0 + 1, 270, 270, 0, 175, 80, 74, 5, 4))
enemies.add(Enemy(450, 175 - 1, 450, 450, 0, 175, 80, 74, 5, 4))

bullets = sprite.Group()

boss = Boss()

debug_message("Start!")
if not COLLISION: debug_message("Collision is disabled!", "Warning")

bullets_cooldown = 0

run = True
while run:
    for event in pygame.event.get():
        if event.type == QUIT:
            run = False
            debug_message("Quit!")
        elif (event.type == MOUSEBUTTONDOWN and event.button == 1) or (event.type == KEYDOWN and event.key == K_SPACE):
            player.strike()
            debug_message("Strike!", "Player")
        elif event.type == KEYDOWN:
            debug_message("KEYDOWN", "Controls")
            if event.key == K_UP or event.key == K_w:
                player.add_y_speed(-PLAYER_SPEED)
                debug_message("KEYDOWN UP", "Controls")
            elif event.key == K_DOWN or event.key == K_s:
                player.add_y_speed(PLAYER_SPEED)
                debug_message("KEYDOWN DOWN", "Controls")
            elif event.key == K_LEFT or event.key == K_a:
                player.add_x_speed(-PLAYER_SPEED)
                debug_message("KEYDOWN LEFT", "Controls")
            elif event.key == K_RIGHT or event.key == K_d:
                player.add_x_speed(PLAYER_SPEED)
                debug_message("KEYDOWN RIGHT", "Controls")
            
        elif event.type == KEYUP:
            debug_message("KEYUP", "Controls")
            if event.key == K_UP or event.key == K_w:
                player.stop_y()
                debug_message("KEYUP UP", "Controls")
            elif event.key == K_DOWN or event.key == K_s:
                player.stop_y()
                debug_message("KEYUP DOWN", "Controls")
            elif event.key == K_LEFT or event.key == K_a:
                player.stop_x()
                debug_message("KEYUP LEFT", "Controls")
            elif event.key == K_RIGHT or event.key == K_d:
                player.stop_x()
                debug_message("KEYUP RIGHT", "Controls")
    
    if not finish:
        if (bullets_cooldown >= 1):
            player.can_strike = False
            bullets_cooldown -= 1
        else:
            player.can_strike = True
        
        move_sprites(player, enemies, boss, bullets)
        render(BG, barriers, player, final_sprite, enemies, boss, bullets)

        if sprite.collide_rect(player, final_sprite):
            if player.rect.center > final_sprite.rect.topleft:
                finish = True
                win_screen(window)
                debug_message("Win!")

        if ENEMY_COLLISION:
            if sprite.spritecollide(player, enemies, False):
                finish = True
                lose_screen(window)
                debug_message("Collided with enemy! Lose!")
            if sprite.collide_rect(player, boss):
                finish = True
                lose_screen(window)
                debug_message("Collided with boss! Lose!")
            
    
    time.delay(50)
    display.update()
