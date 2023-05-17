from builtins import str
from PyQt5.QtWidgets import QMessageBox
import sys
import os

current_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_directory)
from matrix_exp import *
import re
import ast
class pyarchinit_Interactive_Matrix:
    DATA_LIST = ""
    ID_US_DICT = {}
    #HOME = os.environ['PYARCHINIT_HOME']
    def __init__(self,  data_list, id_us_dict):
        super().__init__()

        self.DATA_LIST = data_list
        self.ID_US_DICT = id_us_dict


        ##      self.textbox.setText('1 2 3 4')
        # self.on_draw()
        try:
            self.csv_connect()
        except:
            pass
    def csv_connect(self):
        pass
    def urlify(self,s):

        # Rimuove tutti i caratteri che non sono parole (tutto tranne i numeri e le lettere)
        s = re.sub(r"[^\w\s]", ' ', s)

        # Sostituire tutti gli spazi bianchi con un underscore
        s = re.sub(r"\s+", '_', s)

        return s

    def generate_matrix(self):
        #funzione per rimuovere gli underscore nella liste di liste
        def replace_spaces_with_underscore(us, ut,d_interpretativa, epoca,e_id):
            us = str(us).replace(' ', '_')
            ut = str(ut).replace(' ', '_')
            d_interpretativa = d_interpretativa.replace(' ', '_')
            epoca = epoca.replace(' ', '_')
            e_id = e_id.replace(' ', '_')

            return us, ut, d_interpretativa, epoca,e_id

        data = []
        contemporane = []

        properties_ant = []

        for sing_rec in self.DATA_LIST:
            try:
                #us, ut, d_interpretativa, epoca = sing_rec[0], sing_rec[1], sing_rec[2], sing_rec[3]
                rapporti_stratigrafici = [sing_rec[5]]  # Assegna l'elemento corrispondente alla lista di liste

                for record_str in rapporti_stratigrafici:
                    # Dividi la stringa in singole liste di stringhe
                    record_strings = re.findall(r"\[.*?\]", record_str)

                    # Converte ogni lista di stringhe in una lista di tuple
                    record = [tuple(ast.literal_eval(s)) for s in record_strings]

            except (NameError, SyntaxError) as e:
                QMessageBox.warning(self, 'ATTENZIONE',
                                    'Mancano i valori unita tipo e interpretazione startigrafica nella tablewidget dei rapporti startigrafici. affinchè il matrix sia esportato correttamente devi inserirli',
                                    QMessageBox.Ok)
                break

            # Utilizza la funzione replace_spaces_with_underscore per sostituire gli spazi con underscore
            us,ut, d_interpretativa, epoca,e_id = replace_spaces_with_underscore(sing_rec[0], sing_rec[1],sing_rec[2], sing_rec[3],sing_rec[4])

            try:
                for sing_rapp in record:
                    d_interpretativa_sing_rapp = sing_rapp[3].replace(' ', '_')

                    if sing_rapp[0] == 'anteriore':
                        if sing_rapp[1] != '':
                            harris_rapp1 = (
                                ut+us + '_' + d_interpretativa + '_' + epoca+'-'+e_id,str(sing_rapp[2])+
                                str(sing_rapp[1]) + '_' + d_interpretativa_sing_rapp + '_' + str(sing_rapp[4])+'-'+str(sing_rapp[5]))
                            data.append(harris_rapp1)

                    if sing_rapp[0] == 'properties_ant':
                        if sing_rapp[1] != '':
                            harris_rapp3 = (
                                ut+us + '_' + d_interpretativa + '_' + epoca+'-'+e_id,str(sing_rapp[2])+
                                str(sing_rapp[1]) + '_' + d_interpretativa_sing_rapp + '_' + str(sing_rapp[4])+'-'+str(sing_rapp[5]))
                            properties_ant.append(harris_rapp3)

                    if sing_rapp[0] == 'contemporaneo':
                        if sing_rapp[1] != '':
                            harris_rapp2 = (
                                ut+us + '_' + d_interpretativa + '_' + epoca+'-'+e_id,str(sing_rapp[2])+
                                str(sing_rapp[1]) + '_' + d_interpretativa_sing_rapp + '_' + str(sing_rapp[4])+'-'+str(sing_rapp[5]))
                            contemporane.append(harris_rapp2)

            except Exception as e:
                QMessageBox.warning(self, 'ATTENZIONE',
                                    'Mancano i valori unita tipo e interpretazione startigrafica nella tablewidget dei rapporti startigrafici. affinchè il matrix sia esportato correttamente devi inserirli',
                                    QMessageBox.Ok)

        def find_unique_epochs(data_list):
            epochs = set()
            #print(f'questa è il data_list_:{data_list}')
            for record in data_list:
                epoch = record[3]+'-'+record[4]  # L'epoca si trova all'indice 3 di ogni record
                epochs.add(epoch)

            return epochs

        # Utilizzare la funzione sul  dataset
        data_list = self.DATA_LIST
        print(f'data lista: {data_list}')
        unique_epochs = find_unique_epochs(data_list)
        #print(f'unica epoca: {unique_epochs}')
        periodizz_data_list = unique_epochs
        periodi_data_values = []
        for a in periodizz_data_list:
            #print(f'ciclo su a: {a}')
            periodi_data_values.append([a])
            #print(f'periodi data valori: {periodi_data_values}')
        periodi_us_list = []

        clust_number = 0



        for epoch in unique_epochs:
            print(f'ciclo su epoca: {epoch}')
            cluster_label = "cluster%s" % (clust_number)
            periodo_label = "Epoca: %s" % (epoch)
            sing_per = [cluster_label, periodo_label]
            sing_us = []

            for rec in data_list:
                us, ut, d_interpretativa, epoca,e_id = replace_spaces_with_underscore(rec[0], rec[1], rec[2], rec[3],rec[4])

                if epoca == epoch:
                    sing_us.append(ut+str(us) + '_' + d_interpretativa + '_' + epoca + '-'+e_id)

            sing_per.insert(0, sing_us)
            periodi_us_list.append(sing_per)
            clust_number += 1
        print(f'data:{data}\n\n,conteporaneo:{contemporane}\n\n,propeties: {properties_ant}\n\n epoche:{periodi_us_list}\n\n' )
        matrix_exp = HarrisMatrix(data,contemporane,properties_ant, periodi_us_list)
        try:
            matrix_exp.export_matrix_2
        except Exception as e :
            QMessageBox.information(self, "Info", str(e), QMessageBox.Ok)
        finally:
            data_plotting_2 = matrix_exp.export_matrix_2
            #QMessageBox.information(self, "Info", "Esportazione completata")
        return data_plotting_2


