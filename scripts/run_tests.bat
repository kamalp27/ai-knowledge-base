@echo off
echo ==============================================
echo Running Backend Tests with Pytest
echo ==============================================
cd /d "%~dp0\.."

if exist "backend\.venv\Scripts\activate.bat" (
    call backend\.venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python -m pytest backend/tests -v
