@echo off
echo ==============================================
echo Starting AI Knowledge Base FastAPI Backend
echo ==============================================
cd /d "%~dp0\.."

REM Activate virtual environment if present
if exist "backend\.venv\Scripts\activate.bat" (
    call backend\.venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
