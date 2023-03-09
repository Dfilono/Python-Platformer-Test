import pygame as pg
import os
import random
import math
from os import listdir
from os.path import isfile, join

pg.init()

pg.display.set_caption("Platformer")

# Global variables
WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5

# Set up window
window = pg.display.set_mode((WIDTH, HEIGHT))

def flip(sprites):
    return [pg.transform.flip(sprite, True, False) for sprite in sprites]

def load_sheets(dir1, dir2, w, h, direction = False):
    path = join("assets", dir1, dir2)
    imgs = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for img in imgs:
        sheet = pg.image.load(join(path, img)).convert_alpha()
        sprites = []

        for i in range(sheet.get_width() // w):
            surface = pg.Surface((w, h), pg.SRCALPHA, 32)
            rect = pg.Rect(i * w, 0, w, h)
            surface.blit(sheet, (0, 0), rect)
            sprites.append(pg.transform.scale2x(surface))

        if direction:
            all_sprites[img.replace(".png", "") + "_right"] = sprites
            all_sprites[img.replace(".png", "") + "_left"] = flip(sprites)

        else:
            all_sprites[img.replace('.png', '')] = sprites

    return all_sprites

def load_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    img = pg.image.load(path).convert_alpha()
    surface = pg.Surface((size, size), pg.SRCALPHA, 32)
    rect = pg.Rect(96, 0, size, size) # Change 96, 0 coords to choose a differnt terrain img, size is dimension of block
    surface.blit(img, (0, 0), rect)

    return pg.transform.scale2x(surface)

class Player(pg.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sheets("MainCharacters", "NinjaFrog", 32, 32, True)
    ANIM_DELAY = 3
    
    def __init__(self, x, y, w, h):
        super().__init__()
        self.rect = pg.Rect(x, y, w, h)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1

        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True
        self.hit_count = 0

    def move_left(self, vel):
        self.x_vel = -vel

        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel

        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sheet = "idle"

        if self.hit:
            sheet = "hit"

        elif self.y_vel < 0:
            if self.jump_count == 1:
                sheer = "jump"
            elif self.jump_count == 2:
                sheet = "double_jump"

        elif self.y_vel > self.GRAVITY * 2:
            sheet = "fall"

        elif self.x_vel != 0:
            sheet = "run"

        sheet_name = sheet + "_" + self.direction
        sprites = self.SPRITES[sheet_name]
        sprite_idx = (self.animation_count // self.ANIM_DELAY) % len(sprites)
        self.sprite = sprites[sprite_idx]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft = (self.rect.x, self.rect.y))
        self.mask = pg.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

class Object(pg.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pg.Rect(x, y, width, height)
        self.image = pg.Surface((width, height), pg.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = load_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pg.mask.from_surface(self.image)

class Fire(Object):
    ANIM_DELAY = 3
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, "fire")
        self.fire = load_sheets("Traps", "Fire", w, h)
        self.image = self.fire["off"][0]
        self.mask = pg.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_idx = (self.animation_count // self.ANIM_DELAY) % len(sprites)
        self.image = sprites[sprite_idx]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft = (self.rect.x, self.rect.y))
        self.mask = pg.mask.from_surface(self.image)

        if self.animation_count // self.ANIM_DELAY > len(sprites):
            self.animation_count = 0



def get_bg(name):
    img = pg.image.load(join("assets", "Background", name))
    _, _, width, height = img.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, img

def draw(window, bg, bg_img, player, objs, offset_x):
    for tile in bg:
        window.blit(bg_img, tile)

    for obj in objs:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    pg.display.update()

def handle_vertical_collision(player, objs, dy):
    collided_objs = []

    for obj in objs:
        if pg.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objs.append(obj)

    return collided_objs

def collide(player, objs, dx):
    player.move(dx, 0)
    player.update()
    collided_objs = None

    for obj in objs:
        if pg.sprite.collide_mask(player, obj):
            collided_objs = obj
            break
    
    player.move(-dx, 0)
    player.update()
    
    return collided_objs


def player_move(player, objs):
    key = pg.key.get_pressed()
    player.x_vel = 0
    collide_left = collide(player, objs, -PLAYER_VEL * 2)
    collide_right = collide(player, objs, PLAYER_VEL * 2)

    if (key[pg.K_a] or key[pg.K_LEFT]) and not collide_left:
        player.move_left(PLAYER_VEL)

    if (key[pg.K_d] or key[pg.K_RIGHT]) and not collide_right:
        player.move_right(PLAYER_VEL)

    verticle_collide = handle_vertical_collision(player, objs, player.y_vel)
    to_check = [collide_left, collide_right, *verticle_collide]

    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()

def main(window):
    clock = pg.time.Clock()
    bg, bg_img = get_bg("Green.png")
    block_size = 96

    player = Player(100, 100, 50, 50)
    fire = Fire(100, HEIGHT - block_size - 64, 16, 32)
    fire.on()
    floor = [Block(i * block_size, HEIGHT - block_size, block_size) for i in range(-WIDTH // block_size, WIDTH * 2 // block_size)]
    objs = [*floor, Block(0, HEIGHT - block_size * 2, block_size), 
            Block(block_size * 3, HEIGHT - block_size * 4, block_size), fire]
    
    offset_x = 0
    scroll_area_width = 200

    run = True

    while run:
        clock.tick(FPS)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                run = False
                break
            
            if event.type == pg.KEYDOWN:
                if event.key == (pg.K_SPACE or pg.K_UP or pg.K_w) and player.jump_count < 2:
                    player.jump()
        
        player.loop(FPS)
        fire.loop()
        player_move(player, objs)
        draw(window, bg, bg_img, player, objs, offset_x)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

    pg.quit()
    quit()



if __name__ == '__main__':
    main(window)