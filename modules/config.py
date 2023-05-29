#sistema globale per configurare le path
'''
Il codice definisce una classe Config con un attributo privato _path e una proprietà path che permette di ottenere e
impostare il valore di _path.Viene quindi creato un'istanza della classe con config = Config().
Questo codice ci consente di creare un oggetto che memorizza le impostazioni di configurazione.
 Possiamo poi impostare o ottenere il valore dell'impostazione di configurazione attraverso la proprietà path.
Esempio:
config.path = '/var/www/html'
print(config.path) # Output: '/var/www/html'
'''


import os
class Config:
    def __init__(self):
        self._path = ''

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = value

config = Config()
