# Installazione 
Per installare EM2Graphml, eseguire lo script che installerà automaticamente i pacchetti necessari utilizzando PackageManagement. 
 
Dopo l'installazione, lo script avvierà il programma principale che mostrerà uno splash screen. Una volta completato il caricamento, si potrà iniziare ad utilizzarlo. 

# Creazione di standalone per mac windows e linux
- installare  via pip pyinstaller
- installare tutte le dipendenze da requirements.txt
- avviare il comando da dentro la root di EM-Manager:

pyinstaller --onefile --noconsole --add-data 'ui:ui' --add-data 'test:test' --add-data 'parser:parser' --add-data 'template:template' --add-data 'modules:modules' --add-data 'log:log' --add-data 'help:help' --add-data 'icon:icon'  --collect-all "graphviz" --collect-all "networkx" --collect-all "pyvista" --collect-all "pyvistaqt" EDMAtrix2Graphml.py

# Funzioni principali 
EM2Graphml offre diverse funzioni tra cui: 
- Carica dati da un Google Sheet. 
- Aggiorna rapporti. 
- Visualizzatore 3D. 
- Controllo errori. 
 
# Funzioni di controllo errori 
EM2Graphml offre diverse funzioni per controllare gli errori nelle relazioni tra i dati: 
- Controllo duplicati. 
- Controllo esistenza relazioni. 
- Controllo esistenza relazioni inverse. 
- Controllo tipo di relazione. 
 
# Seleziona epoca storica 
EM2Graphml offre anche una funzione che consente di selezionare un'epoca storica da un elenco a discesa. Questo elenco è popolato dai dati nel file CSV o nel foglio Google. 
 
# Salvataggio dei dati 
EM2Graphml consente di salvare i dati in un file CSV o in un foglio Google. I pulsanti "Salva CSV" e "Salva Google" sono collegati alle funzioni corrispondenti. 
 
# Aggiornamento delle relazioni 
EM2Graphml offre due funzioni per aggiornare le relazioni tra i dati: una per i file CSV e una per i fogli Google. 
 
# Finestra Grafica 3D 
La classe GraphWindow crea una finestra che visualizza un grafo 3D. Questa finestra include tre dockwidgets: "Node Info", "Nodi prossimi Info" e "File Multimediali". Ogni dockwidget contiene un QTextEdit o un QWidget che mostra informazioni sul nodo selezionato, sui nodi vicini o sui file multimediali associati al nodo selezionato. 
 
# Classe pyarchinit_Interactive_Matrix 
La classe  pyarchinit_Interactive_Matrix  gestisce la generazione di una matrice interattiva. 
 
# Classe HarrisMatrix 
La classe  HarrisMatrix  gestisce l'esportazione della matrice di Harris in diversi formati. 
 
# Installazione di Graphviz 
Graphviz è necessario per la conversione dei grafici. Si può verificare se Graphviz è installato tramite la funzione  is_graphviz_installed , verificare se la directory bin di Graphviz è nel PATH tramite la funzione  is_graphviz_in_path , installare Graphviz tramite la funzione  install_graphviz , e aggiungere la directory di Graphviz al PATH tramite la funzione  set_graphviz_path .

# Roadmap di sviluppo

## Funzioni da aggiungere a breve

- Lettore GraphML (GraphML to csv) - EMAN
- Create una release su GitHub degli eseguibili per windows, Mac e linux (file fino a 2GB https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)

## Funzioni utili da aggiungere in seconda battuta

- Visualizza foglio elettronico “list of sources”
- Collegamento con Blender via TCP/IP
- Collegamento con Telegram app già in parte esistente
- Collegamento con Google Spreadsheet

