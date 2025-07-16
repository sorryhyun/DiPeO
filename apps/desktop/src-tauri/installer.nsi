!include MUI2.nsh
!include FileFunc.nsh
!include LogicLib.nsh
!include nsDialogs.nsh
!include WinMessages.nsh

; Modern UI Settings
!define MUI_ICON "..\..\..\..\icons\icon.ico"
!define MUI_UNICON "..\..\..\..\icons\icon.ico"
; PNG not supported for header images - commenting out
;!define MUI_HEADERIMAGE
;!define MUI_HEADERIMAGE_RIGHT
;!define MUI_HEADERIMAGE_BITMAP "..\..\..\..\icons\icon.png"

Name "DiPeO"
OutFile "..\..\bundle\nsis\DiPeO_0.1.0_x64-setup.exe"
Unicode True
InstallDir "$PROGRAMFILES64\DiPeO"
RequestExecutionLevel admin

; Version Info
VIProductVersion "0.1.0.0"
VIAddVersionKey "ProductName" "DiPeO"
VIAddVersionKey "CompanyName" "DiPeO Team"
VIAddVersionKey "FileDescription" "DiPeO Installer"
VIAddVersionKey "FileVersion" "0.1.0"

; Variables
Var NodeInstalled
Var PythonInstalled
Var DownloadProgress
Var InstallStatus

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\..\..\..\..\..\..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
Page custom DependencyCheck DependencyCheckLeave
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; Dependency Check Page
Function DependencyCheck
    nsDialogs::Create 1018
    Pop $0
    
    ${NSD_CreateLabel} 0 0 100% 20u "Checking system dependencies..."
    Pop $0
    
    ${NSD_CreateProgressBar} 0 30u 100% 12u ""
    Pop $DownloadProgress
    
    ${NSD_CreateLabel} 0 50u 100% 40u ""
    Pop $InstallStatus
    
    ; Check Node.js
    nsExec::ExecToStack 'cmd /c "node --version"'
    Pop $0
    Pop $1
    ${If} $0 == 0
        StrCpy $NodeInstalled "1"
        ${NSD_SetText} $InstallStatus "✓ Node.js found: $1"
    ${Else}
        StrCpy $NodeInstalled "0"
        ${NSD_SetText} $InstallStatus "✗ Node.js not found - will be installed"
    ${EndIf}
    
    ; Check Python
    nsExec::ExecToStack 'cmd /c "python --version"'
    Pop $0
    Pop $1
    ${If} $0 == 0
        StrCpy $PythonInstalled "1"
        ${NSD_SetText} $InstallStatus "$InstallStatus$\r$\n✓ Python found: $1"
    ${Else}
        StrCpy $PythonInstalled "0"
        ${NSD_SetText} $InstallStatus "$InstallStatus$\r$\n✗ Python not found - will be installed"
    ${EndIf}
    
    nsDialogs::Show
FunctionEnd

Function DependencyCheckLeave
FunctionEnd

; Download function with progress
Function DownloadWithProgress
    Pop $R0 ; URL
    Pop $R1 ; Local file
    Pop $R2 ; Description
    
    download_start:
    DetailPrint "Downloading $R2..."
    NSISdl::download /TIMEOUT=30000 "$R0" "$R1"
    Pop $0
    
    ${If} $0 != "success"
        DetailPrint "Download failed: $0"
        MessageBox MB_RETRYCANCEL "Failed to download $R2. Retry?" IDRETRY download_start
        Abort
    ${EndIf}
FunctionEnd

Section "DiPeO Core" SecMain
    SectionIn RO ; Required section
    
    SetOutPath "$INSTDIR"
    
    ; Install dependencies if needed
    ${If} $NodeInstalled == "0"
        DetailPrint "Installing Node.js..."
        Push "Installing Node.js"
        Push "$TEMP\node-installer.msi"
        Push "https://nodejs.org/dist/v20.11.0/node-v20.11.0-x64.msi"
        Call DownloadWithProgress
        
        DetailPrint "Running Node.js installer (this may take a few minutes)..."
        nsExec::ExecToLog 'msiexec /i "$TEMP\node-installer.msi" /qn ADDLOCAL=ALL'
        Pop $0
        ${If} $0 != 0
            MessageBox MB_OK "Node.js installation failed. Please install manually from https://nodejs.org"
            Abort
        ${EndIf}
        Delete "$TEMP\node-installer.msi"
        
        ; Add Node to PATH for current process
        ReadEnvStr $0 PATH
        StrCpy $0 "$0;C:\Program Files\nodejs"
        System::Call 'Kernel32::SetEnvironmentVariable(t "PATH", t r0)'
    ${EndIf}
    
    ${If} $PythonInstalled == "0"
        DetailPrint "Installing Python..."
        Push "Installing Python"
        Push "$TEMP\python-installer.exe"
        Push "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
        Call DownloadWithProgress
        
        DetailPrint "Running Python installer (this may take a few minutes)..."
        nsExec::ExecToLog '"$TEMP\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0'
        Pop $0
        ${If} $0 != 0
            MessageBox MB_OK "Python installation failed. Please install manually from https://python.org"
            Abort
        ${EndIf}
        Delete "$TEMP\python-installer.exe"
        
        ; Add Python to PATH for current process
        ReadEnvStr $0 PATH
        StrCpy $0 "$0;C:\Program Files\Python311;C:\Program Files\Python311\Scripts"
        System::Call 'Kernel32::SetEnvironmentVariable(t "PATH", t r0)'
    ${EndIf}
    
    ; Copy main executable
    DetailPrint "Installing DiPeO executable..."
    File "..\..\dipeo-desktop.exe"
    
    ; Copy bundled backend executable
    DetailPrint "Installing backend server..."
    File "..\..\dipeo-server.exe"
    
    ; Copy web app dist files
    DetailPrint "Installing web application files..."
    CreateDirectory "$INSTDIR\web"
    SetOutPath "$INSTDIR\web"
    File /r "..\..\..\..\..\web\dist\*.*"
    
    ; Copy necessary config files
    SetOutPath "$INSTDIR"
    File "..\..\..\..\..\..\..\requirements.txt"
    
    ; Create app data directory
    CreateDirectory "$APPDATA\DiPeO"
    
    ; Install any remaining Python packages (for CLI if needed)
    DetailPrint "Installing Python packages..."
    nsExec::ExecToLog 'cmd /c "pip install -r "$INSTDIR\requirements.txt""'
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\DiPeO"
    CreateShortcut "$SMPROGRAMS\DiPeO\DiPeO.lnk" "$INSTDIR\dipeo-desktop.exe"
    CreateShortcut "$SMPROGRAMS\DiPeO\Uninstall DiPeO.lnk" "$INSTDIR\Uninstall.exe"
    CreateShortcut "$DESKTOP\DiPeO.lnk" "$INSTDIR\dipeo-desktop.exe"
    
    ; Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Register uninstall information
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DiPeO" "DisplayName" "DiPeO"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DiPeO" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DiPeO" "DisplayIcon" "$INSTDIR\dipeo-desktop.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DiPeO" "Publisher" "DiPeO Team"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DiPeO" "DisplayVersion" "0.1.0"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DiPeO" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DiPeO" "NoRepair" 1
    
    ; Refresh environment variables
    SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000
    
    DetailPrint "Installation complete!"
SectionEnd

Section "Uninstall"
    ; Kill running processes
    nsExec::ExecToLog 'taskkill /F /IM dipeo-desktop.exe'
    nsExec::ExecToLog 'taskkill /F /IM dipeo-server.exe'
    
    ; Remove files
    Delete "$INSTDIR\dipeo-desktop.exe"
    Delete "$INSTDIR\dipeo-server.exe"
    Delete "$INSTDIR\requirements.txt"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir /r "$INSTDIR\web"
    RMDir "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$SMPROGRAMS\DiPeO\DiPeO.lnk"
    Delete "$SMPROGRAMS\DiPeO\Uninstall DiPeO.lnk"
    RMDir "$SMPROGRAMS\DiPeO"
    Delete "$DESKTOP\DiPeO.lnk"
    
    ; Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DiPeO"
    
    ; Ask about user data
    MessageBox MB_YESNO "Remove user data and settings?" IDNO NoRemoveUserData
        RMDir /r "$APPDATA\DiPeO"
    NoRemoveUserData:
SectionEnd