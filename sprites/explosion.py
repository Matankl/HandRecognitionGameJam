"""
Explosion sprite: appears when an asteroid is destroyed.
It keeps moving with the asteroid's last velocity and disappears after a short time.
"""

import pygame

class Explosion(pygame.sprite.Sprite):
    DURATION = 300  # milliseconds to stay visible

    def __init__(self, pos, image: pygame.Surface, velocity: pygame.Vector2, rotation_speed: float):
        super().__init__()
        self.original_image = image
        self.image = image.copy()
        self.rect = self.image.get_rect(center=pos)
        self.velocity = velocity
        self.spawn_time = pygame.time.get_ticks()
        self.angle = 0
        self.rotation_speed = rotation_speed

    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time

        # Move the explosion in the same direction
        self.rect.centerx += int(self.velocity.x)
        self.rect.centery += int(self.velocity.y)

        # Rotate
        self.angle = (self.angle + self.rotation_speed) % 360
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

        # Fade out
        if elapsed < self.DURATION:
            alpha = 255 * (1 - elapsed / self.DURATION)  # from 255 → 0
            self.image.set_alpha(int(alpha))
        else:
            self.kill()