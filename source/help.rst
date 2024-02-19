HELP
=================================
    .. toctree::
       :maxdepth: 2
       :caption: Contents:

Help for using EM2Graphml
==============================

ED2Graphml is an application that allows you to convert and verify relationships between data in a CSV file or Google Sheet and transform it into Graphml for EM Tools.

Starting the program
---------------------

1. Download the provided batch file and place it in the desired folder on your computer.
2. Double-click the batch file to launch it.
3. The batch file script will take care of checking whether Python and PyQt5 are installed.
4. If Python or PyQt5 are not installed, the script will use PackageManagement to install them automatically.
5. After installation, the script will launch the main program with a splash screen.
6. The splash screen will show the progress of the program loading.
7. Once loading is complete, the main program will launch and you can start using it.

Main functions
-------------------

- Load data from a Google Sheet: This feature allows you to load data directly from a Google Sheet.
- Update Reports: This function allows you to update relationships between data.
- 3D Viewer: This feature allows you to view data in a 3D format.
- Error checking: This function allows you to check for errors in data relationships.

Error checking functions
----------------------------

EM2Graphml offers several functions to check data relationships for errors:

- Duplicate Check: This function checks if there are duplicates in the same row.
- Relationship existence check: This function checks whether relationships exist.
- Check existence of inverse relations: This function checks whether inverse relations exist.
- Relationship type check: This function checks whether the relationship type is correct.

Select historical era
-----------------------

EM2Graphml also offers a feature that allows you to select a historical era from a drop-down list. This list is populated by the data in your CSV file or Google Sheet.

Saving data
--------------------

EM2Graphml allows you to save data to a CSV file or Google Sheet. The "Save CSV" and "Save Google" buttons are linked to the corresponding functions.

Update of reports
-----------------------------

EM2Graphml offers two functions for updating data relationships: one for CSV files and one for Google Sheets.

Updating relationships for CSV files
--------------------------------------------

This function opens the CSV file, reads all the rows, and creates a dictionary to store the rows by name. Then, for each row, check the type of stratigraphic unit and update the corresponding relations. Finally, update the table with the updated data.

Updated reports for Google Sheets
-------------------------------------------------

This feature works similarly to the feature for CSV files, but instead of opening a CSV file, it opens a Google Sheet. After reading all the rows from the Google Sheet, create a dictionary to store the rows by name. Then, for each row, check the type of stratigraphic unit and update the corresponding relations. Finally, update the table with the updated data.

Note:
-----
For both functions, if the stratigraphic unit is of type 'property', 'document', 'combiner' or 'extractor', the 'properties_ant' and 'properties_post' relations are updated. If the stratigraphic unit is of the 'contemporary' type, the 'contemporary' relationship is updated. In all other cases, the 'front' and 'back' relationships are updated.

Updating relationships in the DataFrame
-------------------------------------------

EM2Graphml provides a function to update relations in the DataFrame. This function reads data from the QTableWidget, updates reports in the DataFrame, and displays any errors in the widget dock.

Viewing changes
--------------------------------

EM2Graphml offers a function to show the differences between old and new rows. This feature can be used to verify changes made to data.

Saving changes
---------------------------

EM2Graphml offers a function to ask the user if he wants to save the changes. If the user decides to save the changes, they will be saved to the CSV file and the file will be reloaded.

Viewing dialogue from the era
--------------------------------------

EM2Graphml offers a feature to show an epoch dialog when a cell in the "Epoch" column is double-clicked. This function creates an instance of EpochDialog and displays the dialogue to the user.

Saving data to a CSV file or Google Sheet
-------------------------------------------------- --------

EM2Graphml offers two functions for saving data: one for CSV files and one for Google Sheets. These functions read data from the QTableWidget, create a new DataFrame with this data, and save the DataFrame to the CSV file or Google Sheet.

Updating and restoring CSV data
---------------------------------------

EM2Graphml offers two functions to update and restore CSV data. The update function updates the original DataFrame with the data from the QTableWidget. The restore function restores the QTableWidget's data to the original DataFrame.

Get the current DataFrame
------------------------------

EM2Graphml provides a function to get the current DataFrame from the QTableWidget. This function can be used to get the data currently displayed in the QTableWidget.

Update Relationships
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This function reads data from the QTableWidget and adds it to a new DataFrame. It then updates the relationships in the DataFrame. If there are any changes, it will ask the user if they want to save the changes and will save the CSV file if necessary.

Update Relationships in the DataFrame
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This function takes a DataFrame as input, updates the relations in the DataFrame, and returns the updated DataFrame along with the new header.

Show Changes
~~~~~~~~~~~~~~~~~~

This function prints the differences between the old and new lines. If a line has changed, the old line and the new line will be printed.

Ask to Save Changes
-------------------------------

This feature asks the user if they want to save the changes. If the user chooses to save changes, the changes will be saved to the output CSV file.

3D Graphics Window
~~~~~~~~~~~~~~~~~~~

The GraphWindow class creates a window that displays a 3D graph. This window includes three dockwidgets: "Node Info", "Next Nodes Info" and "Media Files". Each dockwidget contains a QTextEdit or QWidget that displays information about the selected node, neighboring nodes, or media files associated with the selected node.

The d_graph function reads a graphml file, retrieves the x, y coordinates for each node and creates a 3D plot of the graph. If 3D models exist that match the node descriptions, they are loaded and displayed as 3D objects in the plot. Otherwise, a 3D image or sphere appears.

The callback function is executed when you click on a point in the 3D plot. Calculate the distance between the selected point and each node in the graph, find the closest node and display the information of this node in the QTextEdit. If the node has an associated media file, it is displayed in the QWidget.

The eventFilter function handles mouse events to start, pause, and stop playing a video when you click the mouse on the QWidget showing the video.

pyarchinit_Interactive_Matrix class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `pyarchinit_Interactive_Matrix` class handles the generation of an interactive matrix.

The `__init__` method initializes the class and sets the `DATA_LIST` and `ID_US_DICT` variables.

The `csv_connect` method takes care of connecting to the CSV file.

The `urlify` method converts a string to a URL-friendly format, replacing spaces with underscores.

The `generate_matrix` method generates the matrix from the supplied data. Different functions are used to process and organize data.

HarrisMatrix class
~~~~~~~~~~~~~~~~~~~~

The `HarrisMatrix` class manages the export of the Harris matrix in different formats.

The `__init__` method initializes the class and sets the `sequence`, `conteporene`, `property` and `periods` variables.

The `export_matrix_2` method generates the Harris matrix using the Graphviz library. Several subgraphs are created to represent the relationships between the data.

Installing Graphviz
~~~~~~~~~~~~~~~~~~~~~~~~~

The program checks whether Graphviz is installed and whether it is in the operating system's PATH. Graphviz is required for graph conversion.

The `is_graphviz_installed` function runs the "dot -V" command to check if Graphviz is installed. If the command executes successfully, the function returns True, otherwise it returns False.

The `is_graphviz_in_path` function checks whether the Graphviz bin directory is in the operating system's PATH. If it is, the function returns True, otherwise it returns False.

The `install_graphviz` function displays a warning message if Graphviz is not installed. The message suggests how to install Graphviz depending on your operating system.

The `set_graphviz_path` function displays a warning message if Graphviz is not in the operating system's PATH. The message suggests adding the Graphviz directory to your PATH.

The `check_graphviz` function calls the `is_graphviz_installed` and `is_graphviz_in_path` functions, and displays an appropriate message depending on the results. If Graphviz is installed and in the PATH, it shows a message that says "Graphviz is installed and ready to use".
