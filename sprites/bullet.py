# """
# Red pixel-bullet fired by the spaceship.
# """
#
# import pygame
# class Bullet(pygame.sprite.Sprite):
#     SPEED = 14
#
#     def __init__(self, pos: pygame.Vector2, direction: pygame.Vector2):
#         super().__init__()
#         self.image = pygame.Surface((6, 6), pygame.SRCALPHA)
#         pygame.draw.circle(self.image, (255, 200, 0), (3, 3), 3)
#
#         self.rect = self.image.get_rect(center=pos)
#         self.vel = direction.normalize() * self.SPEED if direction.length_squared() > .1 \
#                    else pygame.Vector2(0, -self.SPEED)
#
#     def update(self):
#         self.rect.center += self.vel
#         if not pygame.display.get_surface().get_rect().colliderect(self.rect):
#             self.kill()


# Bullet sprite: rotating "package" projectile
from __future__ import annotations
import os, pygame
from pygame import Vector2

class Bullet(pygame.sprite.Sprite):
    """A parcel‑shaped bullet that slowly spins while travelling."""

    SPEED = 14       # pixels per frame
    ROT_SPEED = 6    # degrees per frame
    _original_img: pygame.Surface | None = None

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    @classmethod
    def _load_image(cls) -> pygame.Surface:
        """Load and cache the package sprite (scaled once for all bullets)."""
        if cls._original_img is None:
            path = os.path.join("assets/effects", "package.png")        # <- put your sprite here
            img = pygame.image.load(path).convert_alpha()
            cls._original_img = pygame.transform.smoothscale(img, (24, 24))
        return cls._original_img

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    def __init__(self, pos: Vector2, direction: Vector2):
        super().__init__()
        self.base_image = self._load_image()
        self.image = self.base_image
        self.rect = self.image.get_rect(center=pos)
        self.angle = 0

        # Velocity
        self.vel = (direction.normalize() * self.SPEED
                    if direction.length_squared() > 0.1 else Vector2(0, -self.SPEED))

    # ––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    def update(self):
        # Move
        self.rect.center += self.vel

        # Rotate sprite around its centre
        self.angle = (self.angle + self.ROT_SPEED) % 360
        self.image = pygame.transform.rotate(self.base_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

        # Auto‑despawn when off‑screen
        if not pygame.display.get_surface().get_rect().colliderect(self.rect):
            self.kill()
