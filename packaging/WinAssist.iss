#define MyAppName "WinAssist"
#define MyAppVersion "0.10.0"
#define MyAppPublisher "WinAssist Local"
#define MyAppExeName "WinAssist.exe"

[Setup]
AppId={{D68B864B-1469-4D29-9A76-7B63894D3FAE}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppContact=minhquanpro65@gmail.com
AppSupportURL=mailto:minhquanpro65@gmail.com
DefaultDirName={localappdata}\Programs\WinAssist
DisableDirPage=no
DefaultGroupName=WinAssist
OutputDir=..\dist\installer
OutputBaseFilename=WinAssist-{#MyAppVersion}-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=WinAssist.ico
CloseApplications=yes
RestartApplications=yes
SetupLogging=yes

[Files]
Source: "..\dist\WinAssist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "MicrosoftEdgeWebview2Setup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\WinAssist"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\WinAssist"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng ngoài Desktop"; GroupDescription: "Biểu tượng bổ sung:"

[Run]
Filename: "{tmp}\MicrosoftEdgeWebview2Setup.exe"; Parameters: "/silent /install"; StatusMsg: "Đang chuẩn bị giao diện Windows..."; Flags: waituntilterminated
Filename: "{app}\{#MyAppExeName}"; Description: "Mở WinAssist"; Flags: nowait postinstall; Check: ShouldLaunchWinAssist

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\WinAssist Local"; Check: PurgeWinAssistData

[Code]
function PurgeWinAssistData(): Boolean;
begin
  Result := CompareText(ExpandConstant('{param:PURGEDATA|0}'), '1') = 0;
end;

function ShouldLaunchWinAssist(): Boolean;
begin
  Result := (not WizardSilent) or
    (CompareText(ExpandConstant('{param:UPDATE|0}'), '1') = 0);
end;
