import keyboard
import time

try:
    keyboard.block_key('alt')
    print("Success")
    keyboard.unblock_key('alt')
except Exception as e:
    print(f"Failed: {e}")
