import os
import sys
import subprocess
import traceback


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ikon_path = os.path.join(BASE_DIR, "ikon.ico")

# === File & folder pendukung ===
data_files = [
    f"voices{os.pathsep}voices",
    f"jadwal.json{os.pathsep}.",
    f"libur.txt{os.pathsep}."
]

files_to_build = [
    {"py": "alarm_jadwal.py", "exe": "alarm_jadwal.exe", "windowed": True},
    {"py": "unitealarm_panel.py", "exe": "unitealarm_panel.exe", "windowed": True}
]

# === Fungsi build ===
def build_program(py_file, exe_name, windowed):
    if not os.path.exists(py_file):
        print(f"❌ File tidak ditemukan: {py_file}")
        return False

    windowed_flag = "--windowed" if windowed else "--console"
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",
        "--noconfirm",
        "--clean",
        windowed_flag,
        f"--icon={ikon_path}"
    ]

    for data in data_files:
        cmd.extend(["--add-data", data])

    cmd.append(py_file)

    print(f"\n🚀 Membuild: {exe_name}")
    process = subprocess.run(cmd, cwd=BASE_DIR, text=True)
    if process.returncode != 0:
        print(f"❌ Build gagal: {exe_name} (kode {process.returncode})")
        return False

    print(f"✅ Build selesai: {exe_name}")
    return True


# === Jalankan semua build ===
if __name__ == "__main__":
    print("📦 Starting build for UniteAlarm...")
    print("Working dir:", BASE_DIR)

    for f in files_to_build:
        full_path = os.path.join(BASE_DIR, f["py"])
        if not build_program(full_path, f["exe"], f["windowed"]):
            print("\n⚠️ Proses dihentikan karena ada build yang gagal.")
            sys.exit(1)

    print("\n🎉 Semua build selesai sukses! Cek folder 'dist' untuk hasil .exe.")
