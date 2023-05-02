import io
import os
import platform
import time
import pyautogui
# Windows 10 functions
import pyperclip
import keyboard
from PIL import ImageGrab
import win32clipboard
import win32con

# macOS functions
def escape_applescript_string(s):
    return s.replace('"', '\\"').replace("'", "\\'")

def run_applescript(script):
    escaped_script = escape_applescript_string(script)
    os.system(f"osascript -e '{escaped_script}'")

def set_clipboard_macos(text):
    text = escape_applescript_string(text)
    run_applescript(f'set the clipboard to "{text}"')

def set_image_to_clipboard_macos(image):
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_data = buffer.getvalue()
    buffer.close()
    run_applescript(f'set the clipboard to (read (POSIX file "/dev/stdin") as JPEG picture) as «class PNGf»' + '«data PNGf' + img_data.hex() + '»')

def activate_wechat_and_send_message_macos(message=None, screenshot=None):
    if message:
        message = escape_applescript_string(message)
        set_clipboard_macos(message)
    elif screenshot:
        set_image_to_clipboard_macos(screenshot)

    run_applescript('activate application "WeChat"')
    run_applescript('delay 1')
    run_applescript('tell application "System Events" to keystroke "v" using command down')
    run_applescript('tell application "System Events" to keystroke return')


# Windows 10 functions
def escape_windows_string(s):
    return s.replace('"', '\\"').replace("'", "\\'")

def set_clipboard_windows(text):
    text = escape_windows_string(text)
    pyperclip.copy(text)

def paste_and_send_message_windows():
    keyboard.press('ctrl')
    keyboard.press('v')
    keyboard.release('v')
    keyboard.release('ctrl')
    keyboard.press('enter')
    keyboard.release('enter')

# def activate_wechat_and_send_message_windows(message):
#     message = escape_windows_string(message)
#     set_clipboard_windows(message)

#     # You might need to adjust the sleep duration and hotkey to switch to WeChat
#     # time.sleep(1)
#     # keyboard.press('alt')
#     # keyboard.press('tab')
#     # keyboard.release('tab')
#     # keyboard.release('alt')

#     time.sleep(1)
#     paste_and_send_message_windows()

def set_image_to_clipboard_windows(image):
    output = io.BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32con.CF_DIB, data)
    win32clipboard.CloseClipboard()
    
def activate_wechat_and_send_message_windows(message=None, screenshot=None):
    if message:
        message = escape_windows_string(message)
        set_clipboard_windows(message)
    elif screenshot:
        set_image_to_clipboard_windows(screenshot)

    # Activate WeChat
    wechat_window_title = "WeChat"  # Replace with the actual WeChat window title
    pyautogui.getWindowsWithTitle(wechat_window_title)[0].activate()
    # You might need to adjust the sleep duration and hotkey to switch to WeChat
    # time.sleep(1)
    # keyboard.press('alt')
    # keyboard.press('tab')
    # keyboard.release('tab')
    # keyboard.release('alt')

    time.sleep(1)
    paste_and_send_message_windows()

def activate_wechat_and_send_message(message=None, screenshot=None):
    current_os = platform.system()

    if current_os == "Darwin":  # macOS
        activate_wechat_and_send_message_macos(message, screenshot)
    elif current_os == "Windows":
        activate_wechat_and_send_message_windows(message, screenshot)
    else:
        print("Unsupported operating system.")
