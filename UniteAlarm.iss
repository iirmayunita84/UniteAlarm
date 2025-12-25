[Setup]
AppName=UniteAlarm
AppVersion=1.0
DefaultDirName={pf}\UniteAlarm
DefaultGroupName=UniteAlarm
OutputDir=Output
OutputBaseFilename=UniteAlarm_Setup
SetupIconFile=unitealarm.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
PrivilegesRequired=admin
UninstallDisplayIcon={app}\unitealarm_panel.exe
AppPublisher=Irma Studio

[Files]
Source: "dist\alarm_jadwal.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\unitealarm_panel.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\alarm_tray.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "voices\*"; DestDir: "{app}\voices"; Flags: recursesubdirs ignoreversion
Source: "unitealarm.ico"; DestDir: "{app}"; Flags: ignoreversion
 

[Icons]
Name: "{autoprograms}\UniteAlarm Panel"; Filename: "{app}\unitealarm_panel.exe"; IconFilename: "{app}\unitealarm.ico"
Name: "{autoprograms}\Alarm Otomatis"; Filename: "{app}\alarm_jadwal.exe"; IconFilename: "{app}\unitealarm.ico"
Name: "{autoprograms}\Alarm Tray (Auto Start)"; Filename: "{app}\alarm_tray.exe"; IconFilename: "{app}\unitealarm.ico"
Name: "{autodesktop}\UniteAlarm"; Filename: "{app}\unitealarm_panel.exe"; IconFilename: "{app}\unitealarm.ico"


[Dirs]
Name: "{userappdata}\UniteAlarm"; Flags: uninsalwaysuninstall

[Run]
Filename: "{app}\unitealarm_panel.exe"; Description: "Jalankan UniteAlarm sekarang"; Flags: nowait postinstall skipifsilent
Filename: "{app}\alarm_tray.exe"; Description: "Jalankan UniteAlarm Tray (Notifikasi)"; Flags: nowait postinstall skipifsilent


[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\UniteAlarm"
