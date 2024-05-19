# ---------------------------------------------------------
# Autore: Enzo Cocca
# Data: 06/04/2024
# Descrizione: Script per convertire un file GraphML in Excel e CSV,
#              con elaborazione specifica per nodi e archi.
# ---------------------------------------------------------
import csv
import os
import xml.etree.ElementTree as ET
from datetime import datetime

import networkx as nx
import pandas as pd
import re
from PyQt5.QtWidgets import QFileDialog




# Function to read keywords from CSV and convert to lowercase
def load_keywords_from_csv(file_path):
    keywords = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            keywords.extend([keyword.lower() for keyword in row])
    return keywords
# Load keywords from template/epoche_storiche.csv
# Function to read indices and keywords from a CSV and convert to lowercase
def load_keywords_epoch(file_path):
    keywords = {}
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if row:  # Ensure the row is not empty
                index = row[0].strip()
                keyword = row[1].strip().lower()
                keywords[keyword] = index
                print(f"Loaded keyword: {keyword} with index: {index}")  # Debugging line
    return keywords


period_keywords = load_keywords_epoch('template/epoche_storiche.csv')
print(f"Period Keywords: {period_keywords}")
def is_period_label(label_text):
    # Controlla se il label_text contiene una delle parole chiave
    result = any(keyword in label_text.lower() for keyword in period_keywords)
    print(f"Checking label: {label_text}, Result: {result}")  # Debugging line
    return result

# Load keywords from property.csv
def load_graphml(project_directorys, csv_name):
    graphml_path, _ = QFileDialog.getOpenFileName(None, 'Seleziona il file GraphML', '', '*.graphml')


    # Carico il file GraphML con xml tree che mi serve per estrarre i NodeLabels e
    # i periodi dato che i periodi non sono delle label
    tree = ET.parse(graphml_path)
    root = tree.getroot()

    # Definisco i namespace utilizzati nel file GraphML
    namespaces = {
        'graphml': 'http://graphml.graphdrawing.org/xmlns',
        'y': 'http://www.yworks.com/xml/graphml'
    }

    # Inizializzo il dizionario per i periodi e i nodi elaborati
    periods = {}

    # Analizzo l'XML per trovare tutti gli elementi y:NodeLabel ed estrarre i periodi
    for table_node in root.findall('.//y:TableNode', namespaces):
        for node_label in table_node.findall('.//y:NodeLabel', namespaces):
            label_text = node_label.text
            # Utilizza una logica specifica per determinare se il label rappresenta un periodo
            # Ad esempio, potresti controllare se il testo contiene certe parole chiave,
            # numeri romani, date o altri indicatori che usi per identificare i periodi.
            if label_text and is_period_label(label_text):  # is_period_label è una funzione da definire
                print(f"Periodo trovato: {label_text}")
                # Estrai la posizione (x, y) dall'elemento NodeLabel se disponibile
                x = float(node_label.attrib.get('x', 0))
                y = float(node_label.attrib.get('y', 0))
                periods[label_text] = {'x': x, 'y': y}
                print(f"Periodo trovato: {label_text} - Posizione: ({x}, {y})")

    # Ora ho un dizionario dei periodi con le loro posizioni
    print(periods)

    # Carico il file GraphML usando NetworkX
    G = nx.read_graphml(graphml_path)

    # Estraggo i dati dei nodi e degli archi
    nodes_data = G.nodes(data=True)
    edges_data = G.edges(data=True)
    # Inizializzo i dizionari per i nodi epoca e US
    epoca_nodes = {}
    processed_nodes = {}
    documenti_visti = {}
    print(nodes_data)
    # Elaboro i nodi per identificare le epoche e i nodi US
    for node, data in nodes_data:
        label = data.get('label', '')
        description = data.get('description', '')
        tipo = ''
        nome_us = ''

        if not label:
            continue
        # Controllo se la label contiene 'USV'
        elif 'USV' in label:
            # Ottiengo il tipo di forma dal nodo
            shape_type = data.get('shape_type', '').lower()  # Converto in minuscolo per il confronto
            nome_us = re.sub(r'[^0-9]', '', label)  # Estraggo la parte numerica
            #esempio USV123 -> 123
            # Assegno il tipo in base alla forma
            if shape_type == 'ellipse':
                tipo = 'USV/c'
            elif shape_type == 'parallelogram':
                tipo = 'USV/s'
            elif shape_type == 'hexagon':
                tipo = 'USV/n'
            else:
                tipo = 'USV'
        # Se non c'è una corrispondenza di forma, assegna solo USV
        # devo fare ciò per i nodi USV perchè hanno uno forma differente anche se presentano lo stessa sigla quindi
        # quando trovo USV nel graphm a seconda del tipo di forma assegno un tipo diverso di sigla che verrà scritto
        # nella tabella nel campo tipo

        # Controllo se la label contiene i prefissi 'US', 'USM', 'VSF e le altre sigle'
        elif 'US' in label or 'USM' in label or 'VSF' in label or 'UTR' in label or 'USD' in label or 'US/s' in label or 'USM/s' in label:
            match = re.match(r'([a-zA-Z]+)(\d+)', label)
            if match:
                prefix = match.group(1)
                if prefix in ['US', 'USM', 'VSF','UTR','USD','US/s','USM/s']:
                    tipo = prefix
                nome_us = match.group(2)
        elif 'SF' in label:
            tipo = 'SFF'
            # Cambia SF in SFF non so perchè non mi riconosce SF ma SFF sì (in tipo sarà scritto
            # SF ma nell 'esportazione del graphml sarà SF)
            nome_us = label[2:]  # Rimuovi il prefisso SF
        elif '_continuity' in description:
            tipo = 'continuity'
            nome_us = label
        elif label.startswith(('D.', 'E.', 'C.')):
            parts = label.split('.')
            if len(parts) == 2:
                tipo = 'document' if label.startswith('D.') else 'extractor' if label.startswith('E.') else 'combiner'
                # Controllo se il documento è già stato visto e aggiorna il nome se necessario i nomi dei nodi devono
                # essere univoci quindi se trovo un nodo con lo stesso nome lo incremento (questo vale soprattutto per i
                # document)
                if label in documenti_visti:
                    # Incrementa il contatore e aggiorna il nome
                    documenti_visti[label] += 1
                    nome_us = f"{label}_{documenti_visti[label]}"
                else:
                    # Altrimenti, inizializza il contatore
                    documenti_visti[label] = 1
                    nome_us = label
            elif len(parts) > 2:
                tipo = 'extractor'
                nome_us = label
        elif any(keyword in label for keyword in load_keywords_from_csv('template/property.csv')):

            nome_us = label
            tipo = 'property'
        else:
            nome_us = label
            # Caso predefinito se nessun'altra condizione è soddisfatta

        # Trovo il periodo precedente più vicino in base alla posizione
        closest_period_label = ''
        min_distance = float('inf')
        us_x = float(data.get('x', 0))
        us_y = float(data.get('y', 0))

        # Trovo il periodo precedente più vicino
        for period_label, period_data in periods.items():
            distance = (us_x - period_data['x']) ** 2 + (us_y - period_data['y']) ** 2
            if distance < min_distance:
                closest_period_label = period_label  # Usa direttamente l'etichetta del periodo
                min_distance = distance

        # Aggiorno i dati del nodo US con il periodo associato
        data['epoca'] = closest_period_label
        # Aggiungi l'indice dell'epoca
        data['epoca index'] = period_keywords.get(closest_period_label.lower(), '')
        # se stampo G,node_data vedrò aggiugnto l'attributo epoca con il periodo associato per ogni nodo
        # Popolo il dizionario processed_nodes
        if nome_us:
            processed_nodes[node] = {
                'nome us': nome_us,
                'tipo': tipo,
                'tipo di nodo': data.get('shape_type', ''),
                'descrizione': description,
                'epoca': data.get('epoca', ''),  # Segnaposto per l'associazione del periodo
                'epoca index': data.get('epoca index', ''),
                'anteriore': '',
                'posteriore': '',
                'contemporaneo': '',
                'properties_ant': '',
                'properties_post': ''
            }

    edge_relations = {}
    #print(edges_data)
    # Elaboro gli archi per associarli ai nodi US
    for edge in G.edges(data=True):
        source, target, attr = edge
        source_data = processed_nodes.get(source, {})
        target_data = processed_nodes.get(target, {})

        # Devo assicurarmi che il dizionario per il nodo target sia inizializzato
        if target not in edge_relations:
            edge_relations[target] = {'anteriore': [], 'posteriore': [], 'properties_ant': [], 'properties_post': []}
        if source not in edge_relations:
            edge_relations[source] = {'anteriore': [], 'posteriore': [], 'properties_ant': [], 'properties_post': []}

        # Classifico i nodi sorgente e destinazione in base al loro tipo
        if source_data.get('tipo') in ['property', 'extractor', 'combiner', 'document']:
            edge_relations[target]['properties_post'].append(source_data.get('nome us', ''))
        else:
            edge_relations[target]['posteriore'].append(source_data.get('nome_us', ''))

        if target_data.get('tipo') in ['property', 'extractor', 'combiner', 'document']:
            edge_relations[source]['properties_ant'].append(target_data.get('nome us', ''))
        else:
            edge_relations[source]['anteriore'].append(target_data.get('nome us', ''))

    # Aggiorno il dizionario processed_nodes con le informazioni degli archi
    for node, relations in edge_relations.items():
        if node in processed_nodes:
            processed_nodes[node].update({
                'anteriore': ','.join(relations['anteriore']),
                'posteriore': ','.join(relations['posteriore']),
                'properties_ant': ','.join(relations['properties_ant']),
                'properties_post': ','.join(relations['properties_post'])
            })

    # Converto i dati dei nodi elaborati in un DataFrame di pandas
    nodes_df = pd.DataFrame.from_dict(processed_nodes, orient='index')
    edges_df = pd.DataFrame(list(edges_data), columns=['Source', 'Target', 'Attributes'])

    # Definisci il percorso della directory del progetto
    project_directory = project_directorys
    csv_names= csv_name
    if not os.path.exists(project_directory):
        os.makedirs(project_directory)

    # Scrivi il DataFrame in un file Excel
    excel_filename = os.path.join(project_directory, 'output.xlsx')
    with pd.ExcelWriter(excel_filename) as writer:
        nodes_df.to_excel(writer, sheet_name='Nodes')
        edges_df.to_excel(writer, sheet_name='Edges')

    # Esporta anche in formato CSV
    # Genera il timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Genera il nome del file utilizzando il timestamp
    csv_filename_nodes = os.path.join(project_directory, csv_names)
    #csv_filename_edges = os.path.join(project_directory, f"edges_{timestamp}.csv")

    # Scrivi i DataFrame in CSV
    nodes_df.to_csv(csv_filename_nodes, index=False)
    #edges_df.to_csv(csv_filename_edges, index=False)

    # Messaggio di successo
    print(f'GraphML convertito con successo in Excel e CSV nella directory {project_directory}!')

    # edges_df.to_csv('edges.csv', index=False)
    # Messaggio di successo
    print('GraphML convertito con successo in Excel!')
