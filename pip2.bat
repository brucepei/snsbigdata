@echo off
if "%1" equ "" (
	echo Need pip arguments!
	exit /b
)
rem echo pip %*
if "%1" equ "install" (
	venv2\scripts\pip.exe %* -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
) else (
	venv2\scripts\pip.exe %*
)