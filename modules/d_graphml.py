import csv

import networkx as nx
import pyvista as pv
import sys
from PyQt5 import QtWidgets, QtCore,QtWebEngineWidgets
from PyQt5.QtCore import QUrl,Qt,QEvent
from PyQt5.QtGui import QPixmap,QMouseEvent
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QLabel,QMessageBox
from pyvistaqt import QtInteractor
import os
import numpy as np
from PIL import Image
from docx import Document
import openpyxl
from html import escape
import tempfile



G = None  # Definisci G all'inizio del tuo codice
graphml_path=None


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
                    tube = line.tube(radius=1)# tubo è lo stile 3d
                    self.plotter.add_mesh(tube, color=EDGE_COLOR)#lo aggiugno alla mesh

            meshes = []#creao una lista vuota dove inserire le mesh che devono essere visualizzate come oggetti 3D
            # Read terms from a CSV file into a list
            terms = []
            csv_file_path = 'template/property.csv'  # Replace with the path to your CSV file
            print(os.path.abspath(csv_file_path))
            with open(csv_file_path, newline='') as csvfile:

                csvreader = csv.reader(csvfile)
                for row in csvreader:
                    terms.extend(row)  # Assuming each row is a list of terms
            print(terms)
            # Directory dei modelli 3D
            dir = os.path.dirname(self.graphml_path)


            models_dir=os.path.join(dir,"3d_obj")
            self.image_path = ''
            # Lista dei modelli 3D esistenti
            existing_models = [f[:-4] for f in os.listdir(models_dir) if f.endswith(".obj")]  # Rimuovi l'estensione .obj
            # print(existing_models)
            # Verifica quali modelli 3D corrispondono alle descrizioni dei nodi
            for node_id, node_data in G.nodes(data=True):
                # print(node_data)
                if "label" in node_data and node_data["label"] in existing_models:
                    print(f"Modello 3D {node_data['label']}.obj esiste e corrisponde al nodo {node_id}.")
                else:
                    print(f"Modello 3D per il nodo {node_id} non trovato.")
                if node_id in self.x_coord and node_id in self.y_coord:
                    x = float(self.x_coord[node_id])
                    y = float(self.y_coord[node_id])
                    z = float(self.z_coord[node_id])

                    # Recupero del percorso del file del modello 3D corrispondente alla descrizione del nodo
                    try:
                        model_path = f"{models_dir}/{G.nodes[node_id]['label']}.obj"
                        model_img = f"{models_dir}/{G.nodes[node_id]['label']}.mtl"
                        label_parts = node_data["label"].split('.')
                        self.i_size = 0
                        self.j_size = 0
                        if "USV" in node_data["label"]:
                            self.image_path = f"{models_dir}/USV.png"
                            self.i_size = 100
                            self.j_size = 50
                        elif "VSF" in node_data["label"]:
                            self.image_path = f"{models_dir}/VSF.png"
                            self.i_size = 100
                            self.j_size = 50
                        elif "SF" in node_data["label"]:
                            self.image_path = f"{models_dir}/SF.png"
                            self.i_size = 100
                            self.j_size = 50
                        elif "US" in node_data["label"]:
                            self.image_path = f"{models_dir}/US.png"
                            self.i_size = 100
                            self.j_size = 50
                        elif "C." in node_data["label"]:
                            print('combiner')
                            self.image_path = f"{models_dir}/combiner.png"
                            self.i_size = 50
                            self.j_size = 50

                        elif label_parts[0] == 'D' and len(label_parts) == 3:
                            print('extractor')
                            self.image_path = f"{models_dir}/extractor.png"
                            self.i_size = 50
                            self.j_size = 50

                        elif label_parts[0] == 'D' and len(label_parts) == 2:
                            print('document')
                            self.image_path = f"{models_dir}/document.png"
                            self.i_size = 50
                            self.j_size = 75
                        elif any(term.lower() in node_data["label"] for term in terms):
                            print('property')
                            self.image_path = f"{models_dir}/property.png"
                            self.i_size = 100
                            self.j_size = 50

                        else:
                            self.image_path = f"{models_dir}/{G.nodes[node_id]['label']}.png"
                            self.i_size = 100
                            self.j_size = 50
                    except KeyError:

                        print(KeyError)

                    else:

                        #se model path esiste carica il 3D, altrimenti carica l'immagine, se non trova l'immagine carica una sfera 3d
                        if os.path.exists(model_path):

                            # Caricamento del modello 3D
                            mesh = pv.read(model_path)
                            angle = np.radians(90)
                            # Ruota la mesh di 90 gradi intorno all'asse xper fare in modo che la mesh si ruotata nel senso desiderato ovvero di 90 gradi rispetto alla sua origine
                            rotate_x_matrix = np.array([[1, 0, 0, 0],
                                                        [0, np.cos(angle), -np.sin(angle), 0],
                                                        [0, np.sin(angle), np.cos(angle), 0],
                                                        [0, 0, 0, 1]])


                            # Calcola il fattore di scala per adattare la mesh alla dimensione desiderata
                            mesh_size = max(mesh.bounds[1] - mesh.bounds[0],
                                            mesh.bounds[3] - mesh.bounds[2],
                                            mesh.bounds[5] - mesh.bounds[4])
                            desired_size = 100  # 4 volte il diametro della sfera
                            scale_factor = desired_size / mesh_size

                            # Scala la mesh
                            mesh.points *= scale_factor

                            # Applicazione della trasformazione alla mesh
                            mesh.transform(rotate_x_matrix)
                            # Calcola la traslazione
                            translation = np.array([x, y, z])

                            # Sposta la mesh di prova
                            mesh.points = mesh.points - mesh.center + translation

                            try:
                                # print(f"Centro della mesh dopo la traslazione: {mesh.center}")
                                texture = pv.read_texture(model_img)#leggo la texture in png la tegture deve avere lo stesso nome della obj

                                self.plotter.add_mesh(mesh, texture=texture)
                            except:
                                self.plotter.add_mesh(mesh, color='red')

                        else:
                            if os.path.exists(self.image_path):
                                image = Image.open(self.image_path)
                                image = image.rotate(180)
                                image = np.array(image)  # Converti l'immagine PIL in un array NumPy per pyvista

                                texture = pv.Texture(image)

                                mesh = pv.Plane(center=(x, y, z), direction=(0, 0, 1), i_size=self.i_size, j_size=self.j_size)
                                mesh.texture_map_to_plane(inplace=True)

                                self.plotter.add_mesh(mesh, texture=texture)
                            else:
                                mesh = pv.Sphere(center=(x, y, z), radius=25)
                                self.plotter.add_mesh(mesh)

                        meshes.append(mesh)
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
        #file_path = closest_node_info.get('url')
        dir = os.path.dirname(self.graphml_path)
        #try: # questo try va ottimizzato per il momento è una toppa
            #file_path_abs_ = os.path.join(dir, file_path)
            #file_path_abs = os.path.abspath(file_path_abs_)
            #print(os.path.exists(file_path))
        #except:
            # If the 'url' attribute does not exist or does not point to a file, check in the 'DoSco' folder
        # Get the path to the 'DoSco' folder
        dosco_dir = os.path.join(dir, 'DosCo')

        # Get all the files in the 'DoSco' directory
        dosco_files = os.listdir(dosco_dir)

        # Try to match the node label to a file in the 'DoSco' directory
        matching_files = [f for f in dosco_files if f.startswith(closest_node_info.get('label'))]

        # If we have found a match, update the file_path
        if matching_files:
            file_path = os.path.join(dosco_dir, matching_files[0])
        else:
            file_path = None

        if file_path is not None and os.path.exists(file_path):
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







