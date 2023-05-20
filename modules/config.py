#sistema globale per configurare le path
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
