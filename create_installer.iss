; Script Inno Setup simplifié pour Navigateur Rapide

[Setup]
AppId={{A8E58742-0544-4E87-A1BF-3453372B28B4}}
AppName=Navigateur Rapide
AppVersion=1.0
AppPublisher=Matteo
DefaultDirName={autopf}\NavigateurRapide
OutputDir=.
OutputBaseFilename=NavigateurRapide-Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le bureau"; Flags: unchecked

[Files]
Source: "dist\Navigateur Rapide\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Navigateur Rapide"; Filename: "{app}\Navigateur Rapide.exe"
Name: "{autodesktop}\Navigateur Rapide"; Filename: "{app}\Navigateur Rapide.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Navigateur Rapide.exe"; Description: "Lancer Navigateur Rapide"; Flags: nowait postinstall skipifsilent