import keyboard
import time

try:
    keyboard.add_hotkey('alt+tab', lambda: print("Blocked alt+tab"), suppress=True)
    keyboard.add_hotkey('windows', lambda: print("Blocked windows"), suppress=True)
    print("Testing blocks for 5 seconds...")
    for _ in range(5):
        time.sleep(1)
    keyboard.unhook_all()
    print("Done")
except Exception as e:
    print(f"Failed: {e}")
