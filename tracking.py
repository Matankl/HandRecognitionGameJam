"""
MediaPipe hand-tracking utilities.
Grabbing, detection and small helper functions live here so sprites stay clean.
"""

from __future__ import annotations
import cv2, mediapipe as mp, pygame
from pygame import Vector2

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False, max_num_hands=2, model_complexity=0,
    min_detection_confidence=0.8, min_tracking_confidence=0.5,
)

# ────────────────────────────────
# Frame capture
# ────────────────────────────────
def grab_frame(cam, w: int, h: int):
    ok, frame = cam.read()
    if not ok:
        return None, None
    frame = cv2.flip(frame, 1)            # mirror left/right
    frame = cv2.resize(frame, (w, h))
    frame = cv2.GaussianBlur(frame, (41, 41), sigmaX=0)
    return frame, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

# ────────────────────────────────
# Landmark helpers
# ────────────────────────────────
def hand_is_open(hand_lms) -> bool:
    """True if index--pinkie fingertips are above their PIP joints (thumb ignored)."""
    tips = [mp_hands.HandLandmark.INDEX_FINGER_TIP,
            mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
            mp_hands.HandLandmark.RING_FINGER_TIP,
            mp_hands.HandLandmark.PINKY_TIP]
    pips = [mp_hands.HandLandmark.INDEX_FINGER_PIP,
            mp_hands.HandLandmark.MIDDLE_FINGER_PIP,
            mp_hands.HandLandmark.RING_FINGER_PIP,
            mp_hands.HandLandmark.PINKY_PIP]
    return all(hand_lms.landmark[t].y < hand_lms.landmark[p].y for t, p in zip(tips, pips))

def center_px(hand_lms, w: int, h: int) -> Vector2:
    """Return the pixel-coords centre of all 21 landmarks."""
    cx = sum(lm.x for lm in hand_lms.landmark) / 21 * w
    cy = sum(lm.y for lm in hand_lms.landmark) / 21 * h
    return Vector2(cx, cy)

# ────────────────────────────────
# Convenience wrapper
# ────────────────────────────────
def detect_hands(frame_rgb):
    """Return (left_hand_lms, right_hand_lms) or (None, None)."""
    left = right = None
    results = hands.process(frame_rgb)
    if results.multi_hand_landmarks and results.multi_handedness:
        for lms, handedness in zip(results.multi_hand_landmarks,
                                   results.multi_handedness):
            if handedness.classification[0].label == "Left":
                left = lms
            else:
                right = lms
    return left, right
