"""
MenuScene
─────────
• Draws four background layers with the requested behaviour:
    layer1 – static
    layer2 – slow ±5° rotation, fades out
    layer3 – shows first, fades out after delay
    layer4 – fades in after 2+3 are gone
• Shows instructions & handles SPACE (start) + R (restart after game-over).

Public API
──────────
    menu = MenuScene(screen_size, assets_path)
    menu.reset()                 # call when you re-enter the menu
    menu.handle_event(event)     # returns True if it consumed SPACE / R
    menu.update()                # per-frame book-keeping
    menu.draw(target_surface)    # draw everything
"""

from __future__ import annotations
import pygame, math, pathlib

class MenuScene:
    def __init__(self, size: tuple[int,int], menu_asset_dir: pathlib.Path):
        self.W, self.H = size
        # ─ load layers ─
        self.bg1 = pygame.transform.scale(pygame.image.load(menu_asset_dir/"Title Layer 0.png"), size)
        self.bg2 = pygame.transform.scale(pygame.image.load(menu_asset_dir/"Title Layer 1.png"), size)
        self.bg3 = pygame.transform.scale(pygame.image.load(menu_asset_dir/"Title Layer 2.png"), size)
        self.bg4 = pygame.transform.scale(pygame.image.load(menu_asset_dir/"Title Layer 3.png"), size)

        self.font = pygame.font.SysFont(None, 26)
        self.reset()

    # ---------------------------------------------------------
    # external API
    def reset(self):
        self.t0 = pygame.time.get_ticks()
        self.alpha2 = 255
        self.alpha3 = 255
        self.alpha4 = 0
        self.fade2 = self.fade3 = self.fade4 = False

    def handle_event(self, ev) -> bool:
        """Return True if SPACE/R was consumed (so main won’t treat it)."""
        if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_SPACE, pygame.K_r):
            return True
        return False

    def update(self):
        now_s = (pygame.time.get_ticks() - self.t0) / 1000

        #start fading after 2 s
        if now_s > 2 and not self.fade3:
            self.fade2 = self.fade3 = True

        #alpha step per frame (adjust for speed)
        step = 5
        if self.fade2 and self.alpha2 > 0:
            self.alpha2 = max(0, self.alpha2 - step)
        if self.fade3 and self.alpha3 > 0:
            self.alpha3 = max(0, self.alpha3 - step)
            if self.alpha3 == 0:
                self.fade4 = True
        if self.fade4 and self.alpha4 < 255:
            self.alpha4 = min(255, self.alpha4 + step)

    def draw(self, surf: pygame.Surface, frame_bgr=None):
        # 1 static
        surf.blit(self.bg1, (0,0))

        # 2 rotate, fade
        angle = 5 * math.sin(pygame.time.get_ticks()/3000)
        rotated = pygame.transform.rotozoom(self.bg2, angle, 1.0)
        r_rect  = rotated.get_rect(center=(self.W//2, self.H//2))
        rot_surf = rotated.copy(); rot_surf.set_alpha(self.alpha2)
        surf.blit(rot_surf, r_rect)

        # 3 fade-out
        layer3 = self.bg3.copy(); layer3.set_alpha(self.alpha3)
        surf.blit(layer3, (0,0))

        # Draw webcam when Layer 4 is starting
        if frame_bgr is not None and self.fade4:
            from helpers import webcam_surface_with_alpha
            # Map alpha4 (0-255) into desired webcam transparency
            webcam_alpha = int(self.alpha4 * 0.13)  # 60% maximum transparency
            cam_surface = webcam_surface_with_alpha(frame_bgr, alpha_val=webcam_alpha)
            surf.blit(cam_surface, (0, 0))

        # 4 fade-in last
        layer4 = self.bg4.copy(); layer4.set_alpha(self.alpha4)
        surf.blit(layer4, (0,0))



