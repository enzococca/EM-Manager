API
================================
.. toctree::
   :maxdepth: 2
   :caption: Indice:

La classe `EpochDialog`
-----------------------

La classe `EpochDialog` rappresenta una finestra di dialogo che consente all'utente di selezionare un'epoca storica da una lista di opzioni.

.. autoclass:: EpochDialog
   :members:
   :undoc-members:


La classe `UnitDialog`
----------------------

La classe `UnitDialog` rappresenta una finestra di dialogo che consente all'utente di selezionare un'unità di misura da una lista di opzioni.

.. autoclass:: UnitDialog
   :members:
   :undoc-members:


La classe `CSVMapper`
---------------------

La classe `CSVMapper` rappresenta la finestra principale dell'applicazione.

.. autoclass:: CSVMapper
   :members:
   :undoc-members:


Funzioni
--------

La funzione `check_relation_exists`
--------------------------------------------------
.. autofunction:: check_relation_exists
   :noindex:

La funzione `check_inverse_relation_exists`
----------------------------------------------------------
.. autofunction:: check_inverse_relation_exists
   :noindex:

La funzione `check_relation_type`
------------------------------------------------
.. autofunction:: check_relation_type
   :noindex:

Google Sheet". Una volta caricati i dati, vengono visualizzati nella tabella dei dati.

L'utente può eseguire diverse azioni sulla tabella dei dati, come l'aggiunta, l'eliminazione o la modifica di righe e colonne. È anche possibile ordinare i dati in base a una colonna specifica.

La classe `EpochDialog` e `UnitDialog` forniscono finestre di dialogo per la selezione delle epoche storiche e delle unità di misura.

Le funzioni `show_epoch_dialog` e `show_unit_dialog` vengono chiamate quando l'utente fa doppio clic su una cella nella colonna "Epoca" o "Unità" della tabella dei dati. Queste funzioni mostrano le finestre di dialogo delle epoche storiche e delle unità di misura, rispettivamente, e consentono all'utente di selezionare un'epoca o un'unità dalla combobox.

Le funzioni `on_google_sheet_action_triggered`, `save_csv` e `save_google` gestiscono il salvataggio dei dati su Google Sheets o su file CSV.

La funzione `update_relations` gestisce l'aggiornamento delle relazioni tra le unità stratigrafiche presenti nella tabella dei dati. Questa funzione legge il file CSV o il foglio di calcolo Google Sheets, aggiorna le relazioni tra le unità stratigrafiche e restituisce un DataFrame contenente le righe aggiornate.

La funzione `update_relationships_in_dataframe` aggiorna le relazioni tra le unità stratigrafiche presenti in un DataFrame specifico.

Le funzioni `show_changes` e `ask_to_save_changes` vengono chiamate quando l'utente apporta modifiche alla tabella dei dati e deve decidere se salvare le modifiche su un file CSV.

Le variabili `data_table`, `epochs_df`, `unit_df`, `spreadsheet_id`, `df`, `data_fields`, `df2` e `data_fields2` vengono utilizzate come contenitori per i dati.
("epoca index")

```
                rapporti_idx = header.index("rapporti")

                # Read the data rows
                for row in reader:
                #Split the rapporti column into a list of strings
                rapporti = row[rapporti_idx].split(",")

                #Create a dictionary of ID-US key-value pairs
                id_us_dict[row[us_idx]] = row[unita_tipo_idx]

                #Add the row data to the data list
                data_list.append([row[us_idx], row[unita_tipo_idx], row[descrizione_idx], row[epoca_idx], row[e_idx], rapporti])

            # Convert the data list to a pandas DataFrame and populate the data table
            self.df = pd.DataFrame(data_list, columns=header)
            self.populate_table()

            return data_list, id_us_dict

        except IOError as e:
            print(f"Error reading the file: {e}")
            raise e

    def populate_table(self):
        """
        Populates the data table with the data from the pandas DataFrame.

        """
        self.data_table.setRowCount(len(self.df.index))
        self.data_table.setColumnCount(len(self.df.columns))
        self.data_table.setHorizontalHeaderLabels(self.df.columns)

        for row in range(len(self.df.index)):
            for col in range(len(self.df.columns)):
                item = QTableWidgetItem(str(self.df.iloc[row, col]))
                self.data_table.setItem(row, col, item)

    def get_current_dataframe(self):
        """
        Returns a pandas DataFrame containing the data from the data table.

        Returns:
            DataFrame: A pandas DataFrame containing the data from the data table.

        """
        headers = [self.data_table.horizontalHeaderItem(i).text() for i in range(self.data_table.columnCount())]
        data = [[self.data_table.item(row, col).text() for col in range(self.data_table.columnCount())] for row in range(self.data_table.rowCount())]
        return pd.DataFrame(data, columns=headers)

    def transform_data_google(self, file_buffer, output_buffer):
        """
        Transforms the data in a CSV file to a format compatible with Google Sheets.

        Args:
            file_buffer (BytesIO): A buffer containing the CSV file data.
            output_buffer (BytesIO): A buffer where the transformed data will be written.

        """
        data = pd.read_csv(file_buffer)

        # Convert the "rapporti" column to a list
        data['rapporti'] = data['rapporti'].apply(lambda x: x.split(","))

        # Convert the data to a format compatible with Google Sheets
        data['properties_ant'] = data.apply(lambda row: {row['anteriore']: row['properties_ant']}, axis=1)
        data['properties_post'] = data.apply(lambda row: {row['posteriore']: row['properties_post']}, axis=1)
        data = data.groupby(['nome us', 'tipo', 'descrizione', 'epoca', 'epoca index', 'contemporaneo', 'rapporti'])[['properties_ant', 'properties_post']].apply(lambda x: x.to_dict('list')).reset_index(name='properties')

        # Write the transformed data to the output buffer
        data.to_csv(output_buffer, index=False)

    def update_csv(self, data_list):
        """
        Updates the data in the pandas DataFrame and the data table.

        Args:
            data_list (list): A list of lists containing the updated data.

        """
        # Convert the data list to a pandas DataFrame and update the original DataFrame
        self.df = pd.DataFrame(data_list, columns=self.df.columns)

        # Repopulate the data table
        self.populate_table()

    def rollback_csv(self):
        """
        Rolls back the data in the data table to the original values from the CSV file.

        """
        # Reload the original CSV file and repopulate the data table
        data_list, id_us_dict = self.load_csv(self.filename)
        self.populate_table()
```
.. _documentazione:

Documentazione
==============

Questo modulo contiene diverse classi e funzioni utilizzate per controllare la coerenza dei dati presenti in un file CSV.

Funzioni
---------

``check_file_consistency(csv_file: str, output_file: str) -> Tuple[List[List[str]], Dict[str, Dict[str, str]]]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Questa funzione legge i dati dal file CSV specificato, controlla la coerenza tra le relazioni degli *Unità Stratigrafiche* (US) e restituisce i dati letti e un dizionario di ID per US.

Argomenti:
- ``csv_file``: il percorso del file CSV contenente i dati da leggere.
- ``output_file``: il percorso del file di output contenente gli errori di coerenza (se presenti).

Restituisce:
- ``data_list``: una lista di liste contenente i dati letti dal file CSV.
- ``id_us_dict``: un dizionario di ID per US letto dal file CSV.

``check_consistency(csv_file: str, output_file: str)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Questa funzione controlla la coerenza tra le relazioni degli *Unità Stratigrafiche* (US) presenti nel file CSV specificato e scrive i risultati nel file di output specificato.

Argomenti:
- ``csv_file``: il percorso del file CSV contenente i dati da leggere.
- ``output_file``: il percorso del file di output contenente gli errori di coerenza (se presenti).

``show_errors_in_dock_widget(text: str)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Questa funzione mostra il testo specificato nel widget a scomparsa.

Argomenti:
- ``text``: il testo da mostrare.

``check_consistency_google()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Questa funzione controlla la coerenza tra le relazioni degli *Unità Stratigrafiche* (US) presenti nel DataFrame e restituisce i risultati come stringa.

Restituisce:
- ``str``: una stringa contenente gli errori di coerenza (se presenti).

``show_errors_in_dock_widget_google(errors: str)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Questa funzione mostra gli errori specificati nel widget a scomparsa.

Argomenti:
- ``errors``: gli errori da mostrare.

``show_error(message: str)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Questa funzione mostra un messaggio di errore.

Argomenti:
- ``message``: il messaggio di errore.

``show_info(message: str)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Questa funzione mostra un messaggio informativo.

Argomenti:
- ``message``: il messaggio da mostrare.

``on_pushButton_addrow_pressed()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Questa funzione aggiunge una riga alla tabella dei dati.

``on_pushButton_removerow_pressed()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Questa funzione rimuove la riga selezionata dalla tabella dei dati.

``add_row()``
~~~~~~~~~~~~~

Questa funzione aggiunge una riga alla tabella dei dati.

Classi
------

``MainWindow(QMainWindow)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Questa classe contiene la finestra principale dell'applicazione.

Note
-----

La documentazione è stata generata utilizzando il formato di markup reStructuredText e il tool di generazione della documentazione Sphinx.