@echo off

IF EXIST python (
	echo Python virtual directory exists, activating virtual environment...
) ELSE (
	COLOR 6
	echo Python virtual directory does not exist. Creating...
	python -m venv python
) 

COLOR 7

call python\Scripts\activate.bat

echo Installing from requirements.txt to virtual python environment...

pip install -r requirements.txt

call deactivate

REM Wait for user input, otherwise console window instantly closes.
pause


