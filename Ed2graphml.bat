@echo off

REM Controlla se Python è installato
where python >nul 2>&1
if %errorlevel% neq 0 (
    REM Python non è installato, quindi lo installa utilizzando PackageManagement
    echo Python non trovato, lo sto installando...
    powershell -command "Install-Package python"
)

REM Controlla se PyQt5 è installato
python -c "import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    REM PyQt5 non è installato, quindi lo installa utilizzando PackageManagement
    echo PyQt5 non trovato, lo sto installando...
    powershell -command "Install-Package pyqt5"
)

REM Avvia il programma principale con lo splash screen
start "" /B python splash.py


REM Crea un ambiente virtuale in Python se non esiste già
if not exist ENV (
    python -m venv ENV
)

REM Attiva l'ambiente virtuale
call ENV\Scripts\activate.bat

REM Installa le dipendenze necessarie usando pip all'interno dell'ambiente virtuale e registra l'output nel log dello splash screen
python -m pip install --upgrade pip > temp.log 2>&1
python -m pip install -r requirements.txt >> temp.log 2>&1

REM Disattiva l'ambiente virtuale
deactivate