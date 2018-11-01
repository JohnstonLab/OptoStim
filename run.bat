@echo off

IF NOT EXIST python\Scripts\activate.bat (
	COLOR C
	echo Please run the setup batch file located in the same directory first. The virtual environment python is not setup.
) ELSE (
	call python\Scripts\activate.bat
	python optostim\main.py
)

pause