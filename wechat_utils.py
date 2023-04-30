import os
import platform
import time

# macOS functions
def escape_applescript_string(s):
    return s.replace('"', '\\"').replace("'", "\\'")

def run_applescript(script):
    escaped_script = escape_applescript_string(script)
    os.system(f"osascript -e '{escaped_script}'")

def set_clipboard_macos(text):
    text = escape_applescript_string(text)
    run_applescript(f'set the clipboard to "{text}"')

def activate_wechat_and_send_message_macos(message):
    message = escape_applescript_string(message)
    set_clipboard_macos(message)
    run_applescript('activate application "WeChat"')
    run_applescript('delay 1')
    run_applescript('tell application "System Events" to keystroke "v" using command down')
    run_applescript('tell application "System Events" to keystroke return')

# Windows 10 functions
import pyperclip
import keyboard

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

def activate_wechat_and_send_message_windows(message):
    message = escape_windows_string(message)
    set_clipboard_windows(message)

    # You might need to adjust the sleep duration and hotkey to switch to WeChat
    time.sleep(1)
    keyboard.press('alt')
    keyboard.press('tab')
    keyboard.release('tab')
    keyboard.release('alt')

    time.sleep(1)
    paste_and_send_message_windows()

def activate_wechat_and_send_message(message):
    current_os = platform.system()

    if current_os == "Darwin":  # macOS
        activate_wechat_and_send_message_macos(message)
    elif current_os == "Windows":
        activate_wechat_and_send_message_windows(message)
    else:
        print("Unsupported operating system.")
