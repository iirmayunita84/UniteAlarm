import os, sys, json, time, threading, datetime
import tkinter as tk
from tkinter import ttk, messagebox
import pygame
from win10toast import ToastNotifier
import warnings
import wave
import subprocess
from win32com.client import Dispatch
import pystray
from PIL import Image, ImageDraw


silent_mode = False

warnings.filterwarnings("ignore")

# ================== KONFIG DASAR ==================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def make_default_icon(color):
    img = Image.new("RGB", (64, 64), color)
    d = ImageDraw.Draw(img)
    d.text((18, 18), "⏰", fill="white")
    return img


def load_icon(nama, fallback_color):
    path = os.path.join(BASE_DIR, nama)
    if os.path.exists(path):
        return Image.open(path)
    return make_default_icon(fallback_color)


ICON_IDLE = load_icon("icon_idle.ico", "#f48fb1")
ICON_ACTIVE = load_icon("icon_active.ico", "#2e7d32")


# Folder data di AppData
APPDATA_DIR = os.path.join(os.getenv("APPDATA"), "UniteAlarm")
os.makedirs(APPDATA_DIR, exist_ok=True)


# File jadwal dan libur di AppData
JADWAL_FILE = os.path.join(APPDATA_DIR, "jadwal.json")
LIBUR_FILE = os.path.join(APPDATA_DIR, "libur.txt")

# Folder suara tetap di folder Program Files / BASE_DIR
VOICES_DIR = os.path.join(BASE_DIR, "voices")
os.makedirs(VOICES_DIR, exist_ok=True)

toaster = ToastNotifier()

COLOR_BG = "#fff7f9"
COLOR_TEXT = "#c2185b"
COLOR_ON = "#2e7d32"
COLOR_OFF = "#c2185b"

FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_BTN = ("Segoe UI", 10, "bold")
FONT_ENTRY = ("Segoe UI", 10)

# ================== DEFAULT JADWAL ==================
DEFAULT_JADWAL = [
    {"jam":"07:00","file":"1_masak.wav","pesan":"Urus rumah"},
    {"jam":"09:00","file":"2_menjahit.wav","pesan":"Menjahit"},
]

if not os.path.exists(JADWAL_FILE):
    with open(JADWAL_FILE,"w",encoding="utf-8") as f:
        json.dump(DEFAULT_JADWAL,f,indent=2,ensure_ascii=False)

# ================== AUDIO ==================
try:
    pygame.mixer.init()
except Exception as e:
    print("Audio init gagal:", e)


# ================== HELPER ================== 
def hitung_alarm_berikutnya(jadwal):
    now = datetime.datetime.now()
    kandidat = []

    for r in jadwal:
        try:
            jam = datetime.datetime.strptime(r["jam"], "%H:%M").time()
            dt = datetime.datetime.combine(now.date(), jam)
            if dt > now:
                kandidat.append((dt, r))
        except:
            continue

    if not kandidat:
        return None

    kandidat.sort(key=lambda x: x[0])
    return kandidat[0]

def load_jadwal():
    with open(JADWAL_FILE,"r",encoding="utf-8") as f:
        return json.load(f)

def save_jadwal_from_tree():
    data=[]
    for i in tree.get_children():
        jam,file,pesan = tree.item(i,"values")
        data.append({"jam":jam,"file":file,"pesan":pesan})
    with open(JADWAL_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=2,ensure_ascii=False)
                
def cek_wav_valid(path):
    try:
        with wave.open(path, "rb") as w:
            channels = w.getnchannels()
            sampwidth = w.getsampwidth()   # byte
            framerate = w.getframerate()

            # PCM 16-bit = 2 byte
            if sampwidth != 2:
                return False, "Bit depth bukan 16-bit"

            if framerate != 44100:
                return False, "Sample rate bukan 44100 Hz"

            return True, "OK"

    except wave.Error:
        return False, "Format WAV tidak valid"
    except Exception as e:
        return False, str(e)
           
def auto_convert_wav(path):
    ffmpeg = os.path.join(BASE_DIR, "ffmpeg", "ffmpeg.exe")
    if not os.path.exists(ffmpeg):
        return False, "FFmpeg tidak ditemukan"

    out = path.replace(".wav", "_fixed.wav")

    cmd = [
        ffmpeg, "-y",
        "-i", path,
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        out
    ]

    try:
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True, out
    except:
        return False, "Gagal convert"         
        

def cek_semua_audio():
    files = [f for f in os.listdir(VOICES_DIR) if f.lower().endswith(".wav")]

    if not files:
        messagebox.showinfo("Cek Audio", "Folder voices kosong.")
        return

    ok_list = []
    bad_list = []

    for f in files:
        path = os.path.join(VOICES_DIR, f)
        valid, info = cek_wav_valid(path)
        if valid:
            ok_list.append(f)
        else:
            bad_list.append(f"{f} → {info}")

    pesan = ""

    if ok_list:
        pesan += "✅ Audio VALID:\n"
        pesan += "\n".join(ok_list)
        pesan += "\n\n"

    if bad_list:
        pesan += "❌ Audio TIDAK VALID:\n"
        pesan += "\n".join(bad_list)
        pesan += "\n\n💡 Gunakan WAV PCM 16-bit 44100 Hz"

    messagebox.showinfo("Hasil Cek Audio", pesan)
 
        
def scan_voices():
    hasil = []
    for f in os.listdir(VOICES_DIR):
        if not f.lower().endswith(".wav"):
            continue

        path = os.path.join(VOICES_DIR, f)
        valid, _ = cek_wav_valid(path)
        if valid:
            hasil.append(f)

    return hasil

def is_libur():
    return os.path.exists(LIBUR_FILE)


def popup(teks):
    messagebox.showinfo("UniteAlarm", teks)
    
def add_to_startup():
    try:
        startup = os.path.expanduser(
            r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
        )

        if not os.path.isdir(startup):
            popup(f"❌ Folder Startup tidak ditemukan:\n{startup}")
            return

        shortcut_path = os.path.join(startup, "UniteAlarm.lnk")

        # 🧹 hapus shortcut lama jika ada
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)

        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(shortcut_path)

        if getattr(sys, "frozen", False):
            shortcut.TargetPath = sys.executable
            shortcut.WorkingDirectory = os.path.dirname(sys.executable)
            shortcut.Arguments = ""
        else:
            shortcut.TargetPath = sys.executable
            shortcut.Arguments = f'"{os.path.abspath(__file__)}"'
            shortcut.WorkingDirectory = os.path.dirname(sys.executable)

        shortcut.IconLocation = shortcut.TargetPath
        shortcut.Save()

        popup("✅ Startup otomatis BERHASIL ditambahkan")

    except Exception as e:
        popup(f"❌ Gagal menambahkan startup:\n{e}")


def stop_alarm():
    global alarm_running
    alarm_running = False

    try:
        pygame.mixer.music.stop()
    except:
        pass

    # 🧠 update status GUI (AMAN THREAD)
    root.after(0, next_alarm_var.set, "Alarm dihentikan")

    # 🔄 update tray
    update_tray_status()

    if silent_mode:
        toaster.show_toast(
            "UniteAlarm",
            "🔕 Alarm dihentikan (Silent Mode)",
            duration=2,
            threaded=True
        )
    else:
        root.after(0, popup, "⏹ Alarm dihentikan")


def toggle_silent(icon=None, item=None):
    global silent_mode
    silent_mode = not silent_mode

    status = "ON" if silent_mode else "OFF"
    toaster.show_toast(
        "UniteAlarm",
        f"🔕 Mode Silent {status}",
        duration=3,
        threaded=True
    )


def show_window(icon=None, item=None):
    root.after(0, root.deiconify)

def quit_app(icon=None, item=None):
    global alarm_running
    alarm_running = False
    try:
        pygame.mixer.music.stop()
    except:
        pass
    if icon:
        icon.stop()
    root.after(0, root.destroy)



# ================== GUI ==================
root = tk.Tk()
root.title("💖 UniteAlarm")
root.geometry("1000x600")
root.config(bg=COLOR_BG)
root.resizable(False, False)

next_alarm_var = tk.StringVar(value="Alarm berikutnya: -")

# ================== STATUS ==================
lbl_status = tk.Label(
    root,
    text="Status: AKTIF",
    font=FONT_TITLE,
    fg=COLOR_ON,
    bg=COLOR_BG
)
lbl_status.pack(pady=6)

lbl_next = tk.Label(
    root,
    textvariable=next_alarm_var,
    font=FONT_LABEL,
    bg=COLOR_BG,
    fg=COLOR_TEXT
)
lbl_next.pack(pady=(0, 6))
tray_icon = None

def update_tray_status():
    if tray_icon:
        tray_icon.icon = ICON_ACTIVE if alarm_running else ICON_IDLE
        tray_icon.title = f"UniteAlarm | {next_alarm_var.get()}"

def on_close():
    root.withdraw()  # sembunyikan window
    toaster.show_toast(
        "⏰ UniteAlarm",
        "Alarm tetap berjalan di background",
        duration=4,
        threaded=True
    )


root.protocol("WM_DELETE_WINDOW", on_close)

def setup_tray():
    global tray_icon

    menu = pystray.Menu(
        pystray.MenuItem("📂 Buka UniteAlarm", show_window),
        pystray.MenuItem("⏹ Stop Alarm", stop_alarm),
        pystray.MenuItem("❌ Keluar", quit_app)
    )

    tray_icon = pystray.Icon(
        "UniteAlarm",
        ICON_IDLE,
        "⏰ UniteAlarm",
        menu
    )

    tray_icon.run()
threading.Thread(target=setup_tray, daemon=True).start()

# ================== FRAME TOMBOL ATAS ==================
frame_btn = tk.Frame(root, bg=COLOR_BG)
frame_btn.pack(pady=6)

alarm_running = False
alarm_played_today = set()


def jalankan_alarm():
    global alarm_running
    if alarm_running:
        popup("⏰ Alarm sudah berjalan")
        return

    alarm_running = True
    update_tray_status()
    popup("⏰ Alarm berjalan (hemat CPU)")

    def loop_alarm():
        global alarm_played_today

        jadwal = load_jadwal()
        last_day = None

        while alarm_running:

            # 🌙 MODE LIBUR
            if is_libur():
                next_alarm_var.set("Mode Libur aktif 🌙")
                update_tray_status()
                time.sleep(30)
                continue

            now = datetime.datetime.now()
            today = now.date()
            jam_now = now.strftime("%H:%M")

            # 🔄 reset harian
            if last_day != today:
                alarm_played_today.clear()
                last_day = today

            # ⏳ HITUNG ALARM BERIKUTNYA
            next_alarm = hitung_alarm_berikutnya(jadwal)
            if next_alarm:
                delta = int((next_alarm[0] - now).total_seconds())
                menit = delta // 60
                detik = delta % 60
                next_alarm_var.set(
                    f"Alarm berikutnya {next_alarm[1]['jam']} ({menit}m {detik}s)"
                )
            else:
                next_alarm_var.set("Tidak ada alarm lagi hari ini")

            update_tray_status()

            # 🔔 CEK ALARM
            for r in jadwal:
                if r["jam"] == jam_now and r["jam"] not in alarm_played_today:
                    path = os.path.join(VOICES_DIR, r["file"])

                    if not os.path.exists(path):
                        popup(f"❌ Audio tidak ditemukan:\n{r['file']}")
                        continue

                    valid, info = cek_wav_valid(path)
                    if not valid:
                        popup(f"⚠️ Format salah:\n{info}")
                        continue

                    try:
                        if not silent_mode:
                            pygame.mixer.music.load(path)
                            pygame.mixer.music.play()

                        toaster.show_toast(
                            "⏰ UniteAlarm",
                            r["pesan"],
                            duration=5,
                            threaded=True
                        )

                        alarm_played_today.add(r["jam"])

                    except Exception as e:
                        popup(f"❌ Gagal play\n{e}")

            # 🧊 SUPER DINGIN CPU
            time.sleep(1 if next_alarm else 30)

    threading.Thread(target=loop_alarm, daemon=True).start()

def preview_alarm():
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Info", "Pilih jadwal dulu")
        return

    jam, file, pesan = tree.item(sel[0], "values")
    path = os.path.join(VOICES_DIR, file)

    # ❌ file tidak ada
    if not os.path.exists(path):
        messagebox.showerror(
            "❌ File Tidak Ditemukan",
            "File suara tidak ada di folder voices."
        )
        return

    # 🔍 validasi format WAV
    valid, info = cek_wav_valid(path)

    if not valid:
        res = messagebox.askyesno(
            "❌ Format Audio Salah",
            f"{info}\n\nIngin auto-convert ke format standar?"
        )
        if not res:
            return

        ok, result = auto_convert_wav(path)
        if not ok:
            messagebox.showerror("Gagal Convert", result)
            return

        path = result
        combo_file.set(os.path.basename(path))
        refresh_suara()

    # ▶️ preview audio (atau silent)
    try:
        pygame.mixer.music.stop()

        if silent_mode:
            toaster.show_toast(
                "UniteAlarm",
                "🔕 Mode Silent aktif (audio tidak diputar)",
                duration=2,
                threaded=True
            )
        else:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()

    except Exception as e:
        messagebox.showerror("❌ Error Audio", str(e))


def refresh_suara():
    combo_file["values"] = scan_voices()
    popup("🔁 Daftar suara diperbarui")

def cek_jadwal():
    teks = "\n".join(
        f"{i+1}. {r['jam']} - {r['pesan']}"
        for i, r in enumerate(load_jadwal())
    )
    messagebox.showinfo("Jadwal Hari Ini", teks or "Belum ada jadwal")

def toggle_libur():
    if is_libur():
        os.remove(LIBUR_FILE)
        lbl_status.config(text="Status: AKTIF", fg=COLOR_ON)
        popup("🟢 Mode Libur DIMATIKAN")
    else:
        open(LIBUR_FILE, "w").close()
        lbl_status.config(text="Status: LIBUR", fg=COLOR_OFF)
        popup("🌙 Mode Libur DIAKTIFKAN")

def startup_dummy():
    popup("⚙️ Startup otomatis (placeholder)")

tk.Button(frame_btn, text="🧪 Cek Audio", command=cek_semua_audio).grid(row=0,column=1,padx=4)
tk.Button(frame_btn, text="⏹ Stop Alarm", command=stop_alarm).grid(row=0,column=2,padx=4)
tk.Button(frame_btn, text="▶ Jalankan Alarm", command=jalankan_alarm).grid(row=0,column=3,padx=4)
tk.Button(frame_btn, text="▶ Preview", command=preview_alarm).grid(row=0,column=4,padx=4)
tk.Button(frame_btn, text="🔁 Refresh Suara", command=refresh_suara).grid(row=0,column=5,padx=4)
tk.Button(frame_btn, text="🔔 Cek Jadwal Hari Ini", command=cek_jadwal).grid(row=0,column=6,padx=4)
tk.Button(frame_btn, text="🌙 Libur: ON/OFF", command=toggle_libur).grid(row=0,column=7,padx=4)
tk.Button(frame_btn, text="⚙️ Startup Otomatis", command=add_to_startup).grid(row=0,column=8,padx=4)

# ================== TREE ==================
frame=tk.LabelFrame(root,text="📝 Edit Jadwal",bg=COLOR_BG,fg=COLOR_TEXT,font=FONT_LABEL)
frame.pack(fill="both",padx=10,pady=8)

cols=("Jam","File","Pesan")
tree=ttk.Treeview(frame,columns=cols,show="headings",height=12)
for c in cols:
    tree.heading(c,text=c)
    tree.column(c,width=260)
tree.grid(row=0,column=0,columnspan=4,padx=6,pady=6)

sb=ttk.Scrollbar(frame,orient="vertical",command=tree.yview)
tree.configure(yscroll=sb.set)
sb.grid(row=0,column=4,sticky="ns")

def populate_tree():
    tree.delete(*tree.get_children())
    for r in load_jadwal():
        tree.insert("", "end", values=(r["jam"],r["file"],r["pesan"]))

populate_tree()

# ================== FORM ==================
tk.Label(frame,text="Jam (HH:MM):",bg=COLOR_BG).grid(row=1,column=0,sticky="e")
entry_jam=tk.Entry(frame,font=FONT_ENTRY,width=10)
entry_jam.grid(row=1,column=1,sticky="w")

tk.Label(frame,text="File Suara:",bg=COLOR_BG).grid(row=1,column=2,sticky="e")
combo_file=ttk.Combobox(frame,values=scan_voices(),width=28)
combo_file.grid(row=1,column=3,sticky="w")

tk.Label(frame,text="Pesan:",bg=COLOR_BG).grid(row=2,column=0,sticky="e")
entry_pesan=tk.Entry(frame,font=FONT_ENTRY,width=62)
entry_pesan.grid(row=2,column=1,columnspan=3,sticky="w",pady=4)

# ================== BUTTON ==================
def add_row():
    jam = entry_jam.get()
    file = combo_file.get()
    pesan = entry_pesan.get()

    if not jam or not file:
        messagebox.showwarning("Lengkapi Data", "Jam dan file suara wajib diisi.")
        return

    path = os.path.join(VOICES_DIR, file)
    valid, info = cek_wav_valid(path)

    if not valid:
        messagebox.showerror(
            "❌ Audio Tidak Bisa Digunakan",
            f"{file}\n\nAlasan: {info}\n\n"
            "Gunakan WAV PCM 16-bit 44100 Hz."
        )
        return

    tree.insert("", "end", values=(jam, file, pesan))
    save_jadwal_from_tree()

def update_row():
    sel=tree.selection()
    if not sel: return
    tree.item(sel[0],
        values=(entry_jam.get(),combo_file.get(),entry_pesan.get()))
    save_jadwal_from_tree()

def delete_row():
    for s in tree.selection():
        tree.delete(s)
    save_jadwal_from_tree()

tk.Button(frame,text="➕ Tambah",command=add_row,font=FONT_BTN).grid(row=3,column=0,pady=6)
tk.Button(frame,text="✏ Update",command=update_row,font=FONT_BTN).grid(row=3,column=1)
tk.Button(frame,text="🗑 Hapus",command=delete_row,font=FONT_BTN).grid(row=3,column=2)

# ================== AUTO EDIT (DOUBLE CLICK) ==================
def on_double_click(e):
    region=tree.identify_region(e.x,e.y)
    if region!="cell": return
    row=tree.identify_row(e.y)
    col=tree.identify_column(e.x)
    x,y,w,h=tree.bbox(row,col)
    value=tree.set(row,col)

    ent=tk.Entry(tree,font=FONT_ENTRY)
    ent.insert(0,value)
    ent.place(x=x,y=y,width=w,height=h)
    ent.focus()

    def save_edit(event=None):
        tree.set(row, tree["columns"][int(col[1:])-1], ent.get())
        ent.destroy()
        save_jadwal_from_tree()

    ent.bind("<Return>",save_edit)
    ent.bind("<FocusOut>",save_edit)

tree.bind("<Double-1>",on_double_click)

# ================== SYNC FORM ==================
def on_select(e=None):
    sel=tree.selection()
    if not sel: return
    jam,file,pesan=tree.item(sel[0],"values")
    entry_jam.delete(0,"end"); entry_jam.insert(0,jam)
    combo_file.set(file)
    entry_pesan.delete(0,"end"); entry_pesan.insert(0,pesan)

tree.bind("<<TreeviewSelect>>",on_select)

root.mainloop()
