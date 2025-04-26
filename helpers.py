"""
General utility functions (image loading, parallax math, webcam → Pygame surface)
"""

from __future__ import annotations
import os, random, cv2, pygame, numpy as np
from pygame import Vector2

# ──────────────────────────────────────────────────────────────
# Image helpers
# ──────────────────────────────────────────────────────────────
def load_images_from_folder(folder_path: str, scale: tuple[int, int] | None = None) -> list[pygame.Surface]:
    """Load every .png/.jpg in *folder_path*; optionally scale them."""
    supported = ('.png', '.jpg', '.jpeg')
    images: list[pygame.Surface] = []

    for file in os.listdir(folder_path):
        if file.lower().endswith(supported):
            img = pygame.image.load(os.path.join(folder_path, file)).convert_alpha()
            if scale:
                img = pygame.transform.scale(img, scale)
            images.append(img)

    if not images:
        raise FileNotFoundError(f'No images found in “{folder_path}”.')
    return images


def scale_random(img: pygame.Surface,
                 min_size: tuple[int, int] = (40, 40),
                 max_size: tuple[int, int] = (100, 100)) -> pygame.Surface:
    """Return *img* randomly resized inside the given bounds (keeps square aspect)."""
    size = random.randint(min_size[0], max_size[0])
    return pygame.transform.scale(img, (size, size))

# ──────────────────────────────────────────────────────────────
# Parallax / camera helpers
# ──────────────────────────────────────────────────────────────
def parallax_offset(ship_pos: Vector2, factor: float,
                    bg_size: tuple[int, int], screen_w=800, screen_h=600) -> tuple[int, int]:
    """Compute where a background layer should be blitted for a parallax effect."""
    dx = ship_pos.x - screen_w / 2
    dy = ship_pos.y - screen_h / 2
    center_x = -(bg_size[0] - screen_w) // 2
    center_y = -(bg_size[1] - screen_h) // 2
    return center_x - int(dx * factor), center_y - int(dy * factor)

def webcam_surface_with_alpha(frame_bgr, alpha_val: int = 50) -> pygame.Surface:
    """Convert OpenCV BGR frame → semi-transparent Pygame surface."""
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    h, w = frame_rgb.shape[:2]
    alpha = np.full((h, w, 1), alpha_val, np.uint8)
    frame_rgba = np.concatenate((frame_rgb, alpha), axis=2)
    return pygame.image.frombuffer(frame_rgba.tobytes(), (w, h), "RGBA").convert_alpha()

def draw_mask(surface, mask, offset):
    for x in range(mask.get_size()[0]):
        for y in range(mask.get_size()[1]):
            if mask.get_at((x, y)):
                surface.set_at((x + offset[0], y + offset[1]), (0, 255, 0))  # green pixel
