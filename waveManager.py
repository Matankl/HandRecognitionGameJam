"""
WaveManager
───────────
Handles 4 simple game-states:

    MENU  →  WAVE  →  COOLDOWN  →  (back to WAVE) …  →  GAME_OVER

• Wave duration            = 10 s + wave⋅10 s
• Cool-down duration       = max(2 s, 8 s − (wave−1)⋅2 s)
• Asteroids this wave      = ⌊(wave⋅1.5) × wave_duration / 5⌋
  (they’re spawned evenly across the wave)

Call `.handle_event()` from your event-loop, `.update()` once per frame,
and `.hud_text()` to draw status text.
"""

from __future__ import annotations
import pygame, random, math
from pathlib import Path

from helpers import load_images_from_folder, scale_random
from sprites  import Asteroid


class WaveManager:
    SPAWN_EVT = pygame.USEREVENT + 99          # private event id

    def __init__(self,
        asteroid_group: pygame.sprite.Group,
        all_sprites: pygame.sprite.Group,
        screen_w: int, screen_h: int,
        asteroid_folder: Path):
        self.asteroid_group = asteroid_group
        self.all_sprites = all_sprites
        self.W, self.H = screen_w, screen_h
        self.asteroid_folder = asteroid_folder

        # ─ Runtime state ─
        self.wave = 0
        self.state = "MENU"               # MENU | WAVE | COOLDOWN | GAME_OVER
        self.ends_at_ms = 0               # pygame.time.get_ticks timestamp
        self.to_spawn = self.spawned = 0  # per-wave counters
        self.cooldown_ms = 8000

    # ──────────────────────────────────────────────────────────────
    # Public helpers
    # ──────────────────────────────────────────────────────────────
    def start_game(self):
        self.wave = 0
        self.state = "MENU"

    def handle_event(self, ev):
        """
        • From main event-loop.
        • Returns True if *ev* was consumed (asteroid spawn), so main-loop
          can just continue.
        """
        if ev.type == self.SPAWN_EVT and self.state == "WAVE":
            if self.spawned < self.to_spawn:
                self._spawn_asteroid()
            if self.spawned >= self.to_spawn:        # finished quota
                pygame.time.set_timer(self.SPAWN_EVT, 0)
            return True
        return False

    def update(self, player_alive: bool):
        """
        Call every frame. Handles state transitions.
        """
        now = pygame.time.get_ticks()

        if self.state == "MENU":
            return

        if not player_alive and self.state != "GAME_OVER":
            self.state = "GAME_OVER"
            pygame.time.set_timer(self.SPAWN_EVT, 0)
            return

        if self.state == "WAVE":
            if now >= self.ends_at_ms and not self.asteroid_group:
                self._start_cooldown()

        elif self.state == "COOLDOWN":
            if now >= self.ends_at_ms:
                self._start_wave()

    # ──────────────────────────────────────────────────────────────
    # HUD helper
    # ──────────────────────────────────────────────────────────────
    def hud_text(self) -> str:
        """Short string to overlay on screen."""
        now = pygame.time.get_ticks()
        if self.state == "MENU":
            return ""
        if self.state == "WAVE":
            remain = math.ceil(max(0, self.ends_at_ms - now) / 1000)
            return f"WAVE {self.wave}   {remain}s"
        if self.state == "COOLDOWN":
            remain = math.ceil(max(0, self.ends_at_ms - now) / 1000)
            return f"Cooldown… {remain}s"
        if self.state == "GAME_OVER":
            return "GAME OVER – press R to restart"
        return ""

    # ──────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────
    def _spawn_asteroid(self):
        img = scale_random(random.choice(load_images_from_folder(self.asteroid_folder)))
        a   = Asteroid(img, self.W, self.H)
        self.asteroid_group.add(a); self.all_sprites.add(a)
        self.spawned += 1

    # -------------------------------------------------------------
    def _start_wave(self):
        self.wave += 1
        wave_dur_ms = (10 + self.wave * 10) * 1000      # 10s + n*10s
        self.cooldown_ms = max(2000, 8000 - (self.wave - 1) * 2000)

        # asteroid quota
        self.to_spawn = int((self.wave * 1.5) * (wave_dur_ms / 1000) / 5)
        spawn_interval_ms = max(200, wave_dur_ms // max(1, self.to_spawn))

        pygame.time.set_timer(self.SPAWN_EVT, spawn_interval_ms)
        self.spawned = 0
        self.state = "WAVE"
        self.ends_at_ms = pygame.time.get_ticks() + wave_dur_ms
        print(f"Wave {self.wave}  —  {self.to_spawn} asteroids over {wave_dur_ms/1000:.0f}s "
              f"(spawn every {spawn_interval_ms} ms)")

    def _start_cooldown(self):
        pygame.time.set_timer(self.SPAWN_EVT, 0)
        self.state = "COOLDOWN"
        self.ends_at_ms = pygame.time.get_ticks() + self.cooldown_ms
        print(f"Cooldown {self.cooldown_ms/1000:.0f}s")

    # -------------------------------------------------------------
    # External triggers (menu keys)
    def launch_if_menu(self):
        if self.state == "MENU":
            self._start_wave()

    def restart_if_gameover(self):
        if self.state == "GAME_OVER":
            self.start_game()
