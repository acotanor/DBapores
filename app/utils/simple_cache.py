class SimpleCache:
    def __init__(self):
        self._data = {}

    def has(self, key):
        return key in self._data

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value