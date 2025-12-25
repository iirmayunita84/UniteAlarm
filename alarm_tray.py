import os
import sys
import time
import json
import threading
from datetime import datetime
import pygame
from win10toast import ToastNotifier
import pythoncom
from PIL import Image, ImageDraw
import pystray

# ======================= BASE DIR =======================
if getattr(sys, 'frozen', False):
    BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ======================= FOLDER DATA =======================
APPDATA_DIR = os.path.join(os.getenv("APPDATA"), "UniteAlarm")
os.makedirs(APPDATA_DIR, exist_ok=True)

JADWAL_FILE = os.path.join(APPDATA_DIR, "jadwal.json")
LIBUR_FILE = os.path.join(APPDATA_DIR, "libur.txt")

VOICES_DIR = os.path.join(BASE_DIR, "voices")
os.makedirs(VOICES_DIR, exist_ok=True)

# ======================= INIT =======================
toaster = ToastNotifier()
pygame.mixer.init()

# ======================= DEFAULT JADWAL =======================
DEFAULT_JADWAL = [
    {"jam":"07:00","file":"1_masak.wav","pesan":"Urus rumah"},
    {"jam":"09:00","file":"2_menjahit.wav","pesan":"Menjahit"},
]

if not os.path.exists(JADWAL_FILE):
    with open(JADWAL_FILE, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_JADWAL, f, indent=2, ensure_ascii=False)

# ======================= FUNGSI =======================
def load_jadwal():
    if os.path.exists(JADWAL_FILE):
        with open(JADWAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def is_libur():
    return os.path.exists(LIBUR_FILE)

def play_sound(file_name):
    path = os.path.join(VOICES_DIR, file_name)
    if os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.5)
        except Exception as e:
            print(f"Error play sound {file_name}: {e}")

# ======================= AUTO STARTUP =======================
def add_to_startup():
    try:
        import win32com.client
        startup = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
        target = os.path.abspath(os.path.join(BASE_DIR, "alarm_tray.exe"))
        shortcut_path = os.path.join(startup, "UniteAlarm Tray.lnk")

        shell = win32com.client.Dispatch('WScript.Shell')
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)

        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = os.path.dirname(target)
        shortcut.IconLocation = target
        shortcut.save()
    except Exception as e:
        print(f"⚠️ Gagal add to startup: {e}")

# ======================= LOOP ALARM =======================
def alarm_loop():
    alarm_triggered = set()
    last_day = None

    while True:
        now = datetime.now()
        today = now.date()
        jam_now = now.strftime("%H:%M")

        if last_day != today:
            alarm_triggered.clear()
            last_day = today

        if is_libur():
            time.sleep(30)
            continue

        for item in load_jadwal():
            if item["jam"] == jam_now and jam_now not in alarm_triggered:
                toaster.show_toast("⏰ UniteAlarm", item["pesan"], duration=10, threaded=True)
                if item["file"]:
                    play_sound(item["file"])
                alarm_triggered.add(jam_now)

        time.sleep(20)

# ======================= CREATE TRAY ICON =======================
def create_image():
    # Buat image tray sederhana
    img = Image.new('RGB', (64, 64), color=(0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([16, 16, 48, 48], fill=(255, 0, 0))
    return img

def on_quit(icon, item):
    icon.stop()
    sys.exit(0)

def start_tray():
    image = create_image()
    menu = pystray.Menu(
        pystray.MenuItem('Keluar', on_quit)
    )
    icon = pystray.Icon("UniteAlarm", image, "UniteAlarm Tray", menu)
    icon.run()

# ======================= JALANKAN SEMUA =======================
if __name__ == "__main__":
    # Tambahkan ke startup
    threading.Thread(target=add_to_startup, daemon=True).start()

    # Jalankan alarm loop di thread
    threading.Thread(target=alarm_loop, daemon=True).start()

    # Jalankan tray icon
    start_tray()
