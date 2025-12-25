import os, sys, time, json
from datetime import datetime
from win10toast import ToastNotifier
import pygame

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

# ======================= LOOP ALARM =======================
def main_loop():
    alarm_triggered = set()  # simpan jam yang sudah di-notify hari ini
    last_day = None

    while True:
        now = datetime.now()
        today = now.date()
        jam_now = now.strftime("%H:%M")

        # reset alarm harian
        if last_day != today:
            alarm_triggered.clear()
            last_day = today

        if is_libur():
            print("Mode Libur aktif 🌙")
            time.sleep(30)
            continue

        for item in load_jadwal():
            if item["jam"] == jam_now and jam_now not in alarm_triggered:
                # tampilkan notifikasi
                toaster.show_toast("⏰ UniteAlarm", item["pesan"], duration=10, threaded=True)
                # mainkan suara
                if item["file"]:
                    play_sound(item["file"])
                alarm_triggered.add(jam_now)

        time.sleep(20)  # cek tiap 20 detik

# ======================= JALANKAN =======================
if __name__ == "__main__":
    print("⏰ UniteAlarm berjalan... (Ctrl+C untuk berhenti)")
    main_loop()
