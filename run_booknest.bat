@echo off
echo =====================================
echo        BOOKNEST SETUP AND RUN
echo =====================================
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Could not install dependencies. Make sure Python is installed.
  pause
  exit /b 1
)
echo.
echo Starting BookNest...
py app.py
pause
