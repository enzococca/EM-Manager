

HELP
================================
.. toctree::
   :maxdepth: 2
   :caption: Contents:

Aiuto per l'uso del EM2Graphml
=============================

ED2Graphml è un'applicazione che consente di convertire  e verificare le relazioni tra i dati in un file CSV o un foglio Google e trasformarli in Graphml per EM Tools.

Avvio del programma
-------------------

1. Scarica il file batch fornito e posizionalo nella cartella desiderata sul tuo computer.
2. Fai doppio clic sul file batch per avviarlo.
3. Lo script del file batch si occuperà di controllare se Python e PyQt5 sono installati.
4. Se Python o PyQt5 non sono installati, lo script utilizzerà PackageManagement per installarli automaticamente.
5. Dopo l'installazione, lo script avvierà il programma principale con uno splash screen.
6. Lo splash screen mostrerà il progresso del caricamento del programma.
7. Una volta completato il caricamento, il programma principale verrà avviato e potrai iniziare ad utilizzarlo.

Funzioni principali
-------------------

- **Carica dati da un Google Sheet:** Questa funzione consente di caricare i dati direttamente da un foglio Google.
- **Aggiorna rapporti:** Questa funzione consente di aggiornare le relazioni tra i dati.
- **Visualizzatore 3D:** Questa funzione consente di visualizzare i dati in un formato 3D.
- **Controllo errori:** Questa funzione consente di controllare gli errori nelle relazioni tra i dati.

Funzioni di controllo errori
----------------------------

EM2Graphml offre diverse funzioni per controllare gli errori nelle relazioni tra i dati:

- **Controllo duplicati:** Questa funzione controlla se ci sono duplicati nella stessa riga.
- **Controllo esistenza relazioni:** Questa funzione controlla se le relazioni esistono.
- **Controllo esistenza relazioni inverse:** Questa funzione controlla se le relazioni inverse esistono.
- **Controllo tipo di relazione:** Questa funzione controlla se il tipo di relazione è corretto.

Seleziona epoca storica
-----------------------

EM2Graphml offre anche una funzione che consente di selezionare un'epoca storica da un elenco a discesa. Questo elenco è popolato dai dati nel file CSV o nel foglio Google.

Salvataggio dei dati
--------------------

EM2Graphml consente di salvare i dati in un file CSV o in un foglio Google. I pulsanti "Salva CSV" e "Salva Google" sono collegati alle funzioni corrispondenti.

Aggiornamento delle relazioni
-----------------------------

EM2Graphml offre due funzioni per aggiornare le relazioni tra i dati: una per i file CSV e una per i fogli Google.

Aggiornamento delle relazioni per i file CSV
--------------------------------------------

Questa funzione apre il file CSV, legge tutte le righe e crea un dizionario per memorizzare le righe per nome. Poi, per ogni riga, controlla il tipo di unità stratigrafica e aggiorna le relazioni corrispondenti. Infine, aggiorna la tabella con i dati aggiornati.

Aggiornamento delle relazioni per i fogli Google
-------------------------------------------------

Questa funzione funziona in modo simile alla funzione per i file CSV, ma invece di aprire un file CSV, apre un foglio Google. Dopo aver letto tutte le righe dal foglio Google, crea un dizionario per memorizzare le righe per nome. Poi, per ogni riga, controlla il tipo di unità stratigrafica e aggiorna le relazioni corrispondenti. Infine, aggiorna la tabella con i dati aggiornati.

Nota:
-----
Per entrambe le funzioni, se l'unità stratigrafica è di tipo 'property', 'document', 'combiner' o 'extractor', vengono aggiornate le relazioni 'properties_ant' e 'properties_post'. Se l'unità stratigrafica è di tipo 'contemporaneo', viene aggiornata la relazione 'contemporaneo'. In tutti gli altri casi, vengono aggiornate le relazioni 'anteriore' e 'posteriore'.

Aggiornamento delle relazioni nel DataFrame
-------------------------------------------

EM2Graphml offre una funzione per aggiornare le relazioni nel DataFrame. Questa funzione legge i dati dalla QTableWidget, aggiorna i rapporti nel DataFrame e mostra eventuali errori nel dock widget.

Visualizzazione delle modifiche
--------------------------------

EM2Graphml offre una funzione per mostrare le differenze tra le vecchie e le nuove righe. Questa funzione può essere utilizzata per verificare le modifiche apportate ai dati.

Salvataggio delle modifiche
---------------------------

EM2Graphml offre una funzione per chiedere all'utente se vuole salvare le modifiche. Se l'utente decide di salvare le modifiche, queste verranno salvate nel file CSV e il file verrà ricaricato.

Visualizzazione del dialogo dell'epoca
--------------------------------------

EM2Graphml offre una funzione per mostrare un dialogo dell'epoca quando viene fatto doppio clic su una cella nella colonna "Epoca". Questa funzione crea un'istanza di EpochDialog e mostra il dialogo all'utente.

Salvataggio dei dati in un file CSV o in un foglio Google
----------------------------------------------------------

EM2Graphml offre due funzioni per salvare i dati: una per i file CSV e una per i fogli Google. Queste funzioni leggono i dati dalla QTableWidget, creano un nuovo DataFrame con questi dati e salvano il DataFrame nel file CSV o nel foglio Google.

Aggiornamento e ripristino dei dati CSV
---------------------------------------

EM2Graphml offre due funzioni per aggiornare e ripristinare i dati CSV. La funzione di aggiornamento aggiorna il DataFrame originale con i dati della QTableWidget. La funzione di ripristino ripristina i dati della QTableWidget al DataFrame originale.

Ottenere il DataFrame corrente
------------------------------

EM2Graphml offre una funzione per ottenere il DataFrame corrente dalla QTableWidget. Questa funzione può essere utilizzata per ottenere i dati attualmente visualizzati nella QTableWidget.

Aggiorna Relazioni
~~~~~~~~~~~~~~~~~~

Questa funzione legge i dati dal QTableWidget e li aggiunge a un nuovo DataFrame. Successivamente aggiorna le relazioni nel DataFrame. Se ci sono delle modifiche, chiederà all'utente se desidera salvare le modifiche e, se necessario, salverà il file CSV.

Aggiorna Relazioni nel DataFrame
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Questa funzione prende un DataFrame come input, aggiorna le relazioni nel DataFrame e restituisce il DataFrame aggiornato insieme al nuovo header.

Mostra Cambiamenti
~~~~~~~~~~~~~~~~~~

Questa funzione stampa le differenze tra le righe vecchie e nuove. Se una riga è cambiata, verrà stampata la vecchia riga e la nuova riga.

Chiedi di Salvare le Modifiche
-------------------------------

Questa funzione chiede all'utente se desidera salvare le modifiche. Se l'utente sceglie di salvare le modifiche, le modifiche verranno salvate nel file CSV di output.

Finestra Grafica 3D
~~~~~~~~~~~~~~~~~~~

La classe GraphWindow crea una finestra che visualizza un grafo 3D. Questa finestra include tre dockwidgets: "Node Info", "Nodi prossimi Info" e "File Multimediali". Ogni dockwidget contiene un QTextEdit o un QWidget che mostra informazioni sul nodo selezionato, sui nodi vicini o sui file multimediali associati al nodo selezionato.

La funzione d_graph legge un file graphml, recupera le coordinate x, y per ogni nodo e crea un plot 3D del grafo. Se esistono modelli 3D che corrispondono alle descrizioni dei nodi, questi vengono caricati e visualizzati come oggetti 3D nel plot. In caso contrario, viene visualizzata un'immagine o una sfera 3D.

La funzione callback viene eseguita quando si clicca su un punto nel plot 3D. Calcola la distanza tra il punto selezionato e ogni nodo nel grafo, trova il nodo più vicino e mostra le informazioni di questo nodo nel QTextEdit. Se il nodo ha un file multimediale associato, questo viene visualizzato nel QWidget.

La funzione eventFilter gestisce gli eventi del mouse per avviare, mettere in pausa e interrompere la riproduzione di un video quando si clicca con il mouse sul QWidget che mostra il video.

Classe pyarchinit_Interactive_Matrix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La classe `pyarchinit_Interactive_Matrix` gestisce la generazione di una matrice interattiva.

Il metodo `__init__` inizializza la classe e imposta le variabili `DATA_LIST` e `ID_US_DICT`.

Il metodo `csv_connect` si occupa di connettersi al file CSV.

Il metodo `urlify` converte una stringa in un formato URL-friendly, sostituendo gli spazi con underscore.

Il metodo `generate_matrix` genera la matrice a partire dai dati forniti. Vengono utilizzate diverse funzioni per elaborare e organizzare i dati.

Classe HarrisMatrix
~~~~~~~~~~~~~~~~~~~~

La classe `HarrisMatrix` gestisce l'esportazione della matrice di Harris in diversi formati.

Il metodo `__init__` inizializza la classe e imposta le variabili `sequence`, `conteporene`, `property` e `periodi`.

Il metodo `export_matrix_2` genera la matrice di Harris utilizzando la libreria Graphviz. Vengono creati diversi sottografi per rappresentare le relazioni tra i dati.

Installazione di Graphviz
~~~~~~~~~~~~~~~~~~~~~~~~~

Il programma verifica se Graphviz è installato e se è nel PATH del sistema operativo. Graphviz è necessario per la conversione dei grafici.

La funzione `is_graphviz_installed` esegue il comando "dot -V" per verificare se Graphviz è installato. Se il comando viene eseguito con successo, la funzione restituisce True, altrimenti restituisce False.

La funzione `is_graphviz_in_path` verifica se la directory bin di Graphviz è nel PATH del sistema operativo. Se lo è, la funzione restituisce True, altrimenti restituisce False.

La funzione `install_graphviz` mostra un messaggio di avviso se Graphviz non è installato. Il messaggio suggerisce come installare Graphviz a seconda del sistema operativo.

La funzione `set_graphviz_path` mostra un messaggio di avviso se Graphviz non è nel PATH del sistema operativo. Il messaggio suggerisce di aggiungere la directory di Graphviz al PATH.

La funzione `check_graphviz` chiama le funzioni `is_graphviz_installed` e `is_graphviz_in_path`, e mostra un messaggio appropriato a seconda dei risultati. Se Graphviz è installato e nel PATH, mostra un messaggio che dice "Graphviz è installato e pronto all'uso".
