
import sys
import traceback

import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsItem, \
    QGraphicsEllipseItem, \
    QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QGraphicsLineItem, QListWidgetItem, QListWidget, \
    QGraphicsPixmapItem, QListView, QGraphicsSimpleTextItem, QGraphicsRectItem, QInputDialog, QLineEdit, \
    QGraphicsPathItem, QPushButton, QAbstractItemView
from PyQt5.QtCore import Qt, QRectF, QLineF, QDataStream, QFile, QSize, QTimer, QPoint, QPointF
from PyQt5.QtGui import QPen, QColor, QPainterPath, QKeyEvent, QMouseEvent, QCursor, QTransform, QIcon, QPixmap, QFont, \
    QBrush
import networkx as nx

from pyqtgraph import QtCore



class GraphNode(QGraphicsItem):
    def __init__(self, graph, node_type, x, y, table, node_reference, main_window):
        super().__init__()
        self.node_reference = node_reference # Unique node reference
        self.graph = graph # Reference to the graph
        self.edges = [] # List of edges connected to the node
        self.node_type = node_type # Type of the node
        self.setFlag(QGraphicsItem.ItemIsMovable) # Make the node movable
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges) # Make the node send geometry changes
        self.table = table #
        self.main_window = main_window  # Reference to the MainWindow
        self.setAcceptHoverEvents(True)
        self.setZValue(2) #setta il valore Z dell'oggetto a 1, in modo che il nodo sia disegnato davanti agli archi.

        # Define the shape and color based on the node type
        self.shapes = {
            'extractor': (QGraphicsEllipseItem(0, 0, 50, 50), QColor('lightgray')),
            'combiner': (QGraphicsEllipseItem(0, 0, 50, 50), QColor('darkgray')),
            'USV/c': (QGraphicsRectItem(0, 0, 100, 50, self), QColor('blue')),
            'USV/n': (QGraphicsRectItem(0, 0, 100, 50, self), QColor('green')),
            'USV/s': (QGraphicsRectItem(0, 0, 100, 50, self), QColor('red')),
            'US': (QGraphicsRectItem(0, 0, 100, 50, self), QColor('yellow')),
            'USM': (QGraphicsRectItem(0, 0, 100, 50, self), QColor('yellow')),
            'SF': (QGraphicsRectItem(0, 0, 100, 50, self), QColor('orange')),
            'VSF': (QGraphicsRectItem(0, 0, 100, 50, self), QColor('purple')),
            'USD': (QGraphicsRectItem(0, 0, 100, 50, self), QColor('brown')),
            'UTR': (QGraphicsRectItem(0, 0, 100, 50, self), QColor('pink')),
            'property': (QGraphicsRectItem(0, 0, 100, 50, self), QColor('gray')),

            'document': (QGraphicsRectItem(0, 0, 100, 50, self), QColor('white')),
            'CON': (QGraphicsRectItem(0, 0, 100, 50, self), QColor('black')),

        }
        if node_type in self.shapes:
            self.shape, self.color = self.shapes[node_type]

        else:
            print(f"Unknown node type: {node_type}")
            self.shape, self.color = QGraphicsRectItem(0, 0, 50, 50, self), QColor('gray')
        # In the GraphNode constructor
        for shape in self.shapes.values():
            shape[0].setPen(QPen(Qt.NoPen))
        # Define the label text
        node_types_with_reference = ['US', 'USV/c', 'USV/n', 'USV/s', 'SF', 'VSF', 'USM', 'USD', 'UTR']
        label_text = f"{node_type}{node_reference}" if node_type.strip() in node_types_with_reference else str(
            node_reference)

        # Create the label

        self.label = QGraphicsSimpleTextItem(label_text,self)
        self.label.setFont(QFont('Arial', 8))
        # Set position to center
        label_rect = self.label.boundingRect()
        shape_rect = self.shape.boundingRect()
        self.label.setPos(shape_rect.width() / 2. - label_rect.width() / 2.,
                          shape_rect.height() / 2. - label_rect.height() / 2.)

        # Set color
        #self.shape.setBrush(QBrush(self.color))  # Change is here
        self.setPen(QPen(Qt.transparent, 0))  # Set pen to transparent
        # Set position
        self.setPos(x, y)



    def boundingRect(self):
        return self.shape.boundingRect()

    def set_label(self, new_label):
        print(f"Setting label to: {new_label}")
        self.label.setText(new_label)

        # Re-center the label after changing the text
        label_rect = self.label.boundingRect()
        shape_rect = self.shape.boundingRect()
        self.label.setPos(shape_rect.width() / 2. - label_rect.width() / 2.,
                          shape_rect.height() / 2. - label_rect.height() / 2.)

    def paint(self, painter, option, widget):
        painter.setBrush(self.color)
        pen = QPen()
        pen.setColor(Qt.transparent)
        painter.setPen(pen)

        if isinstance(self.shape, QGraphicsEllipseItem):
            painter.drawEllipse(self.shape.rect())
        elif isinstance(self.shape, QGraphicsRectItem):
            painter.drawRect(self.shape.rect())

        #self.label.paint(painter, option, widget)

    def hoverEnterEvent(self, event):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self.hovered = False
        self.update()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.adjust()
        return super().itemChange(change, value)

    def update_table(self):
        #print(f"Attempting to update table for node: {self.node_type}")
        # Making sure that both name in the graph node and in the table are in sync
        found_item = self.table.findItems(f"{self.node_type}{self.node_reference}", Qt.MatchExactly)
        if found_item:
            row = found_item[0].row()
            print(f"Found node in table at row: {row}")
            self.table.setItem(row, 1, QTableWidgetItem(self.label.text()))  # Update node name in table
            self.table.setItem(row, 2,
                               QTableWidgetItem(f"({self.x():<4}, {self.y():<4})"))  # Update node position in table
            print(
                f"After update, table contains: {self.table.item(row, 1).text()} at position {self.table.item(row, 2).text()}")
        else:
            print(f"Node: {self.node_type} not found in table.")

    def update_table2(self, old_node_reference):
        print(f"Attempting to update table for node: {self.node_reference}")
        found_item = self.table.findItems(f"{old_node_reference}", Qt.MatchExactly)
        print(f"Found item: {found_item}")
        if found_item:
            row = found_item[0].row()
            self.table.setItem(row, 0, QTableWidgetItem(self.label.text()))
            # Update position as well if necessary
            print(
                f"After update, table contains: {self.table.item(row, 0).text()} at position {self.table.item(row, 1).text()}")
        else:
            print(f"Node: {self.node_type} with old reference: {old_node_reference} not found in table.")


    def mousePressEvent(self, event):
        items = self.collidingItems(QtCore.Qt.IntersectsItemShape)
        for item in items:
            if isinstance(item, GraphNode):
                property_name, okPressed = QInputDialog.getText(self.main_window, "Get property", "Your property:",
                                                                QLineEdit.Normal, "")
                if okPressed and property_name != '':
                    item.label.setText(f"{item.node_type}.{property_name}")
                    item.update_table()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        # Quando c'è un doppio clic sul nodo, rimuovilo
        self.main_window.remove_node(self.node_reference)
        super().mouseDoubleClickEvent(event)

    def setPen(self, param):
        return


class GraphEdge(QGraphicsPathItem):
    def __init__(self, source, dest, offset, graph, isBidirectional=False,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source = source
        self.dest = dest
        self.graph = graph
        if isBidirectional:
            self.setPen(QPen(Qt.red, 1))  # Red color for bidirectional
        else:
            self.setPen(QPen(Qt.black, 1))  # Otherwise, black color
        self.offset = offset
        self.adjust()
        self.setZValue(-1) #setta il valore Z dell'oggetto a -1, in modo che l'arco sia disegnato dietro i nodi.
    def adjust(self):
        path = QPainterPath()
        startPos = self.source.mapToScene(self.source.boundingRect().center())
        endPos = self.dest.mapToScene(self.dest.boundingRect().center())
        path.moveTo(startPos)

        ctrlPt = self.control_point(startPos, endPos, float(self.offset))
        path.quadTo(ctrlPt, endPos)
        self.setPath(path)

    def control_point(self, source, target, offset):
        dx = target.x() - source.x()
        dy = target.y() - source.y()
        length = (dx * dx + dy * dy) ** 0.5
        direction = QPointF(dy / length, -dx / length)

        control_offset = QPointF(offset * direction.x(), offset * direction.y())
        center = QPointF((source.x() + target.x()) / 2, (source.y() + target.y()) / 2)
        return QPointF(center.x() + control_offset.x(), center.y() + control_offset.y())

    def mouseDoubleClickEvent(self, event):
        try:
            print("Double click detected")
            self.source.main_window.remove_edge(self.source, self.dest)



        except Exception as e:
            print(f"Unhandled error in mouseDoubleClickEvent: {str(e)}")
            print(traceback.format_exc())


class DragDropTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasText():
            if event.source() == self:
                event.setDropAction(Qt.MoveAction)

            else:
                event.setDropAction(Qt.CopyAction)

            start_row = self.rowAt(event.pos().y())

            data = event.mimeData().text().split('\n')

            for idx, i in enumerate(data):

                if i:  # If item is not empty
                    row = start_row + idx
                    self.insertRow(row)

                    for column, item in enumerate(i.split('\t')):
                        self.setItem(row, column, QTableWidgetItem(item))

            event.acceptProposedAction()
        else:
            super().dropEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.graph = nx.Graph()
        self.scene = MyGraphicsScene(self)
        self.view = GraphicsView(self.scene)
        #self.view = QGraphicsView(self.scene)
        self.view.setAcceptDrops(True)  # enable dropping on the
        self.table = DragDropTableWidget(0, 11)
        self.node_names = []
        self.list_widget = QListWidget()
        # Set the list widget to resize mode to adjust
        # Set the list widget to use LeftToRight flow
        self.list_widget.setFlow(QListView.LeftToRight)

        # Set the grid size to accommodate three columns
        self.list_widget.setGridSize(QSize(100, 100))  # Adjust the size as needed

        # Set the list widget to resize mode to adjust
        self.list_widget.setResizeMode(QListView.Adjust)

        # Set the view mode to icon mode
        self.list_widget.setViewMode(QListView.IconMode)
        self.node_counter = 1  # Add a counter for unique node ids
        self.document_node_counter = 1
        self.combiner_node_counter = 1
        self.extractor_node_counter = 1
        self.selected_node = None  # Keep track of the currently
        # Add Node and Edge options
        self.add_list_item('icons/USV.png', 'USV/c')
        self.add_list_item('icons/USVn.png', 'USV/n')
        self.add_list_item('icons/USVs.png', 'USV/s')
        self.add_list_item('icons/US.png', 'US')
        self.add_list_item('icons/US.png', 'USM')
        self.add_list_item('icons/SF.png', 'SF')
        self.add_list_item('icons/VSF.png', 'VSF')
        self.add_list_item('icons/USD.png', 'USD')
        self.add_list_item('icons/property.png', 'property')
        self.add_list_item('icons/extractor.png', 'extractor')
        self.add_list_item('icons/combiner.png', 'combiner')
        self.add_list_item('icons/document.png', 'document')
        self.add_list_item('icons/continuity.png', 'CON')
        self.node_map = {}  # Add this to __init__ method
        # Add more items as needed...

        self.init_ui()

    def type_checked_node_exists(self, node):
        if isinstance(node, GraphNode):  # checks if node is a GraphNode instance
            node_reference = node.node_reference  # Get the unique identifier of the GraphNode
            if node_reference in self.graph.nodes:
                return node_reference
        elif node in self.graph.nodes:
            return node
        elif str(node) in self.graph.nodes:
            return str(node)
        elif int(node) in self.graph.nodes:
            return int(node)
        else:
            return None

    def remove_edge(self, source_node, dest_node):
        # Print all nodes for debugging
        print(f"All nodes: {self.graph.nodes}")

        # Ensure both nodes exist
        converted_source_node = self.type_checked_node_exists(source_node)
        converted_dest_node = self.type_checked_node_exists(dest_node)
        if converted_source_node is None or converted_dest_node is None:
            print(f"Either source node {source_node} or destination node {dest_node} does not exist.")
            return

        # Ensure edge exists
        if not self.graph.has_edge(converted_source_node, converted_dest_node):
            print(f"No edge exists between {converted_source_node} and {converted_dest_node}.")
            return

        # Remove the graphic edge object from the scene
        edge = self.graph.edges[converted_source_node, converted_dest_node]['line']
        print(edge)
        self.scene.removeItem(edge)
        # Then, also update the table
        source_row = self.table.findItems(source_node.node_reference, Qt.MatchExactly)[0].row()
        dest_rows = self.table.findItems(dest_node.node_reference, Qt.MatchExactly)
        if dest_rows:
            dest_row = dest_rows[0].row()
        else:
            print(f"Error: No items match the given reference: {dest_node.node_reference}")
            return  # Or handle this situation appropriately

        # Remove the source->target relationship in the source row and target->source relationship in the dest row
        self.update_relationship_in_table(source_row, dest_node.node_reference, remove=True)
        self.update_relationship_in_table(dest_row, source_node.node_reference, remove=True)
        # Remove the edge from the

    def update_relationship_in_table(self, row, reference, remove=False):
        for column_with_relationships in range(6, 12):  # process columns 6 to 11
            cell_item = self.table.item(row, column_with_relationships)
            if cell_item:
                relationships = cell_item.text().split(",")  # Assuming relationships are separated by commas
                if remove and reference in relationships:
                    relationships.remove(reference)
                elif not remove:
                    relationships.append(reference)

                new_cell_value = ",".join(relationships)
                self.table.setItem(row, column_with_relationships, QTableWidgetItem(new_cell_value))

    def remove_node(self, node_id):
        if node_id not in self.graph.nodes:
            print(f"Node {node_id} does not exist in the graph.")
            return
        node_attributes = self.graph.nodes[node_id]
        if 'node_ref' not in node_attributes:
            print(f"Node {node_id} does not have a 'node_ref' attribute.")
            return
        node = node_attributes['node_ref']
        self.scene.removeItem(node)
        self.graph.remove_node(node_id)
        rows_to_remove = []
        for i in range(self.table.rowCount()):
            if self.table.item(i, 0).text() == node_id:
                rows_to_remove.append(i)
        for row in sorted(rows_to_remove, reverse=True):
            self.table.removeRow(row)

    def node_selected(self, node_id):
        print(f"node_selected called with {node_id}")  # line for debugging
        self.selected_node = node_id

    def node_deselected(self):
        # Deselect the currently selected node
        self.selected_node = None

    def init_ui(self):
        self.scene.setSceneRect(0, 0, 600, 400)
        layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(layout)

        # Create the layout button


        # Make list widget items draggable
        self.list_widget.setDragEnabled(True)
        # Add list widget to layout
        layout.addWidget(self.list_widget)

        # Allow drop events in the QGraphicsScene
        # self.scene.setAcceptDrops(True)
        layout.addWidget(self.view)
        self.table.setHorizontalHeaderLabels(["nome us", "tipo", "tipo di nodo", "descrizione", "epoca", "epoca_index",
                                              "anteriore", "posteriore", "contemporaneo", "properties_ant",
                                              "properties_post"])
        # Add the table to the layout
        self.table.setColumnCount(11)
        layout.addWidget(self.table)
        self.setCentralWidget(central_widget)
        #self.add_node('', '', '', '', '', '', '', '', '', '')
        # self.add_node('B', 'Tipo1', 150, 150)
        # self.add_edge('A', 'B')

    def add_list_item(self, image_path, node_type):
        # Check if the image file exists
        if QFile.exists(image_path):
            icon = QIcon(image_path)
            item = QListWidgetItem(icon, "")  # Set the icon and an empty label
            item.setData(Qt.UserRole, node_type)
            self.list_widget.addItem(item)
        else:
            print(f"Image not found: {image_path}")

    def read_attributes_from_csv(self,file_path):
        df = pd.read_csv(file_path)

        # assuming the attributes are in the first column
        attributes = df.iloc[:, 0].tolist()

        return attributes

    def add_node(self, node_type, x, y, additional_info=None):
        global new_node_names

        def increment_suffix(s):
            """
            Helper function to increment a suffix, or add "_2" if none exists
            """
            base, _, suffix = s.rpartition("_")
            if suffix.isdigit():
                return f"{base}_{int(suffix) + 1}"
            else:
                return f"{s}_2"
        def increment_suffix_extractor(s):
            """
            Helper function to increment a suffix, or add "_2" if none exists
            """
            base, _, suffix = s.rpartition(".")
            if suffix.isdigit():
                return f"{base}.{int(suffix) + 1}"
            else:
                return f"{s}.2"

        node_id = None

        if node_type == 'property':
            file_path = 'template/property.csv'
            properties = self.read_attributes_from_csv(file_path)
            properties = [prop.lower() for prop in properties]

            new_node_name, ok = QInputDialog.getItem(self, "Select Property", "Choose a property:", properties, 0,
                                                     False)
            if ok and new_node_name:
                new_node_name = new_node_name.lower()
            # Now new_node_name is unique, so we can assign it directly to node_id
            node_id = new_node_name
            # Add the (now unique) name to the list of node names
            self.node_names.append(new_node_name)

        elif node_type == 'document':
            new_node_name, ok = QInputDialog.getText(self, "Input dialog", f"Enter a new {node_type} name:")

            # only continue if user entered a name and pressed OK
            if ok and new_node_name:
                new_node_name = f"D.{new_node_name}"

                while new_node_name in self.node_names:
                    new_node_name = increment_suffix(new_node_name)

                node_id = new_node_name
                self.node_names.append(new_node_name)
        elif node_type == 'combiner':
            new_node_name, ok = QInputDialog.getText(self, "Input dialog", f"Enter a new {node_type} name:")

            # only continue if user entered a name and pressed OK
            if ok and new_node_name:
                new_node_name = f"C.{new_node_name}"

                while new_node_name in self.node_names:
                    new_node_name = increment_suffix(new_node_name)

                node_id = new_node_name
                self.node_names.append(new_node_name)
        elif node_type == 'extractor':
            new_node_name, ok = QInputDialog.getText(self, "Input dialog", f"Enter a new {node_type} name:")

            # only continue if user entered a name and pressed OK
            if ok and new_node_name:
                new_node_name = f"D.{new_node_name}.{self.extractor_node_counter}"

                while new_node_name in self.node_names:
                    new_node_name = increment_suffix_extractor(new_node_name)

                node_id = new_node_name
                self.node_names.append(new_node_name)

        else:
            new_node_name, ok = QInputDialog.getText(self, "Input dialog", f"Enter a new {node_type} name:")
            if ok and new_node_name:
                new_node_name = new_node_name
                # only continue if user entered a name and pressed OK
            node_id = new_node_name
            self.node_names.append(new_node_name)
        #self.node_counter += 1

        node = GraphNode(self.graph, node_type, x, y, self.table, node_id, self)
        self.graph.add_node(node_id, type=node_type, node_ref=node)
        # Check if GraphNode is a subclass of QGraphicsItem that actually has a setPen method
        if issubclass(GraphNode, QGraphicsItem):
            node.setPen(QPen(Qt.transparent, 0))
        self.scene.addItem(node)
        self.update_table(node)
        if node.isSelected():
            print(f"Il nodo {node_id} è attualmente selezionato")
        else:
            print(f"Il nodo {node_id} non è attualmente selezionato")

        print(f"Node map: {self.node_map}")

        return node_id  # Return the generated node_id

    def add_edge(self, source_id, dest_id):
        global offset
        if source_id in self.graph and dest_id in self.graph:
            # Create the edge in the graph
            source_node = self.graph.nodes[source_id]['node_ref']
            dest_node = self.graph.nodes[dest_id]['node_ref']
            offset=0
            edge = GraphEdge(source_node, dest_node,offset, self.graph)
            self.graph.add_edge(source_id, dest_id, line=edge)
            self.scene.addItem(edge)

            # Update the table for the source node
            source_items = self.table.findItems(source_id, Qt.MatchExactly)
            if source_items:
                source_row = source_items[0].row()
                current_posterior = self.table.item(source_row, 6)  # Assuming 'posteriore' is in column 7
                if current_posterior:
                    current_value = current_posterior.text()
                    new_value = f"{current_value}, {dest_id}" if current_value else dest_id
                    self.table.setItem(source_row, 6, QTableWidgetItem(new_value))
                else:
                    self.table.setItem(source_row, 6, QTableWidgetItem(dest_id))

            # Update the table for the destination node
            dest_items = self.table.findItems(dest_id, Qt.MatchExactly)
            if dest_items:
                dest_row = dest_items[0].row()
                current_anterior = self.table.item(dest_row, 7)  # Assuming 'anteriore' is in column 6
                if current_anterior:
                    current_value = current_anterior.text()
                    new_value = f"{current_value}, {source_id}" if current_value else source_id
                    self.table.setItem(dest_row, 7, QTableWidgetItem(new_value))
                else:
                    self.table.setItem(dest_row, 7, QTableWidgetItem(source_id))

        if source_id in self.graph and dest_id in self.graph:
            source_node = self.graph.nodes[source_id]['node_ref']
            dest_node = self.graph.nodes[dest_id]['node_ref']
            edge = GraphEdge(source_node, dest_node, offset,self.graph)
            self.graph.add_edge(source_id, dest_id, line=edge)
            self.scene.addItem(edge)
        else:
            print(f"One or both nodes {source_id} and {dest_id} do not exist")

    def add_edge2(self, source_node, target_node):
        offset=0
        new_edge = GraphEdge(source_node, target_node, offset,self.graph)  # Creazione di un nuovo arco
        self.scene.addItem(new_edge)  # Aggiunge l'arco alla scena
        # Add the edge to the networkx graph
        self.graph.add_edge(source_node.node_reference, target_node.node_reference, line=new_edge)

        source_node.edges.append(new_edge)  # Add the edge to the list of edges of the source node
        target_node.edges.append(new_edge)
        if "property" in target_node.node_type:
            if source_node.node_reference:
                print("Updating property for source node.")
                old_node_reference = target_node.node_reference
                node_id = source_node.node_reference
                new_node_reference = f"{node_id}.{target_node.node_reference}"
                print(f"New node reference: {new_node_reference}")

                target_node.node_reference = new_node_reference
                target_node.label.setText(new_node_reference)

                print(f"Updating table for node: {target_node.node_type} with old reference: {old_node_reference}")
                target_node.update_table2(old_node_reference)
        else:
            print("The source node is not a property or the target node is in the special types.")

        source_row = self.table.findItems(source_node.node_reference, Qt.MatchExactly)[0].row()
        print(f"Source row: {source_row}")

        dest_rows = self.table.findItems(target_node.node_reference, Qt.MatchExactly)
        if not dest_rows:
            print(f"Error: No items match the given reference: {target_node.node_reference}")
            return
        else:
            dest_row = dest_rows[0].row()



        # Define special node types
        special_types = ["property", "extractor", "combiner", "document"]

        # Update the table based on the node types
        if source_node.node_type in special_types:
            # Update 'properties_post' for source node
            self.update_properties_column(source_row, 9,
                                          target_node.node_reference)  # Assuming 'properties_post' is in column 9
        else:
            # Update 'posteriore' for source node
            self.update_properties_column(source_row, 6,
                                          target_node.node_reference)  # Assuming 'posteriore' is in column 7

        if target_node.node_type in special_types:
            # Update 'properties_ant' for destination node
            self.update_properties_column(dest_row, 10,
                                          source_node.node_reference)  # Assuming 'properties_ant' is in column 8
        else:
            # Update 'anteriore' for destination node
            self.update_properties_column(dest_row, 7,
                                          source_node.node_reference)  # Assuming 'anteriore' is in column 6

    def add_double_parallel_edge(self, source_node, target_node):
        self.add_parallel_edge(source_node, target_node)
        self.add_parallel_edge(target_node, source_node)

        source_row = self.table.findItems(source_node.node_reference, Qt.MatchExactly)[0].row()
        dest_row = self.table.findItems(target_node.node_reference, Qt.MatchExactly)[0].row()

        self.update_properties_column(source_row, 8, target_node.node_reference)
        self.update_properties_column(dest_row, 8, source_node.node_reference)

    def add_parallel_edge(self, source_node, target_node, offset=10):
        new_edge = GraphEdge(source_node, target_node, offset,self.graph, isBidirectional=True)

        self.scene.addItem(new_edge)
        source_node.edges.append(new_edge)
        target_node.edges.append(new_edge)

    def update_properties_column(self, row, column, node_reference):
        current_item = self.table.item(row, column)
        if current_item:
            current_value = current_item.text()
            new_value = f"{current_value},{node_reference}" if current_value else node_reference
            self.table.setItem(row, column, QTableWidgetItem(new_value))
        else:
            self.table.setItem(row, column, QTableWidgetItem(node_reference))

    def update_table(self, node):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(f"{node.node_reference}"))  # Node name with progressive number
        self.table.setItem(row, 1, QTableWidgetItem(f"{node.node_type}"))  # Node type

        self.table.setItem(row, 2, QTableWidgetItem("Tipo di nodo"))  # Placeholder for "tipo di nodo"
        self.table.setItem(row, 3, QTableWidgetItem("Descrizione"))  # Placeholder for "descrizione"
        self.table.setItem(row, 4, QTableWidgetItem("Epoca"))  # Placeholder for "epoca"
        self.table.setItem(row, 5, QTableWidgetItem("1"))
        self.table.setItem(row, 6, QTableWidgetItem(""))
        self.table.setItem(row, 7, QTableWidgetItem(""))
        self.table.setItem(row, 8, QTableWidgetItem(""))
        self.table.setItem(row, 9, QTableWidgetItem(""))
        self.table.setItem(row, 10, QTableWidgetItem(""))

class MyGraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):  # Now it takes a MainWindow instance
        super().__init__(parent)
        self.parent = parent
        self.a_key_pressed = False
        self.b_key_pressed = False
        self.source_node = None
        self.draft_edge = None

        # Key press and release events to set/reset the a_key_pressed flag

    def node_at_cursor(self):
        # Assuming you’ve a method to get the cursor position
        cursor_position = self.cursor_position()

        # Find items at cursor position. The items could be nodes or anything else in the graphics scene
        items = self.items(cursor_position)

        # Find the node among the items if it exists
        for item in items:
            if isinstance(item, GraphNode):  # replace with the actual name of your node class
                return item

                # if no node at cursor position
        return None

    def cursor_position(self):
        view = self.views()[0]
        # This will give pos relative to view
        pos = view.mapFromGlobal(QCursor.pos())
        # This will give pos relative to scene
        scenePos = view.mapToScene(pos)
        return scenePos

    def draw_draft_edge(self, source, target):
        line = QLineF(source.pos(), target)
        draft_line = self.addLine(line)
        return draft_line

        # If you need a custom Edge class (with additional attributes or methods), you would create and add it here.
        # edge = GraphEdge(source, target)
        # self.addItem(edge)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_A:
            self.a_key_pressed = True
        if event.key() == Qt.Key_B:
            self.b_key_pressed = True
    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_A:
            self.a_key_pressed = False
        if event.key() == Qt.Key_B:
            self.b_key_pressed = False
        # Mouse press event to set the source node if A key is pressed

    def mousePressEvent(self, event: QMouseEvent):
        if self.a_key_pressed:
            self.source_node = self.node_at_cursor()
            if self.source_node:
                self.draft_edge = self.draw_draft_edge(self.source_node, self.cursor_position())
            self.a_key_pressed = False

        elif self.b_key_pressed:
            self.source_node = self.node_at_cursor()
            if self.source_node:
                self.draft_edge = self.draw_draft_edge(self.source_node, self.cursor_position())
            self.b_key_pressed = False

        else:
            QGraphicsScene.mousePressEvent(self, event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.source_node and self.draft_edge:
            # Get the view from the scene
            view = self.views()[0]
            # Convert QPointF to QPoint
            point = event.pos().toPoint()
            # Map the QPoint to scene coordinates
            scenePos = view.mapToScene(point)
            # Update the draft edge line
            line = QLineF(self.source_node.pos(), scenePos)
            self.draft_edge.setLine(line)
        else:
            QGraphicsScene.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.source_node and self.draft_edge:
            self.removeItem(self.draft_edge)
            target_node = self.node_at_cursor()

            if target_node and target_node is not self.source_node:
                if self.b_key_pressed:
                    self.parent.add_double_parallel_edge(self.source_node,
                                                         target_node)  # New method for double parallel edges
                    self.b_key_pressed = False
                else:
                    self.parent.add_edge2(self.source_node, target_node)


            self.draft_edge = None
            self.source_node = None
        else:
            QGraphicsScene.mouseReleaseEvent(self, event)
#
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            event.acceptProposedAction()
        print('Drag entered')

    def dragMoveEvent(self, event):
        event.acceptProposedAction()
        print('Drag moved')
        self.parent.node_deselected()  # Deselect current node after drawing the edge


    def dropEvent(self, event):
        item = event.source().currentItem()  # Get QListWidgetItem
        type_data = item.data(Qt.UserRole)  # Get UserRole data

        if type_data:
            # Add the node and get its reference
            node_reference = self.parent.add_node(type_data, event.scenePos().x(), event.scenePos().y())

            # If a node is selected, draw an edge between the new node and the selected node
            if self.parent.selected_node is not None and node_reference:
                self.parent.add_edge(self.parent.selected_node, node_reference)
                self.parent.node_deselected()  # Deselect current node after drawing the edge
class GraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._isPanning = False
        self._panStartX = 0
        self._panStartY = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._isPanning = True
            self._panStartX = event.x()
            self._panStartY = event.y()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._isPanning:
            # Calculate the delta using mapToScene to get the scene coordinates
            new_pos = self.mapToScene(event.pos())
            old_pos = self.mapToScene(QPoint(self._panStartX, self._panStartY))
            delta = new_pos - old_pos

            # Scroll by the delta
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - round(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - round(delta.y()))

            # Update the start positions for the next move event
            self._panStartX = event.x()
            self._panStartY = event.y()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self._isPanning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        # Zoom Factor
        zoomInFactor = 1.25
        zoomOutFactor = 1 / zoomInFactor

        # Save the scene pos
        oldPos = self.mapToScene(event.pos())

        # Zoom
        if event.angleDelta().y() > 0:
            zoomFactor = zoomInFactor
        else:
            zoomFactor = zoomOutFactor
        self.scale(zoomFactor, zoomFactor)

        # Get the new position
        newPos = self.mapToScene(event.pos())

        # Move scene to old position
        delta = newPos - oldPos
        self.translate(delta.x(), delta.y())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()

    window.show()
    sys.exit(app.exec_())

