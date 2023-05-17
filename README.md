# CSVMapper class
The CSVMapper class is a subclass of QMainWindow and the main dialog class MAIN_DIALOG_CLASS. It contains methods for customizing the GUI, loading and transforming CSV data, checking consistency errors, and displaying dialog messages.

## Methods
- __init__(self)
Sets up the class as a main window by calling the superclass constructor and setting up the GUI using setupUi method and custumize_gui method.

- custumize_gui(self)
Sets the central widget, status bar, and its style sheet for the window.

- on_toolButton_load_pressed(self)
Loads a data CSV file using QFileDialog.getOpenFileName, and reads it using pandas read_csv method. It creates a PandasModel object from the data and sets it in the data_table widget.

- transform_data(self, input_file, output_file)
Transforms the data by reading CSV file, finding specific columns in the header, editing them, and writing the result to another CSV file. It also checks consistency errors in the transformed data.

- on_convert_data_pressed(self)
Reads the transformed CSV file, generates the matrix, and converts it to GraphML format using dottoxml.

- read_transformed_csv(self, filename)
Reads the transformed CSV file, extracts information from specific columns, and returns them as a list and a dictionary of tuples.

- check_consistency(self, data)
Checks consistency errors in the CSV file by comparing anterior, contemporaneo, and posteriore relations and reporting errors.

- show_errors_in_dock_widget(self)
Shows the errors found by check_consistency method in a dock widget.

- show_error(self, message)
Displays an error dialog with the provided message.

- show_info(self, message)
Displays an information dialog with the provided message.

# AddSequenceDialog
Defines a dialog window for entering starting numbers used to add a sequence of numbers to the CSV file.

# PandasModel class
The PandasModel class is a subclass of QAbstractTableModel and used to create a table model from Pandas DataFrame. It overrides several methods to return data and set data in the view.