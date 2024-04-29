import networkx as nx
import pyvista as pv
import sys
from PyQt5 import QtWidgets, QtCore,QtWebEngineWidgets
from PyQt5.QtCore import QUrl,Qt,QEvent,QObject
from PyQt5.QtGui import QPixmap,QMouseEvent
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QLabel,QMessageBox
from pyvistaqt import QtInteractor
import os
import numpy as np
from PIL import Image
import trimesh
from docx import Document
import openpyxl
from html import escape
import tempfile



G = None  # Definisci G all'inizio del tuo codice
graphml_path=None
class HoverHandler(QObject):
    def __init__(self, plotter, graph, x_coord, y_coord, z_coord, info_widget):
        super().__init__()
        self.plotter = plotter
        self.graph = graph
        self.x_coord = x_coord
        self.y_coord = y_coord
        self.z_coord = z_coord
        self.info_widget = info_widget
        self.threshold_distance = 0.1  # Set this value appropriately for your case
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseMove:
            # Get the mouse position and convert it to world coordinates
            mouse_pos = event.pos()
            world_pos = self.plotter.pick_mouse_position()

            # Find the closest node to the mouse position
            closest_node_id, min_dist = None, float('inf')
            for node_id in self.graph.nodes():
                # Check if the node_id exists in the dictionaries before using it
                if (node_id in self.x_coord) and (node_id in self.y_coord) and (node_id in self.z_coord):
                    node_pos = np.array([self.x_coord[node_id], self.y_coord[node_id], self.z_coord[node_id]])
                    dist = np.linalg.norm(world_pos - node_pos)
                    if dist < min_dist:
                        closest_node_id, min_dist = node_id, dist

            # If a node is close enough to the mouse position, display its information
            if closest_node_id and min_dist < self.threshold_distance:
                node_data = self.graph.nodes[closest_node_id]
                info_text = "\n".join(f"{key}: {value}" for key, value in node_data.items())
                self.info_widget.setText(info_text)
            else:
                self.info_widget.clear()

        return super().eventFilter(obj, event)

class GraphWindow(QtWidgets.QMainWindow):

    def __init__(self, graphml_path, parent=None, show=True):

        QtWidgets.QMainWindow.__init__(self, parent)

        # Creo layout
        layout = QtWidgets.QHBoxLayout()
        self.graphml_path = graphml_path

        # Creo three dockwidgets
        self.dock1 = QtWidgets.QDockWidget("Node Info")
        self.dock2 = QtWidgets.QDockWidget("Nodi prossimi Info")
        self.dock3 = QtWidgets.QDockWidget("File Multimediali")  # Added
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dock1)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock2)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.dock3)  # Added

        # Creo three QTextEdits e setto come widget per il dockwidgets
        self.node_info_textedit = QtWidgets.QTextEdit()
        self.neighbor_info_textedit = QtWidgets.QTextEdit()
        self.file_info_widget = QtWidgets.QWidget()  # Placeholder widget
        self.dock1.setWidget(self.node_info_textedit)
        self.dock2.setWidget(self.neighbor_info_textedit)
        self.dock3.setWidget(self.file_info_widget)

        # Crea il plotter PyVistaqt
        self.plotter = QtInteractor(self)#con questa classe di pyvistaqyt posso aggiungere il plotter tra le due dockwidget
        layout.addWidget(self.plotter.interactor)

        # Imposta il layout centrale
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Esegui la funzione d_graph
        self.d_graph()

        # Abilita il picking dei punti
        self.plotter.enable_point_picking(self.callback)
        self.plotter.view_xy()
        self.plotter.camera.roll += 180 # ruoto di 180 la camera perchè di dfault è al contrario (bho)
        if show:
            self.show()#mostro il plotter

        self.statusbar = None
        # Create the hover handler and install it as an event filter on the plotter interactor
        self.hover_handler = HoverHandler(self.plotter, G, self.x_coord, self.y_coord, self.z_coord,
                                          self.node_info_textedit)
        self.plotter.interactor.installEventFilter(self.hover_handler)

    def d_graph(self):


        print(f"path da d_graph: {self.graphml_path}")
        global G  # Utilizza la parola chiave global per fare riferimento alla variabile G definita all'esterno
        # Colore per gli archi
        EDGE_COLOR = [0, 0, 0]  # black
        if self.graphml_path:
            # Lettura del file graphml
            G = nx.read_graphml(self.graphml_path)

            # Recupero delle coordinate x, y per ogni nodo, dove l'ID del nodo è la chiave
            self.x_coord = {node_id: float(node_data["x"]) for node_id, node_data in G.nodes(data=True) if "x" in node_data}
            self.y_coord = {node_id: float(node_data["y"]) for node_id, node_data in G.nodes(data=True) if "y" in node_data}
            # Poiché non sembra esserci una z nelL'output, assegno un valore di 0 a tutti i nodi per ora.
            self.z_coord = {node_id: 0 for node_id in G.nodes()}

            # Creazione del plotter
            #self.plotter = BackgroundPlotter(notebook=0) # con questo visualizzo la finetra di pyvista separata
            self.plotter.background_color = [255, 255, 255]
            # Abilito lo stile di interazione con il trackball
            self.plotter.enable_trackball_style()
            # Aggiungo gli archi e itero sul grafo G
            # e verifico se i due nodi di ogni arco hanno coordinate x, y e z corrispondenti in tre dizionari separati (self.x_coord, self.y_coord, self.z_coord).
            # Se lo hanno, viene creato un segmento di linea tra i due nodi utilizzando queste coordinate e quindi viene creato un tubo intorno al segmento di linea utilizzando
            # il parametro radius=0.1.
            # Infine, aggiungo questa forma di tubo come mesh a un plot 3D usando self.plotter.add_mesh() con un colore specificato (EDGE_COLOR).
            for edge in G.edges():
                node1, node2 = edge
                if node1 in self.x_coord and node1 in self.y_coord and node2 in self.x_coord and node2 in self.y_coord:
                    line = pv.Line(
                        [self.x_coord[node1], self.y_coord[node1], self.z_coord[node1]],
                        [self.x_coord[node2], self.y_coord[node2], self.z_coord[node2]],
                    )
                    tube = line.tube(radius=0.5)# tubo è lo stile 3d
                    self.plotter.add_mesh(tube, color=EDGE_COLOR)#lo aggiugno alla mesh

            meshes = []#creao una lista vuota dove inserire le mesh che devono essere visualizzate come oggetti 3D
            mesh=''
            try:
                # Directory dei modelli 3D
                dir = os.path.dirname(self.graphml_path)
                models_dir = os.path.join(dir, "3d_obj")
                graph_icon = os.path.join(dir, "3d_obj")

                # Lista dei modelli 3D esistenti
                existing_models = [f[:-4] for f in os.listdir(models_dir) if f.endswith(".obj")]

                # Dizionario dei modelli di default per tipo di nodo
                default_models = {
                    "USV": "USVn.obj",
                    "VSF": "VSF.obj",
                    "SF": "SF.obj",
                    "US": "US.obj",
                    "USVs": "USVs.obj",
                    "combiner": "combiner.obj",
                    "extractor": "extractor.obj",
                    "D.": "document.obj",
                    "property": "property.obj",
                    "USD": "USD.obj",
                    "TSU": "TSU.obj"
                }

                # Verifica quali modelli 3D corrispondono alle descrizioni dei nodi
                for node_id, node_data in G.nodes(data=True):
                    # Check if the node has 'x', 'y', and 'label' attributes
                    if 'x' in node_data and 'y' in node_data and 'label' in node_data:
                        x = float(node_data['x'])
                        y = float(node_data['y'])
                        z = self.z_coord.get(node_id, 0)  # Use a default value if 'z' is not present
                        label = node_data['label']

                        # Determine the model filename based on the existing models or use a default
                        model_filename = f"{label}.obj" if label in existing_models else None
                        if not model_filename:
                            # Find a default model based on the node type
                            for node_type, default_model in default_models.items():
                                if node_type in label:
                                    model_filename = default_model
                                    break

                        # If a model filename was determined, try to load it
                        if model_filename:
                            model_path = os.path.join(models_dir, model_filename)
                            if os.path.exists(model_path):
                                mesh = pv.read(model_path)

                                # Calculate the scale factor based on the desired size
                                mesh_size = max(mesh.bounds[1] - mesh.bounds[0],
                                                mesh.bounds[3] - mesh.bounds[2],
                                                mesh.bounds[5] - mesh.bounds[4])
                                desired_size = 50  # Diameter of the sphere (twice the radius)
                                scale_factor = desired_size / mesh_size

                                # Scale the mesh
                                mesh.points *= scale_factor
                                # Apply transformations...
                                self.plotter.add_mesh(mesh, color='white')
                            else:
                                print(f"Model file not found: {model_path}")
                        else:
                            print(f"No default model found for node {node_id} with label '{label}'")

                        # If no model was loaded, create a fallback sphere
                        if not model_filename or not os.path.exists(model_path):
                            print(f"Creating fallback sphere for node {node_id}")
                            mesh = pv.Sphere(center=(x, y, z), radius=25)
                            self.plotter.add_mesh(mesh, color='white')
                    else:
                        print(f"Error: Node {node_id} is missing required data.")

                    meshes.append(mesh)
            except Exception as e:
                print(f"Errore durante la creazione del modello 3D: {e}")
        else:
            print('Grahml non trovato')
            QMessageBox.warning(self, 'Attenzione', 'Devi caricare un progetto con Graphml valido')
    def euclidean_distance(self,point1, point2):
        #questa funzione serve per poter calcolare le coordinate del punto dove si clicca per mostrate le info
        return np.sqrt(np.sum((np.array(point1) - np.array(point2)) ** 2))

    def callback(self, pick_result):
        #funzione che restituisce l'info quando si clicca
        global G  # Mi assicuro che G sia accessibile

        # Ottengo le coordinate del punto selezionato
        picked_point = pick_result  # Non c'è bisogno di '.position'

        # Calcolo la distanza tra il punto selezionato e ogni nodo nel grafo
        distances = {node_id: self.euclidean_distance([self.x_coord.get(node_id, 0), self.y_coord.get(node_id, 0), self.z_coord.get(node_id, 0)], picked_point)
                     for node_id in G.nodes()}

        # Trovo l'ID del nodo con la distanza minore
        closest_node_id = min(distances, key=distances.get)

        # Recupero le informazioni del nodo più vicino
        closest_node_info = G.nodes[closest_node_id]

        # Aggiungo le informazioni del nodo al QTextEdit
        node_info_text = "\n".join(f"{key}: {value}" for key, value in closest_node_info.items())
        self.node_info_textedit.setText(node_info_text)
        # Assuming that the file path is stored in the 'file_path' attribute of the node
        file_path = closest_node_info.get('url')
        dir = os.path.dirname(self.graphml_path)
        try: # questo try va ottimizzato per il momento è una toppa
            file_path_abs_ = os.path.join(dir, file_path)
            file_path_abs = os.path.abspath(file_path_abs_)
            print(os.path.exists(file_path))
        except:
            pass
        if file_path is not None and os.path.exists(file_path_abs):

            extension = os.path.splitext(file_path)[-1].lower()

            if extension in ('.pdf'):

                file_path_pdf_ = os.path.join(dir,file_path)
                file_path_pdf = os.path.abspath(file_path_pdf_)
                print(file_path_pdf)
                self.file_info_widget = QWebEngineView()
                self.file_info_widget.settings().setAttribute(QtWebEngineWidgets.QWebEngineSettings.PluginsEnabled, True)
                self.file_info_widget.settings().setAttribute(QtWebEngineWidgets.QWebEngineSettings.PdfViewerEnabled, True)

                self.file_info_widget.load(QUrl.fromLocalFile(file_path_pdf))
                self.dock3.setWidget(self.file_info_widget)

            elif extension in ('.docx'):

                def docx_to_html(file_path, output_dir):
                    document = Document(file_path)
                    html = "<html><body>"
                    for paragraph in document.paragraphs:
                        html += "<p>{}</p>".format(paragraph.text)
                    html += "</body></html>"

                    # Write the HTML to a file in the output directory
                    output_path = os.path.join(output_dir, 'output.html')
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(html)

                    return output_path

                # creo un dir temporanea
                tmpdirname = tempfile.mkdtemp()

                # path assoluta
                file_path_dc = os.path.join(dir,file_path)
                file_path_dc = os.path.abspath(file_path_dc)
                #converto in html
                html_path = docx_to_html(file_path_dc, tmpdirname)

                self.file_info_web = QWebEngineView()
                self.file_info_web.load(QUrl.fromLocalFile(html_path))
                self.dock3.setWidget(self.file_info_web)

                # per rimuovere il file temporaneo
                #shutil.rmtree(tmpdirname)


            elif extension in ('.xlsx'):
                def xlsx_to_html(file_path,output_dir):
                    wb = openpyxl.load_workbook(file_path)
                    sheet = wb.active

                    html = "<html><body><table>"
                    for row in sheet.iter_rows():
                        html += "<tr>"
                        for cell in row:
                            html += "<td>{}</td>".format(escape(str(cell.value) if cell.value is not None else ''))
                        html += "</tr>"
                    html += "</table></body></html>"

                    # Write the HTML to a file in the output directory
                    output_path = os.path.join(output_dir, 'output.html')
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(html)
                        output_path = os.path.join(tmpdirname, 'output.html')
                        with open(output_path, 'w',encoding='utf-8') as f:
                            f.write(html)

                    return output_path

                # creo una dir temporanea
                tmpdirname = tempfile.mkdtemp()

                # path assoluta
                file_path_dc = os.path.join(dir,file_path)
                file_path_dc = os.path.abspath(file_path_dc)
                # converto in html
                html_path = xlsx_to_html(file_path_dc, tmpdirname)
                self.file_info_web = QWebEngineView()
                self.file_info_web.load(QUrl.fromLocalFile(html_path))
                self.dock3.setWidget(self.file_info_web)

            elif extension in ('.jpg', '.jpeg', '.png', '.bmp', '.gif'):
                self.file_info_label = QLabel()
                pixmap = QPixmap(file_path)
                self.file_info_label.setPixmap(pixmap)
                self.dock3.setWidget(self.file_info_label)

            elif extension in ('.mp4', '.avi', '.wmv', '.mov'):
                # path assoluta
                file_path_video = os.path.join(dir,file_path)
                file_path_video = os.path.abspath(file_path_video)


                self.file_info_videowidget = QVideoWidget()
                self.file_info_player = QMediaPlayer()
                self.file_info_player.setVideoOutput(self.file_info_videowidget)
                self.file_info_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path_video)))

                def handle_error(error):
                    if error != QMediaPlayer.NoError:
                        error_string = self.file_info_player.errorString()
                        print(f"Errore durante l'impostazione del media: {error_string}")

                self.file_info_player.error.connect(handle_error)


                self.file_info_player.play()
                def handle_media_status_changed(status):
                    if status == QMediaPlayer.LoadedMedia:
                        print("Video pronto per essere visualizzato")
                    elif status == QMediaPlayer.BufferingMedia:
                        print("Video ancora in buffering")
                    elif status == QMediaPlayer.EndOfMedia:
                        print("Video playback completato")
                    elif status == QMediaPlayer.NoMedia:
                        print("No media")
                    elif status == QMediaPlayer.InvalidMedia:
                        print("Media non supportato")
                    elif status == QMediaPlayer.UnknownMediaStatus:
                        print("Status non riconosciuto")

                self.file_info_player.mediaStatusChanged.connect(handle_media_status_changed)
                #richiamo la funzione per gestire il maouse
                self.file_info_videowidget.installEventFilter(self)
                self.dock3.setWidget(self.file_info_videowidget)
        else:
            empty_widget = QtWidgets.QWidget()  # Creo un widget vuoto
            self.dock3.setWidget(empty_widget)
        # Recupero e visualizzo le informazioni sui nodi vicini
        neighbor_info_texts = []
        for neighbor in G.neighbors(closest_node_id):
            neighbor_info = G.nodes[neighbor]
            neighbor_info_text = "\n".join(f"{key}: {value}" for key, value in neighbor_info.items())
            neighbor_info_texts.append(neighbor_info_text)
        self.neighbor_info_textedit.setText("\n\n".join(neighbor_info_texts))


    #gestione degli eventi del maouse per fermare iniziare e smettere in pausa il video
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            mouse_event = QMouseEvent(event)
            if mouse_event.button() == Qt.LeftButton:
                # Avvia la riproduzione del video
                self.file_info_player.play()
            elif mouse_event.button() == Qt.RightButton:
                # Sospendi la riproduzione del video
                self.file_info_player.pause()
            elif mouse_event.button() == Qt.MiddleButton:
                # Interrompi la riproduzione del video
                self.file_info_player.stop()
        elif event.type() == QEvent.MouseButtonRelease:
            mouse_event = QMouseEvent(event)
            if mouse_event.button() == Qt.MiddleButton:
                # Ferma la riproduzione del video
                self.file_info_player.stop()

        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        # Chiudi la visualizzazione 3D prima di chiudere la finestra
        self.plotter.close()
        event.accept()
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = GraphWindow()
    window.show()
    app.exec_()







