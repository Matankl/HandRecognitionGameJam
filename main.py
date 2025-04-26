
"""
Game entry-point: sets up Pygame, camera and main loop.
"""

from __future__ import annotations
import sys, cv2
import pygame
from pygame import Vector2
from pathlib import Path
from sprites import Explosion
# import asyncio

from helpers  import load_images_from_folder, scale_random, parallax_offset, webcam_surface_with_alpha, draw_mask
from tracking import grab_frame, detect_hands
from sprites  import Spaceship   # Bullet is created internally by Spaceship
from waveManager import WaveManager
from menu_scene import MenuScene



# ───────────────────────────────────────────────
# Config / paths
# ───────────────────────────────────────────────
WIDTH, HEIGHT = 750, 750
BG_ZOOM = 1.1
DEBUG = False


ASSETS = Path("assets")
SHIP_FOLDER = ASSETS / "Engine"
ASTEROID_FOLDER = ASSETS / "asteroid"
BG0 = ASSETS / "backgrounds/Background layer 0.png"
BG1 = ASSETS / "backgrounds/Background Layer 1.png"
BG2 = ASSETS / "backgrounds/Background Layer 2.png"
LOGO = ASSETS / "logo.png"

# Menu backgrounds (4 layers)
menu_bg_1 = pygame.image.load("assets/menu/Title Layer 0.png")
menu_bg_2 = pygame.image.load("assets/menu/Title Layer 1.png")
menu_bg_3 = pygame.image.load("assets/menu/Title Layer 2.png")
menu_bg_4 = pygame.image.load("assets/menu/Title Layer 3.png")
# Scale
menu_bg_1 = pygame.transform.scale(menu_bg_1, (WIDTH, HEIGHT))
menu_bg_2 = pygame.transform.scale(menu_bg_2, (WIDTH, HEIGHT))
menu_bg_3 = pygame.transform.scale(menu_bg_3, (WIDTH, HEIGHT))
menu_bg_4 = pygame.transform.scale(menu_bg_4, (WIDTH, HEIGHT))



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
explosion_base_img = pygame.image.load("assets/effects/Explode.png").convert_alpha()


# ───────────────────────────────────────────────
# Sprite groups
# ───────────────────────────────────────────────
all_sprites = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
asteroid_group = pygame.sprite.Group()

ship = Spaceship((WIDTH//2, HEIGHT-80), ship_images, bullet_group)
menu = MenuScene((WIDTH, HEIGHT), ASSETS/"menu")
all_sprites.add(ship)
all_sprites.add(bullet_group)
all_sprites.add(asteroid_group)

# # Periodic asteroid spawn
# ASTEROID_EVENT = pygame.USEREVENT + 1
# pygame.time.set_timer(ASTEROID_EVENT, 1200)

# Wave logic ---------------------------------------------------
wave_mgr = WaveManager(asteroid_group, all_sprites,WIDTH, HEIGHT, ASTEROID_FOLDER)
wave_mgr.start_game()      # start in MENU state

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

        # WaveManager may consume its private SPAWN_EVT
        if wave_mgr.handle_event(ev):
            continue

        if ev.type == pygame.QUIT:
            running = False

        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_SPACE:  # start first wave from menu
                wave_mgr.launch_if_menu()
            elif ev.key == pygame.K_r:  # restart after game-over
                wave_mgr.restart_if_gameover()

    # Camera & hand detection ---------------------------------
    frame_bgr, frame_rgb = grab_frame(cam, WIDTH, HEIGHT)
    left_hand, right_hand = detect_hands(frame_rgb) if frame_rgb is not None else (None, None)

    # Control ship --------------------------------------------
    ship.move(left_hand, WIDTH, HEIGHT)
    ship.shoot(right_hand, WIDTH, HEIGHT)

    # Menu hand-based start -----------------------------------
    if wave_mgr.state == "MENU":
        CIRCLE1_POS = Vector2(WIDTH // 3, HEIGHT // 2)
        CIRCLE2_POS = Vector2(2 * WIDTH // 3, HEIGHT // 2)
        CIRCLE_RADIUS = 80  # adjust based on your design

        if left_hand and right_hand:
            from tracking import center_px, hand_is_open

            left_pos = center_px(left_hand, WIDTH, HEIGHT)
            right_pos = center_px(right_hand, WIDTH, HEIGHT)

            if (hand_is_open(left_hand) and hand_is_open(right_hand) and
                    (left_pos - CIRCLE1_POS).length() < CIRCLE_RADIUS and
                    (right_pos - CIRCLE2_POS).length() < CIRCLE_RADIUS):
                wave_mgr.launch_if_menu()

        # Debug: draw the target circles
        if DEBUG:
            pygame.draw.circle(screen, (0, 255, 0), CIRCLE1_POS, CIRCLE_RADIUS, 3)
            pygame.draw.circle(screen, (0, 255, 0), CIRCLE2_POS, CIRCLE_RADIUS, 3)
            # if left_hand:
            #     pygame.draw.circle(screen, (255, 0, 0), (int(left_pos.x), int(left_pos.y)), 10)
            # if right_hand:
            #     pygame.draw.circle(screen, (255, 0, 0), (int(right_pos.x), int(right_pos.y)), 10)

    # Update sprites ------------------------------------------
    all_sprites.update()
    bullet_group.update()
    wave_mgr.update(player_alive=ship.health > 0)

    # Collisions ----------------------------------------------
    if pygame.sprite.spritecollide(ship, asteroid_group, dokill=True, collided=pygame.sprite.collide_mask):
        ship.hit()

    destroyed = pygame.sprite.groupcollide(
        asteroid_group,
        bullet_group,
        True, True,
        collided=pygame.sprite.collide_mask
    )

    for asteroid in destroyed.keys():
        # Use the asteroid's existing image and velocity
        explosion_img = pygame.transform.scale(explosion_base_img, asteroid.rect.size)
        explosion = Explosion(
            pos=asteroid.rect.center,
            image=explosion_img,
            velocity=asteroid.velocity,
            rotation_speed=asteroid.rotation_speed  # keep asteroid's spin
        )
        all_sprites.add(explosion)

    ship.score += len(destroyed)

    # Draw -----------------------------------------------------
    if frame_bgr is not None:
        screen.blit(bg0, parallax_offset(Vector2(ship.rect.center), .02, bg0.get_size(), WIDTH, HEIGHT))
        screen.blit(bg1, parallax_offset(Vector2(ship.rect.center), .06, bg1.get_size(), WIDTH, HEIGHT))
        screen.blit(bg2, parallax_offset(Vector2(ship.rect.center), .10, bg2.get_size(), WIDTH, HEIGHT))
        screen.blit(webcam_surface_with_alpha(frame_bgr, 35), (0, 0))
    else:
        screen.fill((10, 10, 30))

    # Draw all sprites
    all_sprites.draw(screen)
    bullet_group.draw(screen)

    # Debug: draw bounding boxes and masks
    if DEBUG:
        draw_mask(screen, ship.mask, ship.rect.topleft)
        for asteroid in asteroid_group:
            draw_mask(screen, asteroid.mask, asteroid.rect.topleft)
        for sprite in all_sprites:
            pygame.draw.rect(screen, (255, 0, 0), sprite.rect, 2)
        for bullet in bullet_group:
            bullet.draw_debug(screen)

    hud = pygame.font.SysFont(None, 28).render(
        f'Health: {ship.health}   Score: {ship.score}', True, (255,255,255))
    screen.blit(hud, (10, 10))

    # if wave_mgr.state == "MENU" and wave_mgr.wave == 0:  # first time only
    #     menu.reset()

    # Game Instructions (only on MENU screen)
    if wave_mgr.state == "MENU":
        menu.update()
        menu.draw(screen, frame_bgr=frame_bgr)

    # Wave / cooldown text
    status = wave_mgr.hud_text()
    if status:
        txt = pygame.font.SysFont(None, 36).render(status, True, (255, 255, 0))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 40))

    pygame.display.flip()
    clock.tick(60)

    if wave_mgr.state == "GAME_OVER" and not running:
        break  # optional; you can also let the player restart

# Clean-up ----------------------------------------------------
cam.release()
pygame.quit()
sys.exit()

