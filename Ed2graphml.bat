@echo off


REM Crea un ambiente virtuale in Python se non esiste già
if not exist ENV (
    python -m venv ENV
)

REM Attiva l'ambiente virtuale
call ENV\Scripts\activate.bat

REM Installa le dipendenze necessarie usando pip all'interno dell'ambiente virtuale e registra l'output nel log dello splash screen
python -m pip install --upgrade pip > temp.log 2>&1
python -m pip install -r requirements.txt >> temp.log 2>&1
python EDMatrix2Graphml.py

REM Disattiva l'ambiente virtuale
deactivate