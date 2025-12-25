import os
import zipfile
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
OUTPUT_DIR = os.path.join(BASE_DIR, "UniteAlarm_Portable")
ZIP_PATH = os.path.join(BASE_DIR, "UniteAlarm_Portable.zip")

# daftar file & folder yang ingin dimasukkan
include_files = [
    "unitealarm_panel.exe",
    "alarm_jadwal.exe",
    "jadwal.json",
    "libur.txt",
    "ikon.ico"
]
include_folders = ["voices"]

# pastikan folder output bersih
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# salin file dari dist/
for f in include_files:
    src = os.path.join(DIST_DIR, f)
    if os.path.exists(src):
        shutil.copy(src, OUTPUT_DIR)

# salin folder voices/
for folder in include_folders:
    src_folder = os.path.join(BASE_DIR, folder)
    if os.path.exists(src_folder):
        shutil.copytree(src_folder, os.path.join(OUTPUT_DIR, folder))

# buat zip
with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            zipf.write(file_path, os.path.relpath(file_path, OUTPUT_DIR))

print(f"✅ ZIP selesai dibuat: {ZIP_PATH}")
