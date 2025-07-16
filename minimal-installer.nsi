; DiPeO Minimal Installer
; Simple installer that packages backend and frontend executables

!include "MUI2.nsh"

; General Configuration
Name "DiPeO"
OutFile "DiPeO-Setup-Minimal.exe"
InstallDir "$PROGRAMFILES64\DiPeO"
InstallDirRegKey HKLM "Software\DiPeO" "Install_Dir"
RequestExecutionLevel admin

; UI Configuration
!define MUI_ABORTWARNING
!define MUI_ICON "apps\desktop\src-tauri\icons\icon.ico"
!define MUI_UNICON "apps\desktop\src-tauri\icons\icon.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "apps\desktop\src-tauri\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installer Section
Section "DiPeO Core Files" SEC01
    SetOutPath "$INSTDIR"
    
    ; Copy executables
    File "apps\server\dist\dipeo-server.exe"
    File "apps\web\dist\dipeo-frontend.exe"
    
    ; Copy frontend build files
    SetOutPath "$INSTDIR\web-dist"
    File /r "apps\web\dist\*.*"
    SetOutPath "$INSTDIR"
    
    ; Copy launcher script (use the installed version)
    File /oname=launch-dipeo.bat "launch-dipeo-installed.bat"
    
    ; Copy icon
    CreateDirectory "$INSTDIR\icons"
    File /oname=icons\icon.ico "apps\desktop\src-tauri\icons\icon.ico"
    
    ; Create required directories
    CreateDirectory "$INSTDIR\files"
    CreateDirectory "$INSTDIR\files\diagrams"
    CreateDirectory "$INSTDIR\files\results"
    CreateDirectory "$INSTDIR\files\conversation_logs"
    CreateDirectory "$INSTDIR\files\uploads"
    CreateDirectory "$INSTDIR\files\prompts"
    
    ; Write registry keys
    WriteRegStr HKLM "Software\DiPeO" "Install_Dir" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DiPeO" "DisplayName" "DiPeO"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DiPeO" "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DiPeO" "DisplayIcon" "$INSTDIR\icons\icon.ico"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DiPeO" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DiPeO" "NoRepair" 1
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; Start Menu Shortcuts Section
Section "Start Menu Shortcuts" SEC02
    CreateDirectory "$SMPROGRAMS\DiPeO"
    
    ; Create shortcut for launcher
    CreateShortCut "$SMPROGRAMS\DiPeO\DiPeO.lnk" "$INSTDIR\launch-dipeo.bat" "" "$INSTDIR\icons\icon.ico" 0
    
    ; Create individual shortcuts with working directory set
    CreateShortCut "$SMPROGRAMS\DiPeO\DiPeO Backend Server.lnk" "$INSTDIR\dipeo-server.exe" "" "$INSTDIR\icons\icon.ico" 0 SW_SHOWNORMAL "$INSTDIR"
    CreateShortCut "$SMPROGRAMS\DiPeO\DiPeO Frontend.lnk" "$INSTDIR\dipeo-frontend.exe" "" "$INSTDIR\icons\icon.ico" 0 SW_SHOWNORMAL "$INSTDIR"
    
    ; Uninstall shortcut
    CreateShortCut "$SMPROGRAMS\DiPeO\Uninstall DiPeO.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
SectionEnd

; Desktop Shortcut Section
Section "Desktop Shortcut" SEC03
    CreateShortCut "$DESKTOP\DiPeO.lnk" "$INSTDIR\launch-dipeo.bat" "" "$INSTDIR\icons\icon.ico" 0
SectionEnd

; Uninstaller Section
Section "Uninstall"
    ; Remove files
    Delete "$INSTDIR\dipeo-server.exe"
    Delete "$INSTDIR\dipeo-frontend.exe"
    Delete "$INSTDIR\launch-dipeo.bat"
    Delete "$INSTDIR\icons\icon.ico"
    Delete "$INSTDIR\uninstall.exe"
    
    ; Remove directories (only if empty)
    RMDir "$INSTDIR\icons"
    RMDir "$INSTDIR\files\diagrams"
    RMDir "$INSTDIR\files\results"
    RMDir "$INSTDIR\files\conversation_logs"
    RMDir "$INSTDIR\files\uploads"
    RMDir "$INSTDIR\files\prompts"
    RMDir "$INSTDIR\files"
    RMDir "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$SMPROGRAMS\DiPeO\*.lnk"
    RMDir "$SMPROGRAMS\DiPeO"
    Delete "$DESKTOP\DiPeO.lnk"
    
    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DiPeO"
    DeleteRegKey HKLM "Software\DiPeO"
SectionEnd

; Section Descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC01} "Core DiPeO files including backend server and frontend launcher"
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC02} "Create shortcuts in the Start Menu"
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC03} "Create a shortcut on the Desktop"
!insertmacro MUI_FUNCTION_DESCRIPTION_END