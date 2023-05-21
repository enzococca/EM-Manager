import networkx as nx
import pandas as pd

# Leggi il file GraphML in un grafo
G = nx.read_graphml('../test/test.graphml')

# Crea un dataframe vuoto con le colonne richieste
df = pd.DataFrame(columns=['nome us', 'tipo', 'tipo di nodi', 'descrizione', 'epoca', 'epoca index', 'area',
                           'anteriore', 'posteriore', 'contemporaneo', 'properties_ant', 'properties_post', 'rapporti'])


def get_us_name_and_type(label):
    if label != 'nan':
        if label.startswith('D.'):
            tipo, nome_us = 'document', label
        elif label.startswith('E.'):
            tipo, nome_us = 'extractor', label
        elif label.startswith('C.'):
            tipo, nome_us = 'combiner', label
        elif label.split('.')[0].isdigit():
            tipo, nome_us = 'property', label
        else:
            tipo = ''.join([i for i in label if not i.isdigit()])
            nome_us = ''.join([i for i in label if i.isdigit()])
    else:
        tipo, nome_us = 'nan', 'nan'
    return nome_us, tipo


# Itera attraverso ogni nodo nel grafo
for node in G.nodes(data=True):
    # Estrai le informazioni dal nodo
    label = node[1].get('label', 'nan')  # sostituisci 'label' con il nome del tuo attributo nel GraphML
    nome_us, tipo = get_us_name_and_type(label)
    tipo_di_nodi = node[1].get('node_type', 'nan')
    descrizione = node[1].get('description', 'nan')
    epoca = node[1].get('epoch', 'nan')
    epoca_index = node[1].get('epoch_index', 'nan')
    area = node[1].get('area', 'nan')

    # Ottieni i nodi connessi
    anteriore = [get_us_name_and_type(G.nodes[edge[1]]['label'])[0] for edge in G.edges(node[0])]
    posteriore = [get_us_name_and_type(G.nodes[edge[0]]['label'])[0] for edge in G.edges(node[0]) if edge[1] == node[0]]
    anteriore = ','.join(anteriore) if anteriore else 'nan'
    posteriore = ','.join(posteriore) if posteriore else 'nan'

    df = df._append({'nome us': nome_us, 'tipo': tipo, 'tipo di nodi': tipo_di_nodi,
                    'descrizione': descrizione, 'epoca': epoca, 'epoca index': epoca_index,
                    'area': area, 'anteriore': anteriore, 'posteriore': posteriore,
                    'contemporaneo': 'nan', 'properties_ant': 'nan',
                    'properties_post': 'nan', 'rapporti': 'nan'}, ignore_index=True)

# Scrivi il dataframe in un file CSV
df.to_csv('output.csv', index=False)
