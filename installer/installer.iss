#ifndef MyAppVersion
  #error Pass /DMyAppVersion from scripts/package.py (VERSION is the source of truth)
#endif
[Setup]
AppId={{0D4B9685-97C5-4D69-829E-D91DAE0B113E}
AppName=MelodyAI
AppVersion={#MyAppVersion}
AppPublisher=MelodyAI
DefaultDirName={localappdata}\Programs\MelodyAI
DefaultGroupName=MelodyAI
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist\installer
OutputBaseFilename=MelodyAI-Setup-{#MyAppVersion}
SetupIconFile=..\app\assets\icons\melodyai.ico
UninstallDisplayIcon={app}\MelodyAI.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
DisableProgramGroupPage=yes
[Files]
Source: "..\dist\MelodyAI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\MelodyAI"; Filename: "{app}\MelodyAI.exe"
Name: "{autodesktop}\MelodyAI"; Filename: "{app}\MelodyAI.exe"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
[Run]
Filename: "{app}\MelodyAI.exe"; Description: "Launch MelodyAI"; Flags: nowait postinstall skipifsilent
