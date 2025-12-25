import os, sys, subprocess, shutil, wave

# ======================= Direktori dasar =======================
if getattr(sys, 'frozen', False):
    BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VOICES_DIR = os.path.join(BASE_DIR, "voices")
os.makedirs(VOICES_DIR, exist_ok=True)

# ======================= File & folder pendukung =======================
data_files = [
    f"voices{os.pathsep}voices",
    f"jadwal.json{os.pathsep}.",
    f"libur.txt{os.pathsep}."
]

files_to_build = [
    {"py": "alarm_jadwal.py", "exe": "alarm_jadwal.exe"},
    {"py": "unitealarm_panel.py", "exe": "unitealarm_panel.exe"},
    {"py": "alarm_tray.py", "exe": "alarm_tray.exe"}
]

# ======================= Helper Audio =======================
def cek_wav_valid(path):
    try:
        with wave.open(path, "rb") as w:
            return w.getsampwidth() == 2 and w.getframerate() == 44100
    except:
        return False

def auto_convert_wav(path):
    ffmpeg = os.path.join(BASE_DIR, "ffmpeg", "ffmpeg.exe")
    if not os.path.exists(ffmpeg):
        print(f"⚠️ FFmpeg tidak ditemukan, lewati konversi: {path}")
        return path
    out = path.replace(".wav", "_fixed.wav")
    subprocess.run([ffmpeg, "-y", "-i", path, "-acodec", "pcm_s16le", "-ar", "44100", out],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out

def scan_and_fix_voices():
    for f in os.listdir(VOICES_DIR):
        if not f.lower().endswith(".wav"): continue
        path = os.path.join(VOICES_DIR, f)
        if not cek_wav_valid(path):
            print(f"⚠️ WAV tidak valid, konversi: {f}")
            fixed = auto_convert_wav(path)
            if fixed != path:
                os.replace(fixed, path)
                print(f"✅ Berhasil konversi: {f}")

# ======================= Build Program =======================
def build_program(py_file, exe_name, mode="release"):
    if not os.path.exists(py_file):
        print(f"❌ File tidak ditemukan: {py_file}")
        return False
    windowed_flag = "--windowed" if mode=="release" else "--console"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--noconfirm", "--clean",
        windowed_flag,
        f"--icon={os.path.join(BASE_DIR,'unitealarm.ico')}"
    ]
    for data in data_files:
        cmd.extend(["--add-data", data.replace(";", os.pathsep)])
    cmd.append(py_file)
    print(f"\n🚀 Membuild: {exe_name} ({mode.upper()} MODE)")
    r = subprocess.run(cmd, cwd=BASE_DIR)
    if r.returncode != 0:
        print(f"❌ Build gagal: {exe_name}")
        return False
    print(f"✅ Build selesai: {exe_name}")
    return True

# ======================= MAIN =======================
if __name__ == "__main__":
    print("🔊 Cek dan konversi audio WAV sebelum build...")
    scan_and_fix_voices()

    # Hapus build lama
    for f in ["build", "dist"]:
        if os.path.exists(os.path.join(BASE_DIR,f)):
            shutil.rmtree(os.path.join(BASE_DIR,f), ignore_errors=True)

    # Build semua exe
    for f in files_to_build:
        if not build_program(f["py"], f["exe"]):
            sys.exit(1)

# ======================= Buat folder portable =======================
PORTABLE_DIR = os.path.join(BASE_DIR, "UniteAlarm_Portable")
os.makedirs(PORTABLE_DIR, exist_ok=True)

# Copy exe
for exe in [f["exe"] for f in files_to_build]:
    src = os.path.join(BASE_DIR, "dist", exe)
    dst = os.path.join(PORTABLE_DIR, exe)
    if os.path.exists(src):
        if os.path.exists(dst):
            os.remove(dst)
        shutil.copy2(src, PORTABLE_DIR)

# Copy folder voices
voices_dst = os.path.join(PORTABLE_DIR, "voices")
if os.path.exists(VOICES_DIR):
    shutil.copytree(VOICES_DIR, voices_dst, dirs_exist_ok=True)

# Copy jadwal & libur
for file in ["jadwal.json", "libur.txt"]:
    src = os.path.join(os.getenv("APPDATA"), "UniteAlarm", file)
    dst = os.path.join(PORTABLE_DIR, file)
    if os.path.exists(src):
        shutil.copy2(src, dst)

# Copy ikon
ikon_src = os.path.join(BASE_DIR, "unitealarm.ico")
if os.path.exists(ikon_src):
    shutil.copy2(ikon_src, PORTABLE_DIR)

# ======================= Buat Launcher Batch =======================
launcher_path = os.path.join(PORTABLE_DIR, "start_portable.bat")
with open(launcher_path, "w", encoding="utf-8") as f:
    f.write("""@echo off
start "" "alarm_tray.exe"
start "" "unitealarm_panel.exe"
exit
""")

# ======================= Buat installer Inno Setup =======================
INNO_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
ISS_FILE = os.path.join(BASE_DIR, "UniteAlarm.iss")
if os.path.exists(INNO_PATH) and os.path.exists(ISS_FILE):
    print("🧩 Membuat installer...")
    subprocess.run([INNO_PATH, ISS_FILE])
else:
    print("⚠️ Inno Setup atau ISS file tidak ditemukan, melewati installer.")

print(f"\n📦 Folder portable siap: {PORTABLE_DIR}")
print("🎉 Semua build selesai sukses!")
