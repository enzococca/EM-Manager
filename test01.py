import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QFileDialog, QTableWidget, QTableWidgetItem
from PIL import Image
import base64

class TestScketchGPT(unittest.TestCase):
    def setUp(self):
        # Create a mock main application class
        self.mock_app = MagicMock()
        self.mock_app.data_table = QTableWidget(2, 2)
        self.mock_app.data_table.setItem(0, 0, QTableWidgetItem("Cell 1"))
        self.mock_app.data_table.setItem(0, 1, QTableWidgetItem("Cell 2"))
        self.mock_app.data_table.setItem(1, 0, QTableWidgetItem("Cell 3"))
        self.mock_app.data_table.setItem(1, 1, QTableWidgetItem("nan"))

    @patch('PyQt5.QtWidgets.QFileDialog.getOpenFileName')
    @patch('PIL.Image.open')
    @patch('GPT.ask_sketch')
    def test_scketchgpt_valid_image(self, mock_ask_sketch, mock_image_open, mock_get_open_file_name):
        # Mock the file dialog to return a valid file path
        mock_get_open_file_name.return_value = ('/path/to/image.png', '')

        # Mock the image verification
        mock_image = MagicMock()
        mock_image_open.return_value.__enter__.return_value = mock_image

        # Mock the GPT response
        mock_ask_sketch.return_value = "Mock GPT Response"

        # Call the scketchgpt method
        self.mock_app.scketchgpt()

        # Check that the image was opened and verified
        mock_image_open.assert_called_once_with('/path/to/image.png')
        mock_image.verify.assert_called_once()

        # Check that the GPT model was called with the correct parameters
        expected_table_data_str = "Cell 1\tCell 2\nCell 3\t"
        mock_ask_sketch.assert_called_once_with(self.mock_app, f"trasforma questo diagramma in {expected_table_data_str}",
                                                self.mock_app.apikey_gpt(), '/path/to/image.png')

        # Check that the response was added to the list widget
        self.mock_app.listWidget_ai.addItem.assert_called_once_with("GPT Response\n: Mock GPT Response")

    @patch('PyQt5.QtWidgets.QFileDialog.getOpenFileName')
    def test_scketchgpt_image_selection_canceled(self, mock_get_open_file_name):
        # Mock the file dialog to return no file path
        mock_get_open_file_name.return_value = ('', '')

        # Call the scketchgpt method
        self.mock_app.scketchgpt()

        # Check that the appropriate message was added to the list widget
        self.mock_app.listWidget_ai.addItem.assert_called_once_with("Image selection was canceled.")

    @patch('PyQt5.QtWidgets.QFileDialog.getOpenFileName')
    @patch('PIL.Image.open')
    def test_scketchgpt_invalid_image(self, mock_image_open, mock_get_open_file_name):
        # Mock the file dialog to return a valid file path
        mock_get_open_file_name.return_value = ('/path/to/invalid_image.png', '')

        # Mock the image verification to raise an exception
        mock_image = MagicMock()
        mock_image_open.return_value.__enter__.return_value = mock_image
        mock_image.verify.side_effect = Exception("Invalid image")

        # Call the scketchgpt method
        self.mock_app.scketchgpt()

        # Check that the appropriate error message was added to the list widget
        self.mock_app.listWidget_ai.addItem.assert_called_once_with("Error processing image: Invalid image")

if __name__ == '__main__':
    unittest.main()
