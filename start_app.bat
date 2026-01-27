@echo off
echo Starting NMN Investment Engine...

if not exist venv\Scripts\activate.bat (
    echo Error: Virtual environment not found. Please run install.bat first.
    pause
    exit /b 1
)

:: Activate venv and run app
call venv\Scripts\activate.bat
python app.py

pause
