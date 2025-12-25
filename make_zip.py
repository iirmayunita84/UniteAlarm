import os
import shutil
from zipfile import ZipFile

# ================== KONFIG ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_ZIP = os.path.join(BASE_DIR, "UniteAlarm_Final.zip")

# Folder/file yang akan dimasukkan ke ZIP
INCLUDE_ITEMS = [
    "alarm_jadwal.py",
    "unitealarm_panel.py",
    "build_all.py",
    "build.bat",
    "UniteAlarm.iss",
    "unitealarm.ico",
    "voices",
    "ffmpeg"
]

# ================== HAPUS ZIP LAMA ==================
if os.path.exists(OUTPUT_ZIP):
    os.remove(OUTPUT_ZIP)

# ================== MEMBUAT ZIP ==================
with ZipFile(OUTPUT_ZIP, 'w') as zipf:
    for item in INCLUDE_ITEMS:
        full_path = os.path.join(BASE_DIR, item)
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                for root, dirs, files in os.walk(full_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, BASE_DIR)
                        zipf.write(file_path, arcname)
            else:
                zipf.write(full_path, item)

print(f"✅ ZIP selesai dibuat: {OUTPUT_ZIP}")
