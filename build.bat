@echo off
CALL "%userprofile%\miniforge3\Scripts\activate.bat"
CALL conda activate pybnk
pip install pyinstaller

REM "=== RUNNING PYINSTALLER ==="
IF EXIST dist RMDIR /S /Q dist
pyinstaller banks_of_yonder.py --onefile  REM --icon=icon.ico

REM "=== COPYING ADDITIONAL FILES ==="
REM COPY LICENSE dist\
REM COPY README.md dist\
REM COPY icon.ico dist\
REM ROBOCOPY docs dist\docs /E