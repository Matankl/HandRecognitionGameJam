"""
Player ship: moves with left hand; fires when right hand is open.
"""

from __future__ import annotations
import pygame, mediapipe as mp
from pygame import Vector2
from .bullet import Bullet
from tracking import hand_is_open, center_px   # re-use helpers

mp_hands = mp.solutions.hands

class Spaceship(pygame.sprite.Sprite):
    BULLET_COOLDOWN = 500        # ms
    INVINCIBLE_MS  = 1000
    ANIM_SPEED     = 100         # ms per frame


    def __init__(self, pos, images, bullet_group: pygame.sprite.Group):
        super().__init__()
        self.images = images
        self.image_index = 0
        self.image = self.images[0]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=pos)
        self._last_angle = 0  # store last rotation
        self._current_angle = 0  # For smooth interpolation
        self.ROTATE_SMOOTHNESS = 0.15  # Adjust this from 0.05 (slow) to 0.3 (fast)

        self.bullets = bullet_group
        self.health  = 5
        self.score   = 0

        self._last_shot   = 0
        self._invincible_until = 0
        self._last_anim   = 0
        self._last_pos    = Vector2(self.rect.center)  # for rotation hint

    # ────────────────────────────────
    # Properties
    # ────────────────────────────────
    @property
    def invincible(self) -> bool:
        return pygame.time.get_ticks() < self._invincible_until

    # ────────────────────────────────
    # Event handlers
    # ────────────────────────────────
    def hit(self):
        if not self.invincible:
            self.health -= 1
            self._invincible_until = pygame.time.get_ticks() + self.INVINCIBLE_MS

    def move(self, left_hand_lms, w, h):
        if left_hand_lms:
            self._last_pos = Vector2(self.rect.center)
            self.rect.center = center_px(left_hand_lms, w, h)

    def shoot(self, right_hand_lms, w, h):
        now = pygame.time.get_ticks()
        if (right_hand_lms and hand_is_open(right_hand_lms) and
                now - self._last_shot >= self.BULLET_COOLDOWN):

            tip = right_hand_lms.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            direction = Vector2(tip.x * w, tip.y * h) - Vector2(self.rect.center)
            if direction.length_squared() > 1:
                self.bullets.add(Bullet(Vector2(self.rect.center), direction))
                self._last_shot = now


    def update(self):
        self.rect.clamp_ip(pygame.display.get_surface().get_rect())
        now = pygame.time.get_ticks()

        # Animation
        if now - self._last_anim >= self.ANIM_SPEED:
            self.image_index = (self.image_index + 1) % len(self.images)
            self._last_anim = now

        current_frame = self.images[self.image_index]

        # Calculate movement direction
        move_vec = Vector2(self.rect.center) - self._last_pos
        if move_vec.length_squared() > 4:
            target_angle = move_vec.angle_to(Vector2(0, -1))  # up is 0°
            self._last_pos = Vector2(self.rect.center)
        else:
            target_angle = self._last_angle  # no big move → reuse

        # Smooth rotation
        # Wrap angle to avoid jumps when crossing -180° ↔ +180°
        diff = (target_angle - self._current_angle + 180) % 360 - 180
        self._current_angle += diff * self.ROTATE_SMOOTHNESS
        self._last_angle = target_angle

        # Rotate image
        self.image = pygame.transform.rotate(current_frame, self._current_angle)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)

        # Flash if invincible
        if self.invincible and (now // 100) % 2:
            self.image.set_alpha(80)
        else:
            self.image.set_alpha(255)
