
"""
Game entry-point: sets up Pygame, camera and main loop.
"""

from __future__ import annotations
import sys, random, pygame, cv2
import pygame
from pygame import Vector2
from pathlib import Path

from helpers  import load_images_from_folder, scale_random, parallax_offset, webcam_surface_with_alpha
from tracking import grab_frame, detect_hands
from sprites  import Spaceship, Asteroid   # Bullet is created internally by Spaceship


# ───────────────────────────────────────────────
# Config / paths
# ───────────────────────────────────────────────
WIDTH, HEIGHT = 800, 600
BG_ZOOM = 1.1
DEBUG = True

ASSETS = Path("assets")
SHIP_FOLDER = ASSETS / "Engine"
ASTEROID_FOLDER = ASSETS / "asteroid"
BG0 = ASSETS / "backgrounds/Background layer 0.png"
BG1 = ASSETS / "backgrounds/Background Layer 1.png"
BG2 = ASSETS / "backgrounds/Background Layer 2.png"
LOGO = ASSETS / "logo.png"

# ───────────────────────────────────────────────
# Pygame init
# ───────────────────────────────────────────────
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hand-Controlled Space-Shooter")
pygame.display.set_icon(pygame.image.load(LOGO))
clock = pygame.time.Clock()

# ───────────────────────────────────────────────
# Load graphics
# ───────────────────────────────────────────────
ship_images = load_images_from_folder(str(SHIP_FOLDER), scale=(40, 60))
bg0 = pygame.transform.scale(pygame.image.load(BG0), (int(WIDTH*BG_ZOOM), int(HEIGHT*BG_ZOOM))).convert_alpha()
bg1 = pygame.transform.scale(pygame.image.load(BG1), (int(WIDTH*BG_ZOOM), int(HEIGHT*BG_ZOOM))).convert_alpha()
bg2 = pygame.transform.scale(pygame.image.load(BG2), (int(WIDTH*BG_ZOOM), int(HEIGHT*BG_ZOOM))).convert_alpha()

# ───────────────────────────────────────────────
# Sprite groups
# ───────────────────────────────────────────────
all_sprites   = pygame.sprite.Group()
bullet_group  = pygame.sprite.Group()
asteroid_group= pygame.sprite.Group()

ship = Spaceship((WIDTH//2, HEIGHT-80), ship_images, bullet_group)
all_sprites.add(ship)
all_sprites.add(bullet_group)

# Periodic asteroid spawn
ASTEROID_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(ASTEROID_EVENT, 1200)

# ───────────────────────────────────────────────
# Webcam
# ───────────────────────────────────────────────
cam = cv2.VideoCapture(0)

# ───────────────────────────────────────────────
# Main loop
# ───────────────────────────────────────────────
running = True
while running:
    # Events ---------------------------------------------------
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False
        elif ev.type == ASTEROID_EVENT:
            img = scale_random(random.choice(load_images_from_folder(str(ASTEROID_FOLDER))))
            a = Asteroid(img, WIDTH, HEIGHT)
            asteroid_group.add(a); all_sprites.add(a)

    # Camera & hand detection ---------------------------------
    frame_bgr, frame_rgb = grab_frame(cam, WIDTH, HEIGHT)
    left_hand, right_hand = detect_hands(frame_rgb) if frame_rgb is not None else (None, None)

    # Control ship --------------------------------------------
    ship.move(left_hand, WIDTH, HEIGHT)
    ship.shoot(right_hand, WIDTH, HEIGHT)

    # Update sprites ------------------------------------------
    all_sprites.update()
    bullet_group.update()



    # Collisions ----------------------------------------------
    if pygame.sprite.spritecollide(ship, asteroid_group, dokill=True):
        ship.hit()
    destroyed = pygame.sprite.groupcollide(asteroid_group, bullet_group, True, True)
    ship.score += len(destroyed)

    # Draw -----------------------------------------------------
    if frame_bgr is not None:
        screen.blit(bg0, parallax_offset(Vector2(ship.rect.center), .02, bg0.get_size(), WIDTH, HEIGHT))
        screen.blit(bg1, parallax_offset(Vector2(ship.rect.center), .04, bg1.get_size(), WIDTH, HEIGHT))
        screen.blit(bg2, parallax_offset(Vector2(ship.rect.center), .06, bg2.get_size(), WIDTH, HEIGHT))
        screen.blit(webcam_surface_with_alpha(frame_bgr, 25), (0, 0))
    else:
        screen.fill((10, 10, 30))

    # Draw all sprites
    all_sprites.draw(screen)
    bullet_group.draw(screen)

    # Debug: draw bounding boxes
    if DEBUG:
        for s in all_sprites:
            pygame.draw.rect(screen, (255, 0, 0), s.rect, 1)
        for b in bullet_group:
            pygame.draw.rect(screen, (0, 255, 0), b.rect, 1)

    hud = pygame.font.SysFont(None, 28).render(
        f'Health: {ship.health}   Score: {ship.score}', True, (255,255,255))
    screen.blit(hud, (10, 10))

    pygame.display.flip()
    clock.tick(60)

    if ship.health <= 0:
        running = False

# Clean-up ----------------------------------------------------
cam.release()
pygame.quit()
sys.exit()

