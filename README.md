# Hand-Controlled Space Shooter 🚀🖐️

A Pygame project where you control a spaceship **with your hands** using a webcam!  
Move your ship with your left hand and shoot by opening your right hand.

---

## 📂 Project Structure

```
your_project/
├── assets/
│   ├──   ...      
├── sprites/
│   ├── __init__.py
│   ├── asteroid.py
│   ├── bullet.py
│   ├── explosion.py
│   └── spaceship.py
├── helpers.py
├── main.py
├── menu_scene.py
├── tracking.py
├── waveManager.py
└── requirements.txt    # (see below)
```

---

## 🖥️ Requirements

Install Python 3.11 or later.

You need the following Python libraries:

- pygame
- opencv-python
- mediapipe

Install them all at once by running:

```bash
pip install -r requirements.txt
```


## 🎮 How to Play

1. Make sure your **webcam is connected** and working.
2. Open a terminal or command prompt in the project folder.
3. Run:

```bash
python main.py
```

4. When the **menu** appears:
   - Place your **left and right hands** on the green circles to start the game!

5. In-game:
   - **Move** your left hand to steer the ship.
   - **Open your right hand** to **shoot**.

6. If you lose all health, press **R** to restart!

---

## 📸 Webcam Permissions

When launching for the first time, your system may ask for webcam permissions.  
Make sure to allow it, otherwise the game won't detect your hands.

---

## 📋 Notes

- **Assets** (`/assets` folder) must be placed correctly, otherwise images won't load!
- If you get an error about missing DLLs (MediaPipe-related), make sure you installed everything via `pip install -r requirements.txt`.
- Tested on Windows 10 and Python 3.11.

---

Enjoy flying through space with your hands! 🚀🖐️
