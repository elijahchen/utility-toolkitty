@echo off
REM Check if the script is running as administrator
NET SESSION >NUL 2>&1
IF %ERRORLEVEL% EQU 0 (
	REM Script is running as administrator
	goto agreement
) ELSE (
	REM Script is not running as administrator
	echo Please run this script as an administrator.
	pause
	exit
)

:agreement
cls
echo By running this script, you acknowledge that you have read and agree to the terms and conditions.
echo This script is only intended to be used on non-critical systems.
echo Using it elsewhere may not provide the same results, and no support will be provided.
echo.
set /p agree=Type 'y' and press Enter to continue: 

if /i "%agree%"=="y" (
	goto menu
) else (
	echo You did not agree to the terms and conditions. Exiting script.
	pause
	exit
)

:menu
cls
echo Please select an option:
echo 1. Reset current user's password
echo 2. Validate Windows license key
echo 3. Run traceroute on a domain
echo 4. Run systeminfo
echo 5. Expand advanced menu
echo 6. Exit
echo.

set /p choice=Enter your choice (1-6):

if "%choice%"=="1" goto reset_password
if "%choice%"=="2" goto validate_license
if "%choice%"=="3" goto traceroute
if "%choice%"=="4" goto run_systeminfo
if "%choice%"=="5" goto advanced_menu
if "%choice%"=="6" goto end

echo Invalid choice, please try again.
pause
goto menu

:reset_password
net user %username% *
goto menu

:validate_license
slmgr /ato
pause
goto menu

:traceroute
set /p domain=Enter the domain to traceroute:
tracert %domain%
pause
goto menu

:run_systeminfo
systeminfo
pause
goto menu

:advanced_menu
cls
echo WARNING: Proceed with caution. Advanced menu options may have unintended consequences.
echo.
echo Advanced menu options:
echo 1. List all entries in the host file
echo 2. Add entry to host file
echo 3. Remove entry from host file
echo 4. Reset network settings
echo 5. Flush DNS cache
echo 6. Return to main menu
echo.

set /p advanced_choice=Enter your choice (1-5):

if "%advanced_choice%"=="1" goto list_host_entries
if "%advanced_choice%"=="2" goto add_host_entry
if "%advanced_choice%"=="3" goto remove_host_entry
if "%advanced_choice%"=="4" goto reset_network_settings
if "%advanced_choice%"=="5" goto flush_dns
if "%advanced_choice%"=="6" goto menu

echo Invalid choice, please try again.
pause
goto advanced_menu

:flush_dns
echo Flushing DNS cache...
ipconfig /flushdns
echo DNS cache flushed successfully.
pause
goto advanced_menu

:reset_network_settings
echo Resetting network settings...
netsh winsock reset
netsh int ip reset
ipconfig /release
ipconfig /renew
echo Network settings reset successfully.
pause
goto advanced_menu

:list_host_entries
type %windir%\System32\drivers\etc\hosts
pause
goto advanced_menu

:add_host_entry
set /p ip=Enter the IP address:
set /p domain=Enter the domain:
echo %ip% %domain% >> %windir%\System32\drivers\etc\hosts
echo Host entry added successfully.
pause
goto advanced_menu

:remove_host_entry
set /p entry=Enter the host entry to remove (e.g., 127.0.0.1 example.com):
findstr /v "%entry%" %windir%\System32\drivers\etc\hosts > %windir%\System32\drivers\etc\hosts.tmp
move /y %windir%\System32\drivers\etc\hosts.tmp %windir%\System32\drivers\etc\hosts > nul
echo Host entry removed successfully.
pause
goto advanced_menu

:end