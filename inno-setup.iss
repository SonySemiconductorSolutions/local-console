; Inno Setup Script for generating Windows Installer of Local Console.

#define MyAppName "Local Console"
#define MyAppPublisher "Sony Semiconductor Solutions Corporation"
#define MyAppExeName "local-console.exe"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".myp"
#define MyAppCanonical StringChange(MyAppName, " ", "")
#define MyAppAssocKey MyAppCanonical + MyAppAssocExt
; Define the path to the version file
#define FileHandle = FileOpen("local-console\VERSION")
#define VersionString = FileRead(FileHandle)
#if FileHandle
  #expr FileClose(FileHandle)
#endif

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{63A38119-1103-4ED1-AD9B-0D873FB090B5}}
AppName={#MyAppName}
AppVersion={#VersionString}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppCanonical}
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
OutputBaseFilename=local-console-setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
AlwaysRestart=no
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "local-console\windows\*";  DestDir: "{tmp}\local-console"; Flags: recursesubdirs
Source: "local_console*.whl";  DestDir: "{tmp}\local-console";

[Run]
StatusMsg: "Installing Local Console..."; Filename: "powershell.exe"; Parameters: "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser; {tmp}\\local-console\\install.ps1 -AppInstallPath ""{app}"" -WheelPath $((Get-ChildItem {tmp}\\local-console\\local_console*.whl).FullName)"; Flags: waituntilterminated;

[UninstallDelete]
Type: files; Name: "{userdesktop}\Local Console.lnk"
Type: filesandordirs; Name: "{app}"
Type: filesandordirs; Name: "{userappdata}\local-console"
