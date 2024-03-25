import cryptocode.myfunctions
class File:

    def __init__(self, file, key=None):
        self.file = file
        self.__key = key

    def read(self):
        with open(self.file, "rb") as f:
            data = cryptocode.myfunctions.b64decode(f.read()).decode()
            if self.__key:
                return cryptocode.myfunctions.decrypt(data, self.__key)
            else:
                return data

    def write(self, data):
        with open(self.file, "wb") as f:
            data = str(data)
            if self.__key:
                data = cryptocode.myfunctions.encrypt(data, self.__key)
            f.write(cryptocode.myfunctions.b64encode(data.encode()))