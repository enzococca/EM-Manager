#!/bin/bash

# Crea un ambiente virtuale in Python
python3 -m venv ENV

# Attiva l'ambiente virtuale
source ENV/bin/activate

# Installa le dipendenze necessarie usando pip
pip install --upgrade pip
pip install -r requirements.txt
python splash.py
# Avvia il programma
python EDMatrix2Graphml.py

# Disattiva l'ambiente virtuale
deactivate
