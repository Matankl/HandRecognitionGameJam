"""
Red pixel-bullet fired by the spaceship.
"""

import pygame
class Bullet(pygame.sprite.Sprite):
    SPEED = 14

    def __init__(self, pos: pygame.Vector2, direction: pygame.Vector2):
        super().__init__()
        self.image = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 0, 0), (3, 3), 3)

        self.rect = self.image.get_rect(center=pos)
        self.vel = direction.normalize() * self.SPEED if direction.length_squared() > .1 \
                   else pygame.Vector2(0, -self.SPEED)

    def update(self):
        self.rect.center += self.vel
        if not pygame.display.get_surface().get_rect().colliderect(self.rect):
            self.kill()
