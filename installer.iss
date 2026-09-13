[Setup]
AppName=AppBlocker
AppVersion=1.0
DefaultDirName={autopf}\AppBlocker
DefaultGroupName=AppBlocker
OutputDir=installer_output
OutputBaseFilename=AppBlockerSetup
Compression=lzma
SolidCompression=yes
SetupIconFile=MainIcon.ico

[Files]
Source: "dist\AppBlocker.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\AppBlockerWatchdog.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\appBlockerIconImage.png"; DestDir: "{app}"; Flags: ignoreversion
<<<<<<< HEAD
Source: "dist\appBlockerKeyImage.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "MainIcon.ico"; DestDir: "{app}"; Flags: ignoreversion
=======
Source: "dist\appBlockerKeyImage.png"; DestDir: "{app}"; Flags: ignoreversion
>>>>>>> 51274b0f373e644a4f8f3cc4cae80cee93154bbb

[Icons]
Name: "{group}\AppBlocker"; Filename: "{app}\AppBlocker.exe"
Name: "{commondesktop}\AppBlocker"; Filename: "{app}\AppBlocker.exe"

[Run]
<<<<<<< HEAD
Filename: "{app}\AppBlocker.exe"; Description: "Launch AppBlocker"; Flags: postinstall nowait skipifsilent
=======
Filename: "{app}\AppBlocker.exe"; Description: "Launch AppBlocker"; Flags: postinstall nowait skipifsilent
>>>>>>> 51274b0f373e644a4f8f3cc4cae80cee93154bbb
