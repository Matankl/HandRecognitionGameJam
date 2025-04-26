"""
Spawns at screen edges, drifts & rotates toward screen centre.
"""

from __future__ import annotations
import random, pygame

class Asteroid(pygame.sprite.Sprite):
    MIN_SPEED, MAX_SPEED = 2, 4

    def __init__(self, img: pygame.Surface, screen_w: int, screen_h: int):
        super().__init__()
        self.original_image = self.image = img
        self.screen_rect = pygame.Rect(0, 0, screen_w, screen_h)

        # Random spawn edge
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":
            pos = (random.randint(0, screen_w), -40)
        elif side == "bottom":
            pos = (random.randint(0, screen_w), screen_h + 40)
        elif side == "left":
            pos = (-40, random.randint(0, screen_h))
        else:  # right
            pos = (screen_w + 40, random.randint(0, screen_h))

        self.rect = self.image.get_rect(center=pos)
        self.mask = pygame.mask.from_surface(self.image)


        # Drift toward rough centre
        target = (screen_w // 2 + random.randint(-100, 100),
                  screen_h // 2 + random.randint(-100, 100))
        direction = pygame.Vector2(target) - pygame.Vector2(pos)
        self.velocity = direction.normalize() * random.uniform(self.MIN_SPEED, self.MAX_SPEED)

        # Spin
        self.angle = 0
        self.rotation_speed = random.uniform(-2.0, 2.0)

    def update(self):
        # Move & spin
        self.rect.center += self.velocity
        self.angle = (self.angle + self.rotation_speed) % 360
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)

        # Despawn when far off-screen
        if not self.screen_rect.inflate(100, 100).colliderect(self.rect):
            self.kill()
