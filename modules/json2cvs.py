import json
from collections import defaultdict

import pandas as pd

class DataExtractor:
    def __init__(self, datafile):

        with open(datafile, 'r') as file:
           self.data = json.load(file)
        self.df = None

    def extract_data(self):
        try:
            epochs = self.data['context']['epochs']
            nodes = self.data['graphs']['graph1']['nodes']
            edges = self.data['graphs']['graph1']['edges']
        except KeyError:
            print('Invalid data format.')
            return

        # Determino l'indice delle epoche in base al loro tempo di inizio
        sorted_epochs = sorted(epochs.items(), key=lambda x: x[1]['start'])
        epoch_index_map = {epoch[0]: idx for idx, epoch in enumerate(sorted_epochs)}

        properties_post = {name: [] for name in nodes}
        properties_ant = {name: [] for name in nodes}

        for edge_type in edges.values():
            for link in edge_type:
                if link['from'] in properties_post and link['to'] in nodes:
                    properties_post[link['from']].append(nodes[link['to']]['name'])
                if link['to'] in properties_ant and link['from'] in nodes:
                    properties_ant[link['to']].append(nodes[link['from']]['name'])
        #Estraggo i dati in un array
        rows = []
        # Raccolgo tutte le proprietà dei nodi
        properties_ant = defaultdict(set)
        properties_post = defaultdict(set)
        for edge in edges['line']:
            properties_post[edge['from']].add(edge['to'])
            properties_ant[edge['to']].add(edge['from'])
        for edge in edges['dashed']:
            properties_post[edge['from']].add(edge['to'])
            properties_ant[edge['to']].add(edge['from'])

        for name, node in nodes.items():
            epochs = node['data'].get('epochs', [])
            if epochs:
                for epoch in epochs:
                    if 'data' in node:
                        # Determino il tipo sul prefisso del nome
                        prefixes = ["USM", "US", "USV", "UTR", "VSF", "SF"]
                        if any(name.startswith(prefix) for prefix in prefixes):
                            tipo = ''.join(filter(str.isalpha, node['type']))
                            nome_us = ''.join(filter(str.isdigit, node['name']))
                            row = {
                                'nome us': nome_us,
                                'tipo': tipo,
                                'tipo di nodo': '',
                                'descrizione': node['data'].get('description', ''),
                                'epoca': epoch,
                                'epoca index': epoch_index_map[epoch],
                                'anteriore': ','.join(properties_post[name]) if properties_post.get(name) else '',
                                'posteriore': ','.join(properties_ant[name]) if properties_ant.get(name) else '',
                                'contemporaneo': '',
                                'properties_ant': '',
                                'properties_post': ''
                            }
                            rows.append(row)
            else:
                row = {
                    'nome us': name,
                    'tipo': node['type'],
                    'tipo di nodo': '',
                    'descrizione': node['data'].get('description', ''),
                    'epoca': '',
                    'epoca index': '',
                    'anteriore': '',
                    'posteriore': '',
                    'contemporaneo': '',
                    'properties_ant': ','.join(list(properties_post[name])) if properties_post.get(name) else '',
                    'properties_post': ','.join(list(properties_ant[name])) if properties_ant.get(name) else ''

                }
                rows.append(row)

        self.df = pd.DataFrame(rows)
        print("Data extracted successfully: {} rows.".format(len(self.df)))
        return self.df
    def export_to_csv(self, filename):
        if self.df is not None:
            self.df.to_csv(filename, index=False)
            print(f"Data exported to {filename} successfully.")
        else:
            print("No data to export. Please run extract_data() first.")
class DataImporter:
    #Dato un dataframe, costruisce la struttura json
    def __init__(self, dataframe):
        self.df = dataframe

    def to_json_structure(self):
        # Inizializzo la struttura principale
        data_structure = {
            "context": {
                "epochs": {}
            },
            "graphs": {
                "graph1": {
                    "nodes": {},
                    "edges": {
                        "line": [],
                        "dashed": []


                    }
                }
            }
        }

        # Mi assicuro che le epoche siano uniche
        epochs = self.df['epoca'].unique()
        epoch_data = {
            epoch: {
                "start": min(self.df[self.df['epoca'] == epoch]['epoca index']),
                "end": max(self.df[self.df['epoca'] == epoch]['epoca index']),
                "color": "#FFFFFF"  # imposto un colore di default ma si potrebbe fare in modi di scegliere da configurare
            } for epoch in epochs
        }
        data_structure['context']['epochs'] = epoch_data

        # Costruisco i nodi
        for _, row in self.df.iterrows():
            prefixes = ["USM", "US", "USV", "UTR", "VSF", "SF"]

            node_name = None
            if row['tipo'].startswith(tuple(prefixes)):
                node_name = row['tipo'].split("/")[0] + row['nome us']
            else:
                node_name = row['nome us']

            node = {
                "type": row['tipo'],
                "name": node_name,
                "data": {
                    "description": row['descrizione'],
                    "epochs": [row['epoca']],
                    "url": "Empty",
                    "time": row['epoca index']
                }
            }

            data_structure['graphs']['graph1']['nodes'][node_name] = node

        for _, row in self.df.iterrows():
            from_node = None
            prefixes = ["USM", "US", "USV", "UTR", "VSF", "SF"]
            if row['tipo'].startswith(tuple(prefixes)):
                from_node = row['tipo'].split("/")[0] + row['nome us']
            else:
                from_node = row['nome us']

            # Using line edges as an example
            if pd.notna(row['contemporaneo']):
                for to_node in row['contemporaneo'].split(','):
                    if to_node != "nan":
                        # Find the corresponding node and its type in the dataframe
                        to_node_data = self.df.loc[self.df['nome us'] == to_node.strip()]
                        if not to_node_data.empty:
                            to_node_type = to_node_data['tipo'].values[0]
                            to_node_prefix = to_node_type.split("/")[0] if to_node_type.startswith(
                                tuple(prefixes)) else ""
                            to_nodes = to_node_prefix + to_node.strip()

                            data_structure['graphs']['graph1']['edges']['line'].append(
                                {"from": from_node, "to": to_nodes})

            # check anteriore and posteriore for line edges
            for edge_type in ['anteriore']:
                if pd.notna(row[edge_type]):
                    for to_node in row[edge_type].split(','):
                        if to_node != "nan":
                            # Find the corresponding node and its type in the dataframe
                            to_node_data = self.df.loc[self.df['nome us'] == to_node.strip()]
                            if not to_node_data.empty:
                                to_node_type = to_node_data['tipo'].values[0]
                                to_node_prefix = to_node_type.split("/")[0] if to_node_type.startswith(
                                    tuple(prefixes)) else ""
                                to_nodes = to_node_prefix + to_node.strip()

                                data_structure['graphs']['graph1']['edges']['line'].append(
                                    {"from": from_node, "to": to_nodes})

            # check properties_ant and properties_post for dashed edges
            for edge_type in ['properties_ant']:
                if pd.notna(row[edge_type]):
                    for to_node in row[edge_type].split(','):
                        if to_node != "nan":
                            # Find the corresponding node and its type in the dataframe
                            to_node_data = self.df.loc[self.df['nome us'] == to_node.strip()]
                            if not to_node_data.empty:
                                to_node_type = to_node_data['tipo'].values[0]
                                to_node_prefix = to_node_type.split("/")[0] if to_node_type.startswith(
                                    tuple(prefixes)) else ""
                                to_nodes = to_node_prefix + to_node.strip()

                                data_structure['graphs']['graph1']['edges']['dashed'].append(
                                    {"from": from_node, "to": to_nodes})




        return data_structure

# # esempio DataFrame
# sample_data = {
#     "nome us": ["100", "102", "103"],
#     "tipo": ["US", "USVn", "US"],
#     "tipo di nodo": ["Fondazione di epoca romana", "Serie di colonne di un edificio pubblico, intercolumnio aerostilo", "Muro moderno"],
#     "descrizione": ["Fondazione di epoca romana", "Serie di colonne di un edificio pubblico, intercolumnio aerostilo", "Muro moderno"],
#     "epoca": ["Epoca Romana", "Epoca Romana", "y2018"],
#     "epoca index": [-1, -1, 60],
#     "anteriore": ["", "", ""],
#     "posteriore": ["", "", ""],
#     "contemporaneo": ["", "", ""],
#     "properties_ant": ["", "", ""],
#     "properties_post": ["", "", ""]
# }
#
# df_sample = pd.DataFrame(sample_data)
#

# importer = DataImporter(df_sample)
# g=importer.to_json_structure()

# Esempio importazione file json
#
#extractor = DataExtractor(r'C:\Users\enzoc\Downloads\dati.json')
#extractor.extract_data()
#extractor.export_to_csv('exported_data.csv')