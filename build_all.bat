@echo off
cd /d %~dp0

echo 🔹 Hentikan proses lama jika ada...
taskkill /f /im alarm_jadwal.exe >nul 2>&1
taskkill /f /im unitealarm_panel.exe >nul 2>&1

echo 🔹 Jalankan build_all.py (otomatis fix WAV + build EXE)
python build_all.py
if %errorlevel% neq 0 (
    echo ❌ Build gagal, cek error di atas.
    pause
    exit /b
)

REM ==================== Buat folder portable ====================
set "PORTABLE_DIR=%cd%\UniteAlarm_Portable"
if exist "%PORTABLE_DIR%" rmdir /s /q "%PORTABLE_DIR%"
mkdir "%PORTABLE_DIR%"

echo 🔹 Copy EXE ke portable
copy /y "dist\alarm_jadwal.exe" "%PORTABLE_DIR%" >nul
copy /y "dist\unitealarm_panel.exe" "%PORTABLE_DIR%" >nul

echo 🔹 Copy folder voices
xcopy /e /i /y "voices" "%PORTABLE_DIR%\voices" >nul

echo 🔹 Copy data jadwal & libur
if exist "%APPDATA%\UniteAlarm\jadwal.json" copy /y "%APPDATA%\UniteAlarm\jadwal.json" "%PORTABLE_DIR%" >nul
if exist "%APPDATA%\UniteAlarm\libur.txt" copy /y "%APPDATA%\UniteAlarm\libur.txt" "%PORTABLE_DIR%" >nul

echo 🔹 Copy ikon
if exist "unitealarm.ico" copy /y "unitealarm.ico" "%PORTABLE_DIR%" >nul

REM ==================== Buat installer Inno Setup ====================
set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
set "ISS_FILE=%cd%\UniteAlarm.iss"

if exist "%INNO_PATH%" if exist "%ISS_FILE%" (
    echo 🧩 Membuat installer...
    "%INNO_PATH%" "%ISS_FILE%"
    if %errorlevel% neq 0 echo ❌ Gagal membuat installer.
) else (
    echo ⚠️ Inno Setup atau ISS file tidak ditemukan, melewati installer.
)

REM ==================== Restart EXE ====================
echo 🔹 Jalankan unitealarm_panel.exe otomatis...
start "" "%PORTABLE_DIR%\unitealarm_panel.exe"

echo 🎉 Selesai! Portable siap dan EXE berjalan.
pause
