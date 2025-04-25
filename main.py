"""
Hand-Controlled Space-Shooter
─────────────────────────────
• Move the ship with your *left* hand (palm centre)
• Fire with your *right* hand (open palm → bullet launched toward index tip)
"""

import random
import sys
import cv2
import mediapipe as mp
import pygame
import numpy as np
import os

# ─────────────────────────────────────────────
# ───────────  General helpers  ───────────────
# ─────────────────────────────────────────────

def load_images_from_folder(folder_path: str, scale=None) -> list[pygame.Surface]:
    """
    Loads all image files from the given folder and returns them as a list of pygame.Surface.
    Optionally scales each image to the specified (width, height).
    """
    supported_extensions = ('.png', '.jpg', '.jpeg')
    images = []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(supported_extensions):
            full_path = os.path.join(folder_path, filename)
            img = pygame.image.load(full_path).convert_alpha()
            if scale:
                img = pygame.transform.scale(img, scale)
            images.append(img)

    if not images:
        raise FileNotFoundError(f"No images found in folder: {folder_path}")

    return images


def scale_random(img: pygame.Surface,
                 min_size: tuple[int, int] = (40, 100),
                 max_size: tuple[int, int] = (100, 100)) -> pygame.Surface:
    """
    Scales the image to a random size between min_size and max_size.

    Args:
        img: The original image surface.
        min_size: Minimum (width, height).
        max_size: Maximum (width, height).

    Returns:
        A new scaled pygame.Surface.
    """
    target_w = random.randint(min_size[0], max_size[0])
    target_h = target_w
    return pygame.transform.scale(img, (target_w, target_h))


# ──────────────────────────────────────────────────────────────────
# ───────────  Camera: MediaPipe and OpenCV helpers  ───────────────
# ──────────────────────────────────────────────────────────────────

def parallax_offset(ship_pos: pygame.Vector2, factor: float, bg_size: tuple[int, int], WIDTH=800, HEIGHT=600) -> tuple[int, int]:
    bg_w, bg_h = bg_size

    # Distance ship is from center
    dx = ship_pos.x - WIDTH / 2
    dy = ship_pos.y - HEIGHT / 2

    # Offset from center position
    move_x = -int(dx * factor)
    move_y = -int(dy * factor)

    # Center the zoomed background
    center_x = -(bg_w - WIDTH) // 2
    center_y = -(bg_h - HEIGHT) // 2

    return center_x + move_x, center_y + move_y


def webcam_surface_with_alpha(frame_bgr, alpha_val=50):
    """Convert OpenCV BGR image to a semi-transparent Pygame surface."""
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

    h, w = frame_rgb.shape[:2]
    alpha_channel = np.full((h, w, 1), alpha_val, dtype=np.uint8)
    frame_rgba = np.concatenate((frame_rgb, alpha_channel), axis=2)

    # frombuffer expects bytes, not numpy array
    surface = pygame.image.frombuffer(frame_rgba.tobytes(), (w, h), "RGBA")
    return surface.convert_alpha()


mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    model_complexity=0,
    min_detection_confidence=0.8,
    min_tracking_confidence=0.5,
)


def hand_is_open(hand_lms) -> bool:
    """True when the 4 fingers (thumb ignored) are extended."""
    finger_tips = [
        mp_hands.HandLandmark.INDEX_FINGER_TIP,
        mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
        mp_hands.HandLandmark.RING_FINGER_TIP,
        mp_hands.HandLandmark.PINKY_TIP,
    ]
    finger_pips = [
        mp_hands.HandLandmark.INDEX_FINGER_PIP,
        mp_hands.HandLandmark.MIDDLE_FINGER_PIP,
        mp_hands.HandLandmark.RING_FINGER_PIP,
        mp_hands.HandLandmark.PINKY_PIP,
    ]
    return all(
        hand_lms.landmark[tip].y < hand_lms.landmark[pip].y
        for tip, pip in zip(finger_tips, finger_pips)
    )


def landmarks_center_px(hand_lms, w: int, h: int) -> pygame.Vector2:
    """Average all 21 landmarks; convert to pixel coords."""
    cx = sum(lm.x for lm in hand_lms.landmark) / 21 * w
    cy = sum(lm.y for lm in hand_lms.landmark) / 21 * h
    return pygame.Vector2(cx, cy)


# ───────────────────────────────────────────────
# ─────────────  Sprite classes  ────────────────
# ───────────────────────────────────────────────
class Bullet(pygame.sprite.Sprite):
    SPEED = 14

    def __init__(self, pos: pygame.Vector2, direction: pygame.Vector2):
        super().__init__()
        self.image = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 0, 0), (3, 3), 3)
        self.rect = self.image.get_rect(center=pos)

        if direction.length_squared() > 0.1:
            self.vel = direction.normalize() * self.SPEED
        else:
            self.vel = pygame.Vector2(0, -self.SPEED)  # fallback: shoot upward

    def update(self):
        self.rect.centerx += int(self.vel.x)
        self.rect.centery += int(self.vel.y)
        if not pygame.display.get_surface().get_rect().colliderect(self.rect):
            self.kill()


# class Asteroid(pygame.sprite.Sprite):
#     MIN_SPEED, MAX_SPEED = 1, 6
#
#     def __init__(self, img, screen_w):
#         super().__init__()
#         self.image = img
#         self.rect = self.image.get_rect(
#             center=(random.randint(24, screen_w - 24), -24)
#         )
#         self.speed = random.randint(self.MIN_SPEED, self.MAX_SPEED)
#
#     def update(self):
#         self.rect.centery += self.speed
#         if self.rect.top > pygame.display.get_surface().get_height() + 50:
#             self.kill()

class Asteroid(pygame.sprite.Sprite):
    MIN_SPEED, MAX_SPEED = 2, 4

    def __init__(self, img, screen_w, screen_h):
        super().__init__()
        self.image = img
        self.original_image = img  # Keep original for clean rotation
        self.screen_rect = pygame.Rect(0, 0, screen_w, screen_h)

        # Choose a random spawn side
        side = random.choice(['top', 'bottom', 'left', 'right'])

        if side == 'top':
            x = random.randint(0, screen_w)
            y = -40
        elif side == 'bottom':
            x = random.randint(0, screen_w)
            y = screen_h + 40
        elif side == 'left':
            x = -40
            y = random.randint(0, screen_h)
        else:  # right
            x = screen_w + 40
            y = random.randint(0, screen_h)

        self.rect = self.image.get_rect(center=(x, y))

        # Pick a target point near the middle but with a little randomness
        target_x = screen_w // 2 + random.randint(-100, 100)
        target_y = screen_h // 2 + random.randint(-100, 100)
        direction = pygame.Vector2(target_x - x, target_y - y)
        self.velocity = direction.normalize() * random.uniform(self.MIN_SPEED, self.MAX_SPEED)

        # ─ Rotation ─
        self.angle = 0
        self.rotation_speed = random.uniform(-2.0, 2.0)  # degrees per frame

    def update(self):
        # Movement
        self.rect.centerx += self.velocity.x
        self.rect.centery += self.velocity.y

        # Rotation
        self.angle = (self.angle + self.rotation_speed) % 360
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)  # keep center consistent

        # Cleanup if too far off screen
        if not self.screen_rect.inflate(100, 100).colliderect(self.rect):
            self.kill()






class Spaceship(pygame.sprite.Sprite):
    BULLET_COOLDOWN = 1000  # ms
    INVINCIBLE_MS = 2000    # ms

    def __init__(self, pos, ship_img, bullet_group):
        super().__init__()
        self.image = ship_img
        self.rect = self.image.get_rect(center=pos)
        self.bullets = bullet_group
        self.health = 5
        self.score = 0
        self._last_shot_ms = 0
        self._invincible_until = 0

    # ────────── Input hooks ──────────
    def move(self, left_hand_lms, w, h):
        if left_hand_lms:
            self.rect.center = landmarks_center_px(left_hand_lms, w, h)

    def shoot(self, right_hand_lms, w, h):
        t_now = pygame.time.get_ticks()
        if (
                right_hand_lms
                and hand_is_open(right_hand_lms)
                and t_now - self._last_shot_ms >= self.BULLET_COOLDOWN
        ):
            ship_pos = pygame.Vector2(self.rect.center)
            tip = right_hand_lms.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            target = pygame.Vector2(tip.x * w, tip.y * h)
            direction = target - ship_pos

            if direction.length_squared() > 1:  # prevents /0 bugs
                bullet = Bullet(ship_pos, direction)
                self.bullets.add(bullet)
                self._last_shot_ms = t_now

    # ────────── Gameplay helpers ─────
    @property
    def invincible(self):
        return pygame.time.get_ticks() < self._invincible_until

    def hit(self):
        if not self.invincible:
            self.health -= 1
            self._invincible_until = pygame.time.get_ticks() + self.INVINCIBLE_MS

    def update(self):
        # Keep on-screen
        self.rect.clamp_ip(pygame.display.get_surface().get_rect())
        # Flash while invincible
        if self.invincible and (pygame.time.get_ticks() // 100) % 2 == 0:
            self.image.set_alpha(80)
        else:
            self.image.set_alpha(255)


# ───────────────────────────────────────────────
# ───────────────────  main()  ───────────────────
# ───────────────────────────────────────────────
def main():
    # 1) Pygame --------
    pygame.init()
    WIDTH, HEIGHT = 800, 600
    # Zoom scale (e.g. 1.2 = 120% size)
    zoom_factor = 1.1
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Hand-Controlled Space-Shooter")
    icon = pygame.image.load("assets/logo.png")
    pygame.display.set_icon(icon)
    clock = pygame.time.Clock()

    # 2) Quick placeholder art (swap with PNGs!)
    # objects
    ship_img = pygame.Surface((60, 48), pygame.SRCALPHA)
    pygame.draw.polygon(ship_img, (0, 240, 0), [(30, 0), (0, 47), (60, 47)])

    asteroid_img = pygame.Surface((48, 48), pygame.SRCALPHA)
    pygame.draw.circle(asteroid_img, (100, 100, 100), (24, 24), 24)

    # backgrounds layers
    space_bg_0 = pygame.image.load("assets/backgrounds/Background layer 0.png").convert_alpha()
    space_bg_1 = pygame.image.load("assets/backgrounds/Background Layer 1.png").convert_alpha()
    space_bg_2 = pygame.image.load("assets/backgrounds/Background Layer 2.png").convert_alpha()

    # Optional: resize to fit screen
    space_bg_0 = pygame.transform.scale(space_bg_0, (int(WIDTH * zoom_factor), int(HEIGHT * zoom_factor)))
    space_bg_1 = pygame.transform.scale(space_bg_1, (int(WIDTH * zoom_factor), int(HEIGHT * zoom_factor)))
    space_bg_2 = pygame.transform.scale(space_bg_2, (int(WIDTH * zoom_factor), int(HEIGHT * zoom_factor)))


    # 3) Sprite groups & instances
    all_sprites = pygame.sprite.Group()
    bullet_group = pygame.sprite.Group()
    asteroid_group = pygame.sprite.Group()

    ship = Spaceship((WIDTH // 2, HEIGHT - 80), ship_img, bullet_group)
    all_sprites.add(ship)

    # 4) Timed asteroid spawns
    ASTEROID_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(ASTEROID_EVENT, 1200)

    # 5) Webcam
    cam = cv2.VideoCapture(0)

    def grab_frame():
        ok, frame = cam.read()
        if not ok:
            return None, None
        frame = cv2.flip(frame, 1)  # mirror for easier control
        frame = cv2.resize(frame, (WIDTH, HEIGHT))
        # Apply Gaussian blur
        frame = cv2.GaussianBlur(frame, (15, 15), sigmaX=0)
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame, img_rgb

    # 6) Main loop
    running = True
    while running:
        # ── Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == ASTEROID_EVENT:
                asteroid_images = load_images_from_folder("assets/asteroid")
                asteroid_img = random.choice(asteroid_images)
                asteroid_img = scale_random(asteroid_img)
                a = Asteroid(asteroid_img, WIDTH, HEIGHT)
                asteroid_group.add(a)
                all_sprites.add(a)

        # ── Webcam → hands
        frame_bgr, frame_rgb = grab_frame()
        left_hand = right_hand = None
        if frame_rgb is not None:
            results = hands.process(frame_rgb)
            if results.multi_hand_landmarks and results.multi_handedness:
                for lms, handed in zip(results.multi_hand_landmarks,
                                       results.multi_handedness):
                    if handed.classification[0].label == "Left":
                        left_hand = lms
                    else:
                        right_hand = lms

        # ── Controls & updates
        ship.move(left_hand, WIDTH, HEIGHT)
        ship.shoot(right_hand, WIDTH, HEIGHT)

        all_sprites.update()

        # ── Collisions
        if pygame.sprite.spritecollide(ship, asteroid_group, dokill=True):
            ship.hit()
        destroyed = pygame.sprite.groupcollide(
            asteroid_group, bullet_group, True, True
        )
        ship.score += len(destroyed)

        # ── Draw
        if frame_bgr is not None:
            # use camera feed as backdrop
            surf = pygame.surfarray.make_surface(
                cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB).swapaxes(0, 1)
            )

            # fog_alpha = (pygame.time.get_ticks() // 10) % 255
            # fog_layer.set_alpha(fog_alpha)

            ship_center = pygame.Vector2(ship.rect.center)

            # Parallax layers:
            bg_offset_0 = parallax_offset(pygame.Vector2(ship.rect.center), 0.02, space_bg_0.get_size())
            bg_offset_1 = parallax_offset(pygame.Vector2(ship.rect.center), 0.04, space_bg_1.get_size())
            bg_offset_2 = parallax_offset(pygame.Vector2(ship.rect.center), 0.06, space_bg_2.get_size())

            screen.blit(space_bg_0, bg_offset_0) # dark background
            screen.blit(space_bg_1, bg_offset_1) # mid background
            screen.blit(space_bg_2, bg_offset_2) # fog with alpha

            surf = webcam_surface_with_alpha(frame_bgr, alpha_val=25)
            screen.blit(surf, (0, 0))  # on top (also can be alpha-blended)
        else:
            screen.fill((10, 10, 30))

        all_sprites.draw(screen)
        bullet_group.draw(screen)
        bullet_group.update()

        font = pygame.font.SysFont(None, 28)
        hud = font.render(
            f"Health: {ship.health}   Score: {ship.score}",
            True,
            (255, 255, 255),
        )
        screen.blit(hud, (10, 10))

        pygame.display.flip()
        clock.tick(60)

        if ship.health <= 0:
            running = False

    # ── Cleanup
    cam.release()
    pygame.quit()
    sys.exit()


# ───────────────────────────────────────────────
# ──────────  standard entry-point  ─────────────
# ───────────────────────────────────────────────
if __name__ == "__main__":
    main()
