; Скрипт установщика JARVIS

[Setup]
AppName=JARVIS
AppVersion=1.0
AppPublisher=JARVIS Project
DefaultDirName={autopf}\JARVIS
DefaultGroupName=JARVIS
OutputDir=installer_output
OutputBaseFilename=JARVIS_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\JARVIS.exe
PrivilegesRequired=admin

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные значки:"

[Files]
Source: "dist\JARVIS.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\JARVIS"; Filename: "{app}\JARVIS.exe"
Name: "{group}\Удалить JARVIS"; Filename: "{uninstallexe}"
Name: "{autodesktop}\JARVIS"; Filename: "{app}\JARVIS.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\JARVIS.exe"; Description: "Запустить JARVIS"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\JARVIS"