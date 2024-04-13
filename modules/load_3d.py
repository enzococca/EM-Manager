import re

import vtk
from PyQt5 import QtWidgets, QtCore
from pyvista import QtInteractor
from pyvistaqt import QtInteractor
import pyvista as pv
import os
import numpy as np
# Nella script EDMatrix2Graphml.py:


class OBJPROXY(QtWidgets.QMainWindow):
    def __init__(self, csv_mapper,models_dir,parent=None, show=True):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.csv_mapper2 = csv_mapper
        # Creazione di un frame e layout verticale.
        self.frame = QtWidgets.QFrame()
        vlayout = QtWidgets.QVBoxLayout()

        self.update_models_dir(models_dir)
        self.models_list = sorted([f for f in os.listdir(self.models_dir) if f.endswith(".obj")])

        # Creazione di un cursore (dial) per selezionare diversi modelli.
        self.dial = QtWidgets.QDial()
        self.dial.setMinimum(0)
        self.dial.setMaximum(len(self.models_list) - 1)
        self.dial.valueChanged.connect(self.dial_value_changed)
        vlayout.addWidget(self.dial)

        # Creazione di un visualizzatore interattivo per visualizzare i modelli 3D.
        self.plotter = QtInteractor(self)
        self.plotter.enable_trackball_style()
        self.plotter.set_background('white')
        #self.plotter.add_logo_widget(r'logo.jpeg')


        #self.plotter.show_grid(color='black')
        vlayout.addWidget(self.plotter.interactor)

        self.frame.setLayout(vlayout)
        self.setCentralWidget(self.frame)

        # Creazione di un dizionario per tenere traccia delle mesh e degli attori.
        self.meshes = {}  # già esistente
        self.original_colors = {}  # nuovo dizionario
        self.current_selected_proxy = None
        self.cell_picker = vtk.vtkCellPicker()
        self.plotter.iren.add_observer('EndPickEvent', self.click_callback)

    def select_proxy(self, proxy):
        model, actor, _ = proxy
        if self.current_selected_proxy is not None:
            # Imposta l'attuale proxy selezionato come non selezionato
            cur_model, cur_actor, _ = self.current_selected_proxy
            self.current_selected_proxy = (cur_model, cur_actor, False)
        self.current_selected_proxy = (
            model, actor, True)  # Usa la proprietà/metodo corretto in base alla tua implementazione

    def deselect_all_proxies(self):
        if self.current_selected_proxy is not None:
            model, actor, _ = self.current_selected_proxy

            # Deselezionare tutte le mesh che corrispondono all'attore
            for mesh_name, (mesh_model, mesh_actor, selected) in self.meshes.items():
                if mesh_actor is actor:
                    self.unhighlight_mesh(mesh_name)

            self.current_selected_proxy = None

    # Questa funzione viene chiamata ogni volta che il valore del cursore cambia.
    def update_models_dir(self, models_dir):
        # Aggiorna il percorso dei modelli e ricarica la lista dei modelli.
        self.models_dir = models_dir
        self.models_list = sorted([f for f in os.listdir(self.models_dir) if f.endswith(".obj")])

    def load_model_and_color_from_mtl(self, obj_path):
        mtl_path = obj_path.replace('.obj', '.mtl')
        # Leggi il file mtl e trova il colore Kd
        with open(mtl_path, 'r') as mtl_file:
            for line in mtl_file:
                if line.startswith('Kd'):
                    # I colori Kd sono specificati come tre numeri float separati da spazi
                    color = [float(val) for val in line.split()[1:]]
                    break
            else:
                color = None  # Nessun colore Kd trovato nel file mtl

        model = pv.read(obj_path)
        if model is None:
            print(f"Failed to read the model from {obj_path}")
            return


        if color is not None:  # se c'è il colore nel file .mtl lo utilizza, altrimenti 'gray'
            actor = self.plotter.add_mesh(model, specular=1, specular_power=20, color=color)
        else:
            actor = self.plotter.add_mesh(model)

        # Colore e opacità originali
        original_color = color if color is not None else (
        1, 1, 1)  # assume white as the default color, adjust if necessary
        original_opacity = 1.0  # assumes default opacity is 1.0, adjust if necessary

        # Salva la mesh e i suoi colori originali nei dizionari
        mesh_name = os.path.basename(obj_path)  # si assume che il nome del file sia uguale al nome dell'obj
        self.meshes[mesh_name] = (model, actor, False)
        self.original_colors[mesh_name] = (original_color, original_opacity)

        self.plotter.lighting = True
        self.plotter.add_light(pv.Light(intensity=1))

        return (model, actor, False)  # `False` indica che il proxy non è selezionato

    def create_legend(self):
        legend_entries = []

        # generate entries for only visible actors
        for mesh_name, (model, actor, selected) in self.meshes.items():
            color = self.original_colors[mesh_name][0]  # get color from original_colors
            legend_entries.append([mesh_name, color])

        # remove the old legend
        self.plotter.remove_legend()

        # add the new legend
        self.plotter.add_legend(legend_entries, loc='lower right')

    def dial_value_changed(self, value):
        # Se il valore è minore della lunghezza del dizionario di mesh,
        # vengono rimossi gli attori e le mesh corrispondenti.
        if value < len(self.meshes):
            for mesh_key in list(self.meshes.keys())[value:]:
                mesh, actor, _ = self.meshes[mesh_key]
                self.plotter.remove_actor(actor)
                del self.meshes[mesh_key]

        # Se il valore è maggiore della lunghezza del dizionario delle mesh,
        # Caricare nuovi modelli di file e aggiungerli alla scena.
        else:
            for i in range(len(self.meshes), value + 1):
                path = os.path.join(self.models_dir, self.models_list[i])
                self.name = os.path.basename(path)
                model, actor, _ = self.load_model_and_color_from_mtl(path)
                self.meshes[self.models_list[i]] = (model, actor, False)  # Aggiungi lo stato "selezionato" alla tuple

            self.create_legend()  # Creazione della legenda


    def highlight_mesh(self, mesh_name):
        # Questo metodo è usato per evidenziare una specifica mesh cambiando il suo colore in rosso.
        # Ottieni il proxy corrispondente al nome del mesh
        self.proxy = self.meshes.get(mesh_name)

        # Se il proxy esiste, selezionalo
        if self.proxy is not None:
            self.select_proxy(self.proxy)

        mesh, actor, _ = self.meshes[mesh_name]
        actor.GetProperty().SetColor(1, 0, 0)  # Settare il colore a verde brillante
        actor.GetProperty().SetOpacity(0.7)  # Imposta l'opacità a 0 (completamente trasparente)
        self.csv_mapper2.display_related_info(mesh_name)

        # Also highlight the related cell in CSVMapper table
        for row in range(self.csv_mapper2.data_table.rowCount()):
            if self.csv_mapper2.data_table.item(row, 0).text() == mesh_name:
                self.csv_mapper2.data_table.selectRow(row)
                break
    def unhighlight_mesh(self, mesh_name):
        # Recupera il proxy corrispondente al nome della mesh
        proxy = self.meshes.get(mesh_name)

        model, actor, _ = proxy  # Aggiungi lo stato "selezionato" alla tua tupla
        # Recupera il colore e l'opacità predefiniti
        color, opacity = self.original_colors.get(mesh_name, ((1, 1, 1), 1.0))
        # Imposta il colore e l'opacità predefiniti
        actor.GetProperty().SetColor(*color)  # Ripristina il colore predefinito
        actor.GetProperty().SetOpacity(opacity)  # Ripristina l'opacità predefinita

    def click_callback(self, obj, event):
        #questa funzione viene chiamata quando si verifica un evento di clic.
        # L'evento di clic è associato a un oggetto (probabilmente un oggetto
        # grafico nella rappresentazione 3D). La funzione accede alla posizione
        #
        # dell’evento (x, y) e la usa per selezionare una cella nel renderer 3D.
        # Se l'oggetto cliccato esiste, la funzione itera sugli elementi memorizzati
        # in self.meshes per cercare l'attore che è stato cliccato. Quando trova la corrispondenza,
        # separa il nome dall'attore, pulisce il nome per rimuovere tutti i caratteri non numerici,
        # e quindi chiama un'altra funzione, get_clicked_mesh_name(), passando il nome pulito.
        x, y = obj.GetEventPosition()
        self.cell_picker.Pick(x, y, 0, self.plotter.renderer)
        actor = self.cell_picker.GetActor()
        if actor:
            for name, (_, actor_item, _) in self.meshes.items():
                if actor is actor_item:
                    print(f"Mesh name: {name}")
                    name=re.sub(r'[^\d]', '', name.split(".")[0])
                    self.get_clicked_mesh_name(name)
                    break
    def get_clicked_mesh_name(self, name):
        # Questa funzione è chiamata quando si fa clic su una mesh
        self.csv_mapper2.display_related_info(name)

def main():
    app = QtWidgets.QApplication([])
    window = OBJPROXY()
    window.show()
    app.exec_()


# Questo è il punto di ingresso principale del programma.
if __name__ == "__main__":
    main()
