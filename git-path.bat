@echo off

setlocal enabledelayedexpansion

rem Read the Git for Windows installation path from the Registry.
for %%k in (HKCU HKLM) do (
    for %%w in (\ \Wow6432Node\) do (
        for /f "skip=2 delims=: tokens=1*" %%a in ('reg query "%%k\SOFTWARE%%wMicrosoft\Windows\CurrentVersion\Uninstall\Git_is1" /v InstallLocation 2^> nul') do (
            for /f "tokens=3" %%z in ("%%a") do (
                set GIT=%%z:%%b
                echo Found Git at !GIT!
                goto FOUND
            )
        )
    )
)

goto NOT_FOUND

:FOUND

rem Make sure Bash is in PATH (for running scripts).
REM set PATH=%GIT%bin;%PATH%
REM @set Path_=%GIT%bin;
REM for,/f,"skip=4 tokens=1,2,*",%%a,in,('reg query "HKEY_LOCAL_MACHINE\SYSTEM\ControlSet001\Control\Session Manager\Environment" /v Path'),do,(
    REM @set PathAll_=%%c
    REM )
    REM echo %PathAll_%|find /i "%Path_%" && set IsNull=true|| set IsNull=false
    REM if not %IsNull%==true (
        REM reg add "HKEY_LOCAL_MACHINE\SYSTEM\ControlSet001\Control\Session Manager\Environment" /v Path /t REG_EXPAND_SZ /d "%PathAll_%;%Path_%" /f
        REM )
set ADDpath=%GIT%bin;
reg query "HKEY_LOCAL_MACHINE\SYSTEM\ControlSet001\Control\Session Manager\Environment" /v "Path"|find /i "%ADDpath%"||(reg add "HKEY_LOCAL_MACHINE\SYSTEM\ControlSet001\Control\Session Manager\Environment" /v PATH /t REG_EXPAND_SZ /d "%ADDpath%%PATH%" /f)

:NOT_FOUND
